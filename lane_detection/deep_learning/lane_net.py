"""
Deep Learning Lane Detection Model
CNN-based lane detection using PyTorch.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from typing import Tuple, Optional


class LaneNet(nn.Module):
    """
    Convolutional Neural Network for lane detection.
    This is a simplified UNet-style architecture for lane segmentation.
    """

    def __init__(self, input_channels: int = 3, output_channels: int = 1):
        """
        Initialize LaneNet.

        Args:
            input_channels: Number of input image channels (3 for RGB)
            output_channels: Number of output channels (1 for binary lane mask)
        """
        super(LaneNet, self).__init__()

        # Encoder (downsampling)
        self.enc1 = self._conv_block(input_channels, 64)
        self.enc2 = self._conv_block(64, 128)
        self.enc3 = self._conv_block(128, 256)
        self.enc4 = self._conv_block(256, 512)

        # Bottleneck
        self.bottleneck = self._conv_block(512, 1024)

        # Decoder (upsampling)
        self.upconv4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.dec4 = self._conv_block(1024, 512)

        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec3 = self._conv_block(512, 256)

        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec2 = self._conv_block(256, 128)

        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec1 = self._conv_block(128, 64)

        # Final output layer
        self.out = nn.Conv2d(64, output_channels, kernel_size=1)

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    def _conv_block(self, in_channels: int, out_channels: int) -> nn.Sequential:
        """
        Create a convolutional block with two conv layers.

        Args:
            in_channels: Number of input channels
            out_channels: Number of output channels

        Returns:
            Sequential conv block
        """
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.

        Args:
            x: Input tensor [batch, channels, height, width]

        Returns:
            Output tensor [batch, output_channels, height, width]
        """
        # Encoder with skip connections
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool(enc1))
        enc3 = self.enc3(self.pool(enc2))
        enc4 = self.enc4(self.pool(enc3))

        # Bottleneck
        bottleneck = self.bottleneck(self.pool(enc4))

        # Decoder with skip connections
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat([dec4, enc4], dim=1)
        dec4 = self.dec4(dec4)

        dec3 = self.upconv3(dec4)
        dec3 = torch.cat([dec3, enc3], dim=1)
        dec3 = self.dec3(dec3)

        dec2 = self.upconv2(dec3)
        dec2 = torch.cat([dec2, enc2], dim=1)
        dec2 = self.dec2(dec2)

        dec1 = self.upconv1(dec2)
        dec1 = torch.cat([dec1, enc1], dim=1)
        dec1 = self.dec1(dec1)

        # Output
        out = self.out(dec1)
        return torch.sigmoid(out)


class SimpleLaneNet(nn.Module):
    """
    Simplified CNN for faster inference.
    Good for real-time applications.
    """

    def __init__(self, input_channels: int = 3, output_channels: int = 1):
        """
        Initialize SimpleLaneNet.

        Args:
            input_channels: Number of input image channels
            output_channels: Number of output channels
        """
        super(SimpleLaneNet, self).__init__()

        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 4
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )

        self.decoder = nn.Sequential(
            # Upsample
            nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2),
            nn.ReLU(inplace=True),

            nn.Conv2d(32, output_channels, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor

        Returns:
            Output tensor
        """
        x = self.features(x)
        x = self.decoder(x)
        return torch.sigmoid(x)


class DLLaneDetector:
    """Wrapper class for deep learning-based lane detection."""

    def __init__(self,
                 model_path: Optional[str] = None,
                 model_type: str = 'simple',
                 device: str = 'auto',
                 input_size: Tuple[int, int] = (256, 256),
                 threshold: float = 0.5):
        """
        Initialize DL lane detector.

        Args:
            model_path: Path to pretrained model weights
            model_type: Type of model ('simple' or 'full')
            device: Device to run on ('cpu', 'cuda', or 'auto')
            input_size: Input image size (height, width)
            threshold: Threshold for binary segmentation
        """
        self.input_size = input_size
        self.threshold = threshold

        # Set device
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        # Initialize model
        if model_type == 'simple':
            self.model = SimpleLaneNet()
        else:
            self.model = LaneNet()

        self.model.to(self.device)

        # Load pretrained weights if provided
        if model_path:
            self.load_weights(model_path)

        self.model.eval()

    def load_weights(self, model_path: str):
        """
        Load model weights from file.

        Args:
            model_path: Path to model weights
        """
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"Loaded model weights from {model_path}")
        except Exception as e:
            print(f"Failed to load model weights: {e}")

    def save_weights(self, model_path: str):
        """
        Save model weights to file.

        Args:
            model_path: Path to save weights
        """
        torch.save(self.model.state_dict(), model_path)
        print(f"Saved model weights to {model_path}")

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess image for model input.

        Args:
            image: RGB image as numpy array

        Returns:
            Preprocessed tensor
        """
        # Resize
        resized = cv2.resize(image, (self.input_size[1], self.input_size[0]))

        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # Convert to tensor and change dimension order
        tensor = torch.from_numpy(normalized).permute(2, 0, 1)

        # Add batch dimension
        tensor = tensor.unsqueeze(0)

        return tensor.to(self.device)

    def postprocess(self, output: torch.Tensor, original_size: Tuple[int, int]) -> np.ndarray:
        """
        Postprocess model output to binary mask.

        Args:
            output: Model output tensor
            original_size: Original image size (height, width)

        Returns:
            Binary lane mask
        """
        # Remove batch dimension and convert to numpy
        mask = output.squeeze().cpu().detach().numpy()

        # Apply threshold
        binary_mask = (mask > self.threshold).astype(np.uint8) * 255

        # Resize to original size
        resized_mask = cv2.resize(binary_mask, (original_size[1], original_size[0]))

        return resized_mask

    def detect(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect lanes in image.

        Args:
            image: RGB input image

        Returns:
            Tuple of (lane_mask, debug_image)
        """
        original_size = image.shape[:2]

        # Preprocess
        input_tensor = self.preprocess(image)

        # Inference
        with torch.no_grad():
            output = self.model(input_tensor)

        # Postprocess
        lane_mask = self.postprocess(output, original_size)

        # Create debug image
        debug_image = self._create_debug_image(image, lane_mask)

        return lane_mask, debug_image

    def _create_debug_image(self, image: np.ndarray, lane_mask: np.ndarray) -> np.ndarray:
        """
        Create debug visualization.

        Args:
            image: Original image
            lane_mask: Lane segmentation mask

        Returns:
            Debug visualization
        """
        # Create colored overlay
        overlay = image.copy()
        colored_mask = np.zeros_like(image)
        colored_mask[:, :, 1] = lane_mask  # Green channel

        # Blend
        debug_image = cv2.addWeighted(overlay, 0.7, colored_mask, 0.3, 0)

        return debug_image


if __name__ == "__main__":
    # Example usage
    print("Testing LaneNet architecture...")

    # Create sample input
    batch_size = 2
    channels = 3
    height, width = 256, 256

    x = torch.randn(batch_size, channels, height, width)

    # Test full model
    model_full = LaneNet()
    output_full = model_full(x)
    print(f"Full LaneNet output shape: {output_full.shape}")

    # Test simple model
    model_simple = SimpleLaneNet()
    output_simple = model_simple(x)
    print(f"Simple LaneNet output shape: {output_simple.shape}")

    # Test detector
    detector = DLLaneDetector(model_type='simple')
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    lane_mask, debug_image = detector.detect(test_image)
    print(f"Lane mask shape: {lane_mask.shape}")
