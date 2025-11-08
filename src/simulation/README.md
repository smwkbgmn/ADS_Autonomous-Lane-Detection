# Simulation Module

CARLA simulation orchestrator for the Lane Keeping Assist System.

## Overview

The simulation module integrates with CARLA simulator to provide:
- Vehicle spawning and control
- Camera sensor management
- LKAS module coordination via shared memory
- ZMQ-based vehicle status broadcasting to LKAS broker
- Remote action handling (pause/resume/respawn)
- Performance metrics and logging

## Features

- **CARLA Integration**:
  - Connection management and reconnection logic
  - Vehicle spawning with configurable models
  - Camera sensor setup and image capture
  - World and weather management

- **LKAS Coordination**:
  - Detection client for lane detection results
  - Decision client for steering commands
  - Shared memory-based IPC for low latency
  - ZMQ-based vehicle status publishing to LKAS broker
  - Action subscription from LKAS broker (pause/resume/respawn)

- **Remote Viewer Support**:
  - Publishes vehicle status to LKAS broker (port 5562)
  - Receives actions from LKAS broker (port 5561)
  - LKAS broker handles all viewer communication and data broadcasting

- **Performance Monitoring**:
  - Real-time FPS tracking
  - Frame processing metrics
  - Detection/decision latency measurement
  - Comprehensive logging

## Module Structure

```
simulation/
├── run.py                       # Main simulation entry point
├── orchestrator.py              # System orchestrator
│
├── carla_api/                   # CARLA interface layer
│   ├── connection.py            # CARLA connection management
│   ├── vehicle.py               # Vehicle spawning and control
│   └── sensors.py               # Camera sensor management
│
├── integration/                 # LKAS integration
│   └── __init__.py              # Detection/Decision client wrappers
│
├── processing/                  # Frame processing pipeline
│   ├── frame_processor.py       # Main processing loop
│   └── metrics_logger.py        # Performance metrics
│
└── utils/                       # Utilities
    └── visualizer.py            # Visualization helpers
```

## Installation

### Prerequisites

