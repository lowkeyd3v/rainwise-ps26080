"""
Mixture-of-Experts U-Net Bias Corrector (Module 2 of PS 26080 pipeline)

Architecture:
  - Shared spatial encoder (CNN) extracts features from NWP forecast + topography
  - 6 regime-specific decoder heads (one expert per weather regime)
  - Gating network combines experts using regime classifier confidence scores

Input:  [NWP_rainfall, U850, V850, Topography, Elevation] — 5 channels, gridded
Output: Bias-corrected rainfall at same grid resolution

Reference: Mixture-of-Experts conditioning for regime-aware bias correction
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ─── Building Blocks ─────────────────────────────────────────────────────────

class ConvBlock(nn.Module):
    """Double convolution block used in U-Net encoder/decoder."""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DownBlock(nn.Module):
    """Encoder block: MaxPool → ConvBlock."""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.pool = nn.MaxPool2d(2)
        self.conv = ConvBlock(in_ch, out_ch)

    def forward(self, x):
        return self.conv(self.pool(x))


class UpBlock(nn.Module):
    """Decoder block: Upsample → concat skip → ConvBlock."""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_ch, in_ch // 2, kernel_size=2, stride=2)
        self.conv = ConvBlock(in_ch, out_ch)

    def forward(self, x, skip):
        x = self.up(x)
        # Pad if spatial dims don't match
        if x.shape != skip.shape:
            x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)


# ─── Shared Encoder ──────────────────────────────────────────────────────────

class SharedEncoder(nn.Module):
    """
    Shared U-Net encoder extracting multi-scale spatial features
    from NWP forecast fields + static topography.
    """
    def __init__(self, in_channels: int = 5, base_features: int = 64):
        super().__init__()
        f = base_features
        self.inc = ConvBlock(in_channels, f)
        self.down1 = DownBlock(f, f * 2)
        self.down2 = DownBlock(f * 2, f * 4)
        self.down3 = DownBlock(f * 4, f * 8)
        self.bottleneck = DownBlock(f * 8, f * 16)

    def forward(self, x):
        s1 = self.inc(x)
        s2 = self.down1(s1)
        s3 = self.down2(s2)
        s4 = self.down3(s3)
        bottleneck = self.bottleneck(s4)
        return bottleneck, [s1, s2, s3, s4]


# ─── Expert Decoder Head ─────────────────────────────────────────────────────

class ExpertDecoder(nn.Module):
    """Single regime-specific decoder head."""
    def __init__(self, base_features: int = 64, out_channels: int = 1):
        super().__init__()
        f = base_features
        self.up1 = UpBlock(f * 16, f * 8)
        self.up2 = UpBlock(f * 8, f * 4)
        self.up3 = UpBlock(f * 4, f * 2)
        self.up4 = UpBlock(f * 2, f)
        self.out = nn.Sequential(
            nn.Conv2d(f, out_channels, kernel_size=1),
            nn.ReLU()  # Rainfall is non-negative
        )

    def forward(self, bottleneck, skips):
        x = self.up1(bottleneck, skips[3])
        x = self.up2(x, skips[2])
        x = self.up3(x, skips[1])
        x = self.up4(x, skips[0])
        return self.out(x)


# ─── Gating Network ──────────────────────────────────────────────────────────

class GatingNetwork(nn.Module):
    """
    Computes soft gate weights from regime confidence scores.
    Input: regime_probs [B, n_experts]
    Output: gate_weights [B, n_experts, 1, 1]
    """
    def __init__(self, n_experts: int = 6, temperature: float = 1.0):
        super().__init__()
        self.n_experts = n_experts
        self.temperature = temperature

    def forward(self, regime_probs: torch.Tensor) -> torch.Tensor:
        # regime_probs: [B, n_experts]
        gates = F.softmax(regime_probs / self.temperature, dim=1)
        return gates.view(-1, self.n_experts, 1, 1)


# ─── Full MoE U-Net ──────────────────────────────────────────────────────────

class MoEUNet(nn.Module):
    """
    Mixture-of-Experts U-Net for regime-conditional rainfall bias correction.

    Args:
        in_channels:   Number of input channels (NWP fields + topography)
        n_experts:     Number of weather regimes / expert decoder heads
        base_features: Base number of feature maps in U-Net
    """
    def __init__(
        self,
        in_channels: int = 5,
        n_experts: int = 6,
        base_features: int = 64,
        temperature: float = 1.0,
    ):
        super().__init__()
        self.n_experts = n_experts
        self.encoder = SharedEncoder(in_channels, base_features)
        self.experts = nn.ModuleList([
            ExpertDecoder(base_features) for _ in range(n_experts)
        ])
        self.gating = GatingNetwork(n_experts, temperature)

    def forward(
        self,
        x: torch.Tensor,
        regime_probs: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            x: [B, C, H, W]  — NWP fields + topography
            regime_probs: [B, n_experts]  — softmax outputs from regime classifier

        Returns:
            corrected_rain: [B, 1, H, W]  — bias-corrected rainfall
        """
        bottleneck, skips = self.encoder(x)

        # Run all expert decoders
        expert_outputs = torch.stack(
            [expert(bottleneck, skips) for expert in self.experts],
            dim=1,
        )  # [B, n_experts, 1, H, W]

        # Gate: [B, n_experts, 1, 1]
        gates = self.gating(regime_probs)  # [B, n_experts, 1, 1]
        gates = gates.unsqueeze(-1)  # [B, n_experts, 1, 1, 1]

        # Weighted mixture: sum over experts
        corrected = (expert_outputs * gates).sum(dim=1)  # [B, 1, H, W]
        return corrected


# ─── Loss Function ───────────────────────────────────────────────────────────

class RainfallLoss(nn.Module):
    """
    MSE loss with additional penalty weight on heavy rainfall grid cells.
    Prevents the model from ignoring rare extreme events.
    """
    def __init__(self, heavy_threshold_mm: float = 64.5, extreme_weight: float = 3.0):
        super().__init__()
        self.threshold = heavy_threshold_mm
        self.weight = extreme_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        weights = torch.ones_like(target)
        weights[target >= self.threshold] = self.weight
        loss = (weights * (pred - target) ** 2).mean()
        return loss


# ─── Convenience Functions ───────────────────────────────────────────────────

def build_model(model_cfg: dict) -> MoEUNet:
    """Build MoE U-Net from config dict."""
    cfg = model_cfg["moe_corrector"]
    return MoEUNet(
        in_channels=cfg["shared_encoder"]["in_channels"],
        n_experts=cfg["n_experts"],
        base_features=cfg["shared_encoder"]["base_features"],
        temperature=cfg["gating"]["temperature"],
    )


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Quick smoke test
    model = MoEUNet(in_channels=5, n_experts=6, base_features=32)
    B, C, H, W = 2, 5, 64, 80   # Typical India domain at 0.25 deg
    x = torch.randn(B, C, H, W)
    regime_probs = torch.softmax(torch.randn(B, 6), dim=1)
    out = model(x, regime_probs)
    print(f"Input:  {x.shape}")
    print(f"Output: {out.shape}")   # Expected: [2, 1, 64, 80]
    print(f"Params: {count_parameters(model):,}")
