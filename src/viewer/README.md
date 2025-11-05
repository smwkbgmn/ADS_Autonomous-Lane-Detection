# Viewer Module

**Remote web-based viewer for monitoring autonomous vehicles.**

## Overview

The viewer module runs on your **laptop** (not the vehicle!) and:
- ✅ Receives data from vehicle via ZMQ
- ✅ Draws overlays (lanes, HUD, metrics)
- ✅ Serves web interface for browser viewing
- ✅ Sends commands back to vehicle (respawn, pause)

## Why Separate Viewer?

**Problem with old approach:**
- ❌ Rendering runs on vehicle CPU
- ❌ Heavy overlay drawing impacts control loop
- ❌ Not suitable for resource-constrained devices

**Benefits of new approach:**
- ✅ **Vehicle stays lightweight** - No rendering on vehicle!
- ✅ **Rich visualizations** - Draw complex overlays on laptop
- ✅ **Remote monitoring** - Monitor from any machine on network
- ✅ **Multiple viewers** - Multiple laptops can connect

## Quick Start

### Integrated with Simulation

The web viewer is built into the simulation module. Simply use:

```bash
# Start LKAS with web viewer (uses port from config.yaml)
lkas --method cv --viewer web

# Or start simulation alone with web viewer
simulation --viewer web

# Override port from command line if needed
simulation --viewer web --web-port 8081

# Open browser
# http://localhost:8080 (or your custom port)
```

### Standalone Viewer (Future)

For remote monitoring scenarios, a standalone viewer can be developed to connect via network.

## Usage

### Integrated Mode

The viewer is integrated into the simulation module:

```bash
# Web viewer (uses port from config.yaml, default: 8080)
simulation --viewer web

# Override web port from command line
simulation --viewer web --web-port 8081

# OpenCV window viewer
simulation --viewer opencv

# Pygame viewer
simulation --viewer pygame

# No visualization (headless)
simulation --viewer none
```

### Web Viewer Features

- **Real-time video streaming** from CARLA camera
- **Lane overlay visualization** (left/right lanes)
- **HUD display** with metrics:
  - Speed, steering angle
  - Lane offset, heading angle
  - Detection FPS, latency
- **Interactive controls**:
  - Respawn vehicle
  - Toggle autopilot
  - Adjust view settings

## Architecture

```
┌─ SIMULATION PROCESS ──────────────────────────────────────┐
│                                                            │
│  ┌──────────┐      ┌──────────────┐      ┌────────────┐  │
│  │  CARLA   │ ───▶ │  Detection   │ ───▶ │  Decision  │  │
│  │  Camera  │      │  (Shared Mem)│      │ (Shared Mem│  │
│  └──────────┘      └──────────────┘      └────────────┘  │
│       │                    │                     │        │
│       │ Image              │ Lanes               │ Steer  │
│       ▼                    ▼                     ▼        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Frame Processor & Visualizer              │  │
│  │  • Draws lane overlays                              │  │
│  │  • Renders HUD with metrics                         │  │
│  │  • Generates JPEG stream                            │  │
│  └─────────────────────────────────────────────────────┘  │
│                              │                            │
│                              ▼                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Web Server (Flask/HTTP)                   │  │
│  │  • Serves HTML interface                            │  │
│  │  • Streams MJPEG video                              │  │
│  │  • Handles user interactions                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                              │                            │
└──────────────────────────────┼────────────────────────────┘
                               │ HTTP
                               ▼
                      ┌────────────────┐
                      │    Browser     │
                      │  localhost:8080│
                      └────────────────┘
```

## Features

### Visualization Elements

**Lane Overlays:**
- Left lane line (green/red based on detection)
- Right lane line (green/red based on detection)
- Lane confidence indicators
- Region of interest (ROI) visualization

**HUD Display:**
- Vehicle speed (km/h)
- Steering angle (degrees)
- Lateral offset from center
- Heading angle deviation
- Lane departure status
- Detection FPS and latency
- Frame processing time

**Interactive Controls:**
- Keyboard shortcuts for vehicle control
- Respawn vehicle button
- Toggle autopilot mode
- Adjust visualization settings

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| FPS | 25-30 FPS | Real-time streaming |
| Latency | ~33ms | Frame capture to display |
| CPU (simulation) | ~15-20% | Rendering + encoding |
| Memory | ~50MB | Frame buffers |
| Network | ~200-500 KB/s | MJPEG stream to browser |

## Troubleshooting

### Problem: Blank page in browser

**Solutions:**
- Check if simulation is running: `ps aux | grep simulation`
- Verify web port is accessible: `curl http://localhost:8080`
- Try different port (CLI override): `simulation --web-port 8081`
- Or change port in config.yaml: `visualization.web_port: 8081`
- Check browser console for errors (F12)

### Problem: No video stream

**Solutions:**
- Ensure CARLA camera is active
- Check simulation terminal for errors
- Verify detection/decision modules are running
- Restart simulation

### Problem: Slow/laggy video

**Solutions:**
- Reduce camera resolution in config.yaml
- Close other resource-intensive applications
- Check CARLA server performance
- Use headless mode if visualization not needed

### Problem: Controls not working

**Solutions:**
- Ensure JavaScript is enabled in browser
- Check browser console for errors
- Verify keyboard focus is on browser window
- Refresh the page (F5)

## Development

### Adding Custom Overlays

The visualization is handled in the simulation module's visualizer:

```python
from simulation.utils.visualizer import Visualizer

visualizer = Visualizer()

# Draw custom overlay
def draw_custom_info(frame, custom_data):
    cv2.putText(frame, f"Custom: {custom_data}",
                (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 2)
    return frame

# Use in processing loop
visualized_frame = visualizer.draw_lanes(frame, detection_result)
visualized_frame = draw_custom_info(visualized_frame, my_data)
```

### Web Viewer Technology

The web viewer uses:
- **Flask** - Web server framework
- **MJPEG streaming** - Real-time video to browser
- **HTML5/JavaScript** - Interactive UI
- **OpenCV** - Frame rendering and overlay drawing

### Files

- `run.py` - Web viewer entry point
- `__init__.py` - Package exports
- `README.md` - This documentation

## See Also

- [Simulation Module](../simulation/README.md) - CARLA orchestration
- [Detection Module](../lkas/detection/README.md) - Lane detection
- [Main README](../../README.md) - Project overview

## License

See main project LICENSE file.