1. **CARLA Simulator**: Download and install from [https://carla.org/](https://carla.org/)
   - Recommended: CARLA 0.9.15+
   - Start with: `./CarlaUE4.sh` (Linux/Mac) or `CarlaUE4.exe` (Windows)

2. **Python Package**: Install the ads-skynet package
   ```bash
   cd /path/to/ads_skynet
   pip install -e .
   ```

## Usage

### Quick Start

```bash
# Terminal 1: Start CARLA
./CarlaUE4.sh

# Terminal 2: Start LKAS with ZMQ broker for viewer support
lkas --method cv --broadcast

# Terminal 3: Start simulation with broadcast enabled
simulation --broadcast

# Terminal 4: Start web viewer (optional)
viewer

# The viewer will show vehicle status, lane detection, and interactive controls
```

### Command Line Options

```bash
simulation --help

Options:
  --host HOST              CARLA server host (overrides config, default: from config.yaml)
  --port PORT              CARLA server port (overrides config, default: from config.yaml)
  --spawn-point N          Spawn vehicle at specific point (default: random)
  --config PATH            Path to config file (default: auto-detected)
  --broadcast              Enable ZMQ broadcasting to LKAS broker (for viewer support)
  --autopilot              Enable CARLA autopilot
  --no-sync                Disable synchronous mode
  --verbose                Enable verbose output
```

### Examples

**Standard mode with viewer support** (recommended):
```bash
# Enable broadcasting to LKAS broker for web viewer
simulation --broadcast

# In another terminal, start the viewer
viewer
```

**Remote CARLA server**:
```bash
simulation --host 192.168.1.100 --port 2000 --broadcast
```

**Custom spawn point**:
```bash
simulation --spawn-point 5 --broadcast
```

**Verbose output**:
```bash
simulation --broadcast --verbose
```

**Custom configuration**:
```bash
simulation --config /path/to/custom-config.yaml --broadcast
```

## Programming API

### Using as a Library

```python
from simulation import SimulationOrchestrator
from simulation.carla_api import CARLAConnection, VehicleManager
from lkas.detection.core.config import ConfigManager

# Load configuration
config = ConfigManager.load('config.yaml')

# Connect to CARLA
connection = CARLAConnection(
    host='localhost',
    port=2000,
    timeout=10.0
)
connection.connect()

# Spawn vehicle
vehicle_mgr = VehicleManager(connection.world)
vehicle = vehicle_mgr.spawn_vehicle()

# Create orchestrator
orchestrator = SimulationOrchestrator(
    config=config,
    connection=connection,
    vehicle=vehicle
)

# Run simulation loop
orchestrator.run()
```

### Using Detection/Decision Clients

```python
from lkas.detection import DetectionClient
from lkas.decision import DecisionClient
from lkas.detection.core.config import ConfigManager

# Initialize clients
config = ConfigManager.load('config.yaml')
detection_client = DetectionClient(config)
decision_client = DecisionClient(config)

# Send image for detection
detection_client.write_image(image_array, frame_id=123)

# Read detection result
detection_msg = detection_client.read_detection()
if detection_msg:
    print(f"Lanes detected: {detection_msg.left_lane}, {detection_msg.right_lane}")

# Read steering command from decision
steering_msg = decision_client.read_steering()
if steering_msg:
    print(f"Steering: {steering_msg.steering}")
```

## Architecture

### System Flow

```
┌─────────────────────────────────────────────────────┐
│             CARLA Simulator                         │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐  │
│  │  World   │ ───▶ │ Vehicle  │ ───▶ │  Camera  │  │
│  └──────────┘      └──────────┘      └──────────┘  │
└─────────────────────────────────────────────────────┘
         │                                    │
         │ Steering                           │ Image
         ▼                                    ▼
┌──────────────────────┐         ┌──────────────────────┐
│  Decision Module     │         │  Detection Module    │
│  (Shared Memory)     │ ◀────── │  (Shared Memory)     │
└──────────────────────┘         └──────────────────────┘
         │                                    │
         │ Steering Command                   │ Detection Result
         ▼                                    ▼
┌─────────────────────────────────────────────────────┐
│           Simulation Orchestrator                   │
│  • Reads detections via shared memory               │
│  • Reads steering via shared memory                 │
│  • Applies control to CARLA vehicle                 │
│  • Publishes vehicle status to LKAS broker (ZMQ)    │
│  • Receives actions from LKAS broker (ZMQ)          │
└─────────────────────────────────────────────────────┘
         │                                    │
         │ Vehicle Status (5562)              │ Actions (5561)
         ▼                                    ▼
┌─────────────────────────────────────────────────────┐
│              LKAS ZMQ Broker                        │
│  • Routes vehicle status to viewers                 │
│  • Routes actions to simulation                     │
│  • Broadcasts frames and detection data             │
└─────────────────────────────────────────────────────┘
         │
         │ All data (5557)
         ▼
┌─────────────────────────────────────────────────────┐
│              Web Viewer                             │
│  • Displays video stream with lane overlays        │
│  • Shows vehicle status (speed, position)           │
│  • Interactive controls (pause/resume/respawn)      │
└─────────────────────────────────────────────────────┘
```

### Communication Architecture

**Shared Memory (Low Latency IPC):**
- **Image Channel**: Sends camera images to detection module
- **Detection Channel**: Receives lane detection results
- **Control Channel**: Receives steering commands from decision module
- Benefits: ~0.1ms latency, zero-copy transfer

**ZMQ (Remote Viewer Support):**
- **Vehicle Status Publisher** (Port 5562): Sends vehicle state to LKAS broker
  - Data: steering, throttle, brake, speed, position, rotation, pause state
- **Action Subscriber** (Port 5561): Receives actions from LKAS broker
  - Actions: pause, resume, respawn
- Benefits: Network-capable, multiple subscribers, fire-and-forget

## Configuration

Configuration is managed via `config.yaml` in the project root.

### CARLA Settings

```yaml
carla:
  host: "localhost"
  port: 2000
  timeout: 10.0
  vehicle_type: "vehicle.tesla.model3"
  spawn_point: null  # null for random spawn
```

### Camera Settings

```yaml
camera:
  width: 800
  height: 600
  fov: 90.0
  position:
    x: 2.0
    y: 0.0
    z: 1.5
  rotation:
    pitch: -10.0
    yaw: 0.0
    roll: 0.0
```

### Visualization Settings

```yaml
visualization:
  web_port: 8080              # Web viewer port (runs separately)
  show_spectator_overlay: true
  follow_with_spectator: false
  show_hud: true
  show_steering: true
  fill_lane: true
  enable_alerts: true

# Note: Web viewer now runs as separate process via 'viewer' command
# It connects to LKAS broker which receives data from simulation
```

### Performance Settings

```yaml
performance:
  target_fps: 30
  max_frame_skip: 5
  enable_logging: true
  log_level: "INFO"
```

## Troubleshooting

### CARLA Connection Issues

**Problem**: `RuntimeError: time-out of 10.0s while waiting for the simulator`

**Solutions**:
- Ensure CARLA is running: `ps aux | grep CarlaUE4`
- Check CARLA is listening: `netstat -an | grep 2000`
- Increase timeout: `simulation --timeout 30.0`
- Try different port: `simulation --port 2001`

### Visualization Issues

**Problem**: Web viewer shows blank page

**Solutions**:
- Check web port is accessible: `curl http://localhost:8080`
- Try different port: `simulation --web-port 8081`
- Check browser console for errors

**Problem**: OpenCV window doesn't appear

**Solutions**:
- Ensure X11 is available: `echo $DISPLAY`
- Use web viewer instead: `simulation --viewer web`
- Check OpenCV installation: `python -c "import cv2; print(cv2.__version__)"`

### Performance Issues

**Problem**: Low FPS, laggy simulation

**Solutions**:
- Reduce camera resolution in config.yaml
- Use headless mode: `simulation --viewer none`
- Check CARLA server performance
- Ensure detection/decision servers are responsive

### Shared Memory Issues

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: '/dev/shm/...'`

**Solutions**:
- Ensure detection server is running: `ps aux | grep lane-detection`
- Ensure decision server is running: `ps aux | grep decision-server`
- Check shared memory: `ls -la /dev/shm/`
- Restart all modules in correct order

## Related Modules

- [LKAS Detection Module](../lkas/detection/README.md) - Lane detection algorithms
- [LKAS Decision Module](../lkas/decision/) - Control decision logic
- [Viewer Module](../viewer/README.md) - Remote web viewer

## Performance Metrics

Typical performance on modern hardware:

| Metric | Value | Notes |
|--------|-------|-------|
| FPS | 25-30 | With web visualization |
| Detection Latency | 5-10ms | CV method |
| Decision Latency | <1ms | PD controller |
| Total Loop Time | ~33ms | 30 FPS |
| Memory (Simulation) | ~200MB | Excluding CARLA |

## References

- [CARLA Documentation](https://carla.readthedocs.io/)
- [Main Project README](../../README.md)
- [Configuration Guide](../../config.yaml)

## License

See [LICENSE](../../LICENSE) file in project root.
