# Quick Start Guide - Lane Detection System

This guide will help you get started with the lane detection implementation for your LKAS project.

## Overview

The implementation provides:
- **Traditional CV approach** using OpenCV (Hough Transform)
- **Deep Learning approach** using PyTorch (CNN segmentation)
- **Lane position analysis** with drift/departure detection
- **Visual feedback system** with HUD and alerts
- **CARLA integration** for simulation testing

## Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd /Users/donghyun/All/seame/ads_ld
pip install -r requirements.txt
```

### Step 2: Test the Setup (Without CARLA)

```bash
cd lane_detection
python test_setup.py
```

This will test all components using synthetic test images.

### Step 3: Install CARLA

**⚠️ macOS M1/M2 Users**: CARLA doesn't support Apple Silicon natively!
👉 **Follow [MACOS_M1_SETUP.md](MACOS_M1_SETUP.md) for Docker-based setup**

**For Linux/Windows users**:
- Download CARLA from [carla.org](https://carla.org/)
- Or install Python API: `pip install carla==0.9.15`

### Step 4: Run with CARLA

**Terminal 1 - Start CARLA:**
```bash
cd /path/to/CARLA
./CarlaUE4.sh  # or CarlaUE4.exe on Windows
```

**Terminal 2 - Run Lane Detection:**
```bash
cd /Users/donghyun/All/seame/ads_ld/lane_detection
python main.py --method cv
```

## Project Structure

```
ads_ld/
├── README.md                    # Project overview
├── QUICK_START.md              # This file
├── requirements.txt            # Python dependencies
└── lane_detection/
    ├── main.py                 # Main entry point ⭐
    ├── carla_interface.py      # CARLA connection
    ├── config.yaml             # Configuration
    ├── README.md               # Module documentation
    ├── test_setup.py           # Setup verification
    ├── traditional/
    │   └── cv_lane_detector.py # OpenCV detector
    ├── deep_learning/
    │   └── lane_net.py         # CNN models
    └── utils/
        ├── lane_analyzer.py    # Position analysis
        └── visualizer.py       # Visualization tools
```

## Usage Examples

### Basic Usage

```bash
# Traditional CV method (recommended for starting)
python main.py --method cv

# Deep learning method (requires trained model)
python main.py --method dl --model path/to/model.pth
```

### Save Output Video

```bash
python main.py --method cv --save-video output.mp4
```

### Custom Settings

```bash
python main.py \
  --method cv \
  --width 1280 \
  --height 720 \
  --vehicle vehicle.audi.a2
```

## Understanding the System

### 1. Detection Methods

**Traditional CV (Recommended for starting):**
- ✅ Fast and interpretable
- ✅ Works out-of-the-box
- ✅ Easy to tune parameters
- ⚠️ Sensitive to lighting/shadows

**Deep Learning:**
- ✅ More robust to conditions
- ✅ Can handle complex scenarios
- ⚠️ Requires trained model
- ⚠️ Slower inference

### 2. System Pipeline

```
Camera Image → Lane Detection → Position Analysis → Visualization
                                       ↓
                              Steering Correction
```

### 3. Lane Departure States

- **CENTERED**: Vehicle is centered in lane ✅
- **DRIFT**: Small deviation (warning) ⚠️
- **DEPARTURE**: Large deviation (alert) 🚨
- **NO_LANES**: Cannot detect lanes ❌

## Tuning for Best Results

### If lanes are not detected well:

1. **Adjust Canny thresholds** in `traditional/cv_lane_detector.py`:
   ```python
   detector = CVLaneDetector(
       canny_low=30,    # Try lowering
       canny_high=100   # Try lowering
   )
   ```

2. **Adjust Hough parameters**:
   ```python
   hough_threshold=30,      # Try lowering for more lines
   hough_min_line_len=20,   # Try lowering
   ```

3. **Check ROI settings** - The region of interest should cover the road ahead

### If steering correction is too aggressive:

Edit gains in `utils/lane_analyzer.py`:
```python
steering = analyzer.get_steering_correction(
    left_lane, right_lane,
    kp=0.3,  # Reduce for gentler correction
    kd=0.05  # Reduce for less sensitivity to heading
)
```

## Common Issues

### "Failed to connect to CARLA"
- Ensure CARLA server is running
- Check host/port: `python main.py --host localhost --port 2000`

### "No module named 'carla'"
- Install CARLA Python package: `pip install carla==0.9.13`
- Or add CARLA PythonAPI to PYTHONPATH

### Poor performance
- Reduce resolution: `python main.py --width 640 --height 480`
- Use headless mode: `python main.py --no-display`

### Camera shows black screen
- Vehicle might not be spawned correctly
- Try different vehicle: `python main.py --vehicle vehicle.tesla.model3`

## Next Steps

### 1. Understanding the Code

Start with these files in order:
1. `main.py` - See how everything connects
2. `traditional/cv_lane_detector.py` - Understand lane detection
3. `utils/lane_analyzer.py` - See position calculation
4. `utils/visualizer.py` - Check visualization

### 2. Experiment and Tune

- Try different CARLA maps and weather conditions
- Tune detection parameters for your specific use case
- Test with different vehicles and camera positions

### 3. Collect Training Data (for DL)

```python
# Add to main.py to save images
if frame_count % 30 == 0:  # Save every 30 frames
    cv2.imwrite(f'data/frame_{frame_count}.jpg', image)
```

### 4. Extend to PiRacer

When ready for hardware:
1. Replace `CARLAInterface` with PiRacer camera
2. Add motor control integration
3. Implement safety constraints
4. Calibrate on real track

## Development Tips

### Running Individual Components

```python
# Test CV detector alone
from traditional.cv_lane_detector import CVLaneDetector
import cv2

detector = CVLaneDetector()
image = cv2.imread('test_image.jpg')
left, right, debug = detector.detect(image)
cv2.imshow('Result', debug)
cv2.waitKey(0)
```

### Adding Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Detected lanes: {left_lane}, {right_lane}")
```

### Performance Profiling

```python
import time

start = time.time()
left, right, debug = detector.detect(image)
fps = 1.0 / (time.time() - start)
print(f"FPS: {fps:.1f}")
```

## Resources

- **CARLA Documentation**: https://carla.readthedocs.io/
- **OpenCV Tutorials**: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
- **PyTorch Tutorials**: https://pytorch.org/tutorials/

## Getting Help

If you encounter issues:
1. Check this guide and the module README
2. Review the example code in each module's `__main__` block
3. Run `test_setup.py` to verify your installation
4. Check CARLA server logs for connection issues

## Team Collaboration

For your team members working on other parts:
- This module provides lane detection only
- Integration points:
  - Input: Camera images (numpy arrays)
  - Output: Lane lines, metrics, steering correction
- They can use `LaneAnalyzer` for position data
- Steering correction is provided but not applied to vehicle

---

**Ready to start?** Run `python test_setup.py` to verify everything works!
