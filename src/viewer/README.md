# Viewer Module

**Standalone ZMQ-based web viewer for remote monitoring of autonomous vehicles.**

## Overview

The viewer runs as a **separate process** and connects to the LKAS ZMQ broker to:
- ✅ Receives video frames, lane detection, and vehicle status via ZMQ (port 5557)
- ✅ Renders overlays on laptop (offloads vehicle CPU)
- ✅ Serves web interface on localhost:8080
- ✅ Sends commands (pause/resume/respawn) back to simulation
- ✅ Adjusts detection/decision parameters in real-time

## Why Separate Viewer?

**Benefits:**
- ✅ **Offloads vehicle CPU** - All rendering happens on laptop!
- ✅ **Rich visualizations** - Complex overlays don't impact vehicle performance
- ✅ **Remote monitoring** - Connect from any machine on network
- ✅ **Multiple viewers** - Multiple people can monitor simultaneously
- ✅ **Live tuning** - Adjust parameters without restarting system

## Quick Start

The viewer connects to the LKAS ZMQ broker which receives data from simulation.

```bash
# Terminal 1: Start CARLA
./CarlaUE4.sh

# Terminal 2: Start LKAS with ZMQ broker enabled
lkas --method cv --broadcast

# Terminal 3: Start simulation with broadcasting
simulation --broadcast

# Terminal 4: Start web viewer
viewer

# Open browser
# http://localhost:8080
```

### Port Configuration

Web viewer port can be configured in `config.yaml`:

```yaml
visualization:
  web_port: 8080  # Default port
```

Or override via command line:

```bash
viewer --port 8081
```

## Usage

### Command Line Options

```bash
viewer --help

Options:
  --vehicle URL      ZMQ URL for vehicle data (default: tcp://localhost:5557)
  --actions URL      ZMQ URL for sending actions (default: tcp://localhost:5558)
  --parameters URL   ZMQ URL for parameter updates (default: tcp://localhost:5559)
  --port N           HTTP port for web interface (default: from config.yaml)
  --config PATH      Path to config file (default: auto-detected)
  --verbose          Enable verbose HTTP logging
```

### Features

**Real-time Visualization:**
- **Video streaming** with lane overlays rendered on laptop
- **Lane detection overlay** (left/right lanes with confidence)
- **HUD display** with vehicle telemetry:
  - Speed (km/h), steering angle
  - Position (x, y), rotation (pitch, yaw, roll)
  - Detection processing time

**Interactive Controls:**
- **Pause/Resume** simulation via web button
- **Respawn vehicle** at spawn point
- **Live parameter tuning** for detection and decision modules
  - Detection: Canny thresholds, Hough parameters, smoothing
  - Decision: PID gains (Kp, Kd), throttle settings

**Network Monitoring:**
- Works over local network or WiFi
- Multiple viewers can connect simultaneously
- Automatic reconnection on network issues

## Architecture

