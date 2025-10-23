"""
Lane Detection Models
This file serves as a compatibility layer for the old structure.

For the actual implementations, see:
- traditional/cv_lane_detector.py - OpenCV-based lane detection
- deep_learning/lane_net.py - CNN-based lane detection models

Usage:
    from traditional.cv_lane_detector import CVLaneDetector
    from deep_learning.lane_net import LaneNet, SimpleLaneNet, DLLaneDetector
"""

# Import all models for easy access
from traditional.cv_lane_detector import CVLaneDetector
from deep_learning.lane_net import LaneNet, SimpleLaneNet, DLLaneDetector

__all__ = [
    'CVLaneDetector',
    'LaneNet',
    'SimpleLaneNet',
    'DLLaneDetector'
]
