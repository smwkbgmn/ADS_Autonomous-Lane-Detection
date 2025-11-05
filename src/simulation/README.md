# Simulation Module

CARLA simulation orchestrator for the Lane Keeping Assist System.

## Overview

The simulation module integrates with CARLA simulator to provide:
- Vehicle spawning and control
- Camera sensor management
- LKAS module coordination via shared memory
- Real-time visualization (web, OpenCV, Pygame)
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
  - Automatic process lifecycle management

- **Visualization Options**:
  - Web viewer (no X11 required, works in Docker)
  - OpenCV window viewer
  - Pygame viewer
  - Headless mode for deployment

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

# Terminal 2: Start simulation with integrated LKAS
lkas --method cv --viewer web

# Or start simulation alone (requires separate LKAS servers)
simulation --viewer web

# Note: Web port defaults to 8080 from config.yaml
```

### Command Line Options

```bash
simulation --help

Options:
  --host HOST              CARLA server host (overrides config, default: from config.yaml)
  --port PORT              CARLA server port (overrides config, default: from config.yaml)
  --viewer {web,opencv,pygame,none}  Visualization mode (default: web)
  --web-port PORT          Web viewer port (overrides config, default: from config.yaml)
  --config PATH            Path to config file (default: auto-detected)
  --timeout SECONDS        CARLA connection timeout (default: 10.0)
```

### Examples

**Web viewer (recommended, no X11 required)**:
```bash
# Uses port from config.yaml (default: 8080)
simulation --viewer web

# Override port from command line
simulation --viewer web --web-port 8081

# Open http://localhost:8080 in browser (or your custom port)
```

**OpenCV window viewer**:
```bash
simulation --viewer opencv
```

**Headless mode** (no visualization):
```bash
simulation --viewer none
```

**Remote CARLA server**:
```bash
simulation --host 192.168.1.100 --port 2000 --viewer web
```

**Custom configuration**:
```bash
simulation --config /path/to/custom-config.yaml --viewer web
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
│  • Reads detections via DetectionClient             │
│  • Reads steering via DecisionClient                │
│  • Applies control to CARLA vehicle                 │
│  • Manages visualization                            │
└─────────────────────────────────────────────────────┘
```

### Shared Memory Communication

The simulation module uses shared memory for ultra-low latency IPC:

- **Detection Channel**: Receives lane detection results (left/right lanes)
- **Decision Channel**: Receives steering commands from decision module
- **Image Channel**: Sends camera images to detection module

**Benefits:**
- ~0.1ms latency (vs ~5-10ms for ZMQ)
- No network overhead
- Zero-copy data transfer
- Process isolation maintained

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
  web_port: 8080              # Web viewer port (default: 8080)
  show_spectator_overlay: true
  follow_with_spectator: false
  show_hud: true
  show_steering: true
  fill_lane: true
  enable_alerts: true
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