```
┌─ CARLA Simulator ────────────────────────────────────────┐
│  • Provides camera images                                │
│  • Receives steering commands                            │
└───────────────┬──────────────────────────────────────────┘
                │ Shared Memory
                ▼
┌─ Simulation Orchestrator ────────────────────────────────┐
│  • Reads LKAS detection/control via shared memory        │
│  • Publishes vehicle status to LKAS broker (port 5562)   │
│  • Receives actions from LKAS broker (port 5561)         │
└───────────────┬──────────────────────────────────────────┘
                │ ZMQ (Vehicle Status)
                ▼
┌─ LKAS ZMQ Broker (port 5557-5562) ───────────────────────┐
│  • Receives vehicle status from simulation                │
│  • Receives frames/detection from LKAS shared memory      │
│  • Broadcasts all data to viewers (port 5557)            │
│  • Routes parameters to detection/decision servers        │
│  • Forwards actions to simulation                        │
└───────────────┬──────────────────────────────────────────┘
                │ ZMQ (All Data: 5557)
                ▼
┌─ VIEWER PROCESS (Laptop) ────────────────────────────────┐
│  ┌────────────────────────────────────────────────────┐  │
│  │  ZMQ Subscriber (connects to broker:5557)          │  │
│  │  • Receives video frames (JPEG compressed)         │  │
│  │  • Receives lane detection results                 │  │
│  │  • Receives vehicle status (speed, position, etc)  │  │
│  └─────────────────┬──────────────────────────────────┘  │
│                    ▼                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Overlay Renderer (runs on laptop!)                │  │
│  │  • Draws lane lines on frame                       │  │
│  │  • Renders HUD with vehicle telemetry              │  │
│  │  • Generates MJPEG stream for browser              │  │
│  └─────────────────┬──────────────────────────────────┘  │
│                    ▼                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  HTTP Server (localhost:8080)                      │  │
│  │  • Serves HTML/CSS/JavaScript                      │  │
│  │  • Streams MJPEG video (/stream endpoint)          │  │
│  │  • Handles actions POST (/action endpoint)         │  │
│  │  • Handles parameters POST (/parameter endpoint)   │  │
│  └─────────────────┬──────────────────────────────────┘  │
│                    │                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ZMQ Publishers (send to broker)                   │  │
│  │  • Actions (pause/resume/respawn) → port 5558      │  │
│  │  • Parameters (Kp, Kd, thresholds) → port 5559     │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────┬──────────────────────────────────────┘
                     │ HTTP
                     ▼
            ┌────────────────┐
            │    Browser     │
            │  localhost:8080│
            │  • Video stream│
            │  • Controls    │
            │  • Parameters  │
            └────────────────┘
```

**Key Points:**
- **Rendering on laptop**: Heavy drawing operations don't impact vehicle
- **Centralized broker**: LKAS broker handles all routing and broadcasting
- **Separate processes**: Viewer, LKAS, and simulation run independently
- **Network capable**: Works over local network or WiFi

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
- Check if viewer is running: `ps aux | grep viewer`
- Check if LKAS broker is running: `ps aux | grep "lkas.*broadcast"`
- Verify web port is accessible: `curl http://localhost:8080`
- Try different port: `viewer --port 8081`
- Check browser console for errors (F12)

### Problem: No video stream

**Solutions:**
- Ensure LKAS is running with `--broadcast` flag: `lkas --method cv --broadcast`
- Ensure simulation is running with `--broadcast` flag: `simulation --broadcast`
- Check LKAS terminal for "Broadcasting" messages
- Verify ZMQ connection in viewer logs
- Restart all processes in order: CARLA → LKAS → Simulation → Viewer

### Problem: Controls don't work (pause/resume/respawn)

**Solutions:**
- Check LKAS broker is receiving actions (look for "[Broker] Action received" logs)
- Ensure simulation is connected to LKAS broker (port 5561)
- Verify viewer can reach LKAS broker (port 5558)
- Check browser console for network errors

### Problem: Slow/laggy video

**Solutions:**
- Reduce camera resolution in config.yaml
- Close other resource-intensive applications
- Check CARLA server performance
- Use headless mode if visualization not needed

### Problem: Parameter changes don't take effect

**Solutions:**
- Ensure LKAS is running with `--broadcast` flag (enables parameter broker)
- Check LKAS broker is forwarding parameters (look for "[Broker] Parameter forwarded" logs)
- Verify detection/decision servers are subscribed to parameter updates
- Parameters update immediately - no need to restart

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

### Technology Stack

- **ZMQ (ØMQ)** - High-performance messaging for vehicle data
- **HTTP Server** - Threaded server for web interface
- **MJPEG streaming** - Real-time video to browser
- **HTML5/JavaScript** - Interactive UI with live controls
- **OpenCV** - Frame decoding and overlay rendering (on laptop!)

### ZMQ Topics

**Subscribed (from LKAS broker:5557):**
- `frame` - JPEG-compressed video frames
- `detection` - Lane detection results (left/right lanes)
- `state` - Vehicle status (speed, steering, position, etc.)

**Published:**
- `action` (to port 5558) - User commands (pause, resume, respawn)
- `parameter` (to port 5559) - Real-time parameter updates

## See Also

- [Simulation Module](../simulation/README.md) - CARLA orchestration
- [Detection Module](../lkas/detection/README.md) - Lane detection
- [Main README](../../README.md) - Project overview

## License

See main project LICENSE file.
