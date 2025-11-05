# Autonomous Driving Lane Keeping System

A modular, production-ready lane keeping system for CARLA simulator with clean separation of concerns.

## 🌟 Features

- **Clean 3-Module Architecture**: Simulation, Detection, Decision
- **Dual Detection Methods**: Computer Vision (OpenCV) and Deep Learning (PyTorch CNN)
- **Distributed System**: Run detection as separate process
- **Multiple Visualization Options**: OpenCV, Pygame, and Web viewer (no X11 needed!)
- **Production Ready**: Process isolation, shared memory communication, fault tolerance
- **Modern Python Package**: `pyproject.toml`, editable install, entry point scripts

## 📦 Installation

### Prerequisites
- Python 3.10+
- CARLA 0.9.15+ simulator
- GPU (optional, for deep learning detection)

### Install Package

```bash
# Clone repository
git clone <repository-url>
cd seame-ads

# Install in editable mode with all dependencies
pip install -e .

# Or install with optional development tools
pip install -e ".[dev]"

# Or install everything (dev + training tools)
pip install -e ".[all]"
```

This installs the package as `ads-skynet` with four command-line entry points:
- `simulation` - Main CARLA simulation
- `lane-detection` - Standalone detection server
- `decision-server` - Decision/control server
- `viewer` - Remote web viewer

## 🚀 Quick Start

### Integrated Mode (All-in-one)

```bash
# Terminal 1: Start CARLA server
./CarlaUE4.sh

# Terminal 2: Start LKAS (detection + decision integrated)
lkas --method cv --viewer web --web-port 8080

# Open browser: http://localhost:8080
```

### Modular Mode (Separate Processes)

**Better for distributed systems and resource allocation:**

```bash
# Terminal 1: Start CARLA server
./CarlaUE4.sh

# Terminal 2: Start detection server
lane-detection --method cv

# Terminal 3: Start decision server
decision-server

# Terminal 4: Start simulation orchestrator
simulation --viewer web --web-port 8080

# Open browser: http://localhost:8080
```

**Benefits:**
- ✅ Separate processes for detection and decision
- ✅ Shared memory for low-latency communication
- ✅ Independent lifecycle management
- ✅ Easy to distribute across machines

**Alternative (using Python modules directly):**
```bash
# Terminal 2
python -m lkas.detection.run --method cv

# Terminal 3
python -m lkas.decision.run

# Terminal 4
python -m simulation.run --viewer web
```

## 📁 Project Structure

```
ads_skynet/
├── pyproject.toml           # 📦 Package configuration & dependencies
├── config.yaml              # ⚙️ System configuration (auto-loaded from project root)
│
├── src/
│   │
│   ├── lkas/                ⭐ Lane Keeping Assist System
│   │   ├── run.py           # Integrated LKAS entry point
│   │   ├── system.py        # LKAS orchestrator
│   │   │
│   │   ├── detection/       # Lane detection module
│   │   │   ├── run.py       # Detection server entry point
│   │   │   ├── server.py    # DetectionServer with shared memory
│   │   │   ├── client.py    # DetectionClient for IPC
│   │   │   ├── detector.py  # Core LaneDetection wrapper
│   │   │   │
│   │   │   ├── core/        # Core abstractions
│   │   │   │   ├── config.py     # Configuration management
│   │   │   │   ├── factory.py    # Factory pattern
│   │   │   │   ├── interfaces.py # Abstract base classes
│   │   │   │   └── models.py     # Data models (Lane, DetectionResult)
│   │   │   │
│   │   │   ├── integration/ # IPC infrastructure
│   │   │   │   ├── messages.py              # Message definitions
│   │   │   │   ├── shared_memory_detection.py  # Image/detection channels
│   │   │   │   └── shared_memory_control.py    # Control channel
│   │   │   │
│   │   │   └── method/      # Detection implementations
│   │   │       ├── computer_vision/  # OpenCV-based
│   │   │       │   └── cv_lane_detector.py
│   │   │       └── deep_learning/    # CNN-based
│   │   │           ├── lane_net.py
│   │   │           └── lane_net_base.py
│   │   │
│   │   └── decision/        # Control decision module
│   │       ├── run.py       # Decision server entry point
│   │       ├── server.py    # DecisionServer
│   │       ├── client.py    # DecisionClient
│   │       ├── analyzer.py  # Lane position analysis
│   │       └── controller.py # PD control logic
│   │
│   ├── simulation/          ⭐ CARLA simulation & orchestration
│   │   ├── run.py           # Main simulation entry point
│   │   ├── orchestrator.py  # System orchestrator
│   │   │
│   │   ├── carla_api/       # CARLA interface
│   │   │   ├── connection.py # CARLA connection
│   │   │   ├── vehicle.py    # Vehicle control
│   │   │   └── sensors.py    # Camera sensors
│   │   │
│   │   ├── integration/     # LKAS integration
│   │   │   └── __init__.py  # Detection/Decision clients
│   │   │
│   │   ├── processing/      # Frame processing
│   │   │   ├── frame_processor.py  # Processing pipeline
│   │   │   └── metrics_logger.py   # Performance metrics
│   │   │
│   │   └── utils/           # Utilities
│   │       └── visualizer.py # Visualization helpers
│   │
│   └── viewer/              ⭐ Remote web viewer
│       ├── run.py           # Web viewer entry point
│       ├── __init__.py      # Package exports
│       └── README.md        # Viewer documentation
│
└── docs/                    # Documentation
    └── README.md            # Documentation index
```

## 🎯 Architecture

### Clean 3-Module Separation

```
┌──────────────────────────────────────────────────────────────┐
│                    simulation/                               │
│              (CARLA Orchestration Layer)                     │
│  • Runs CARLA simulation                                     │
│  • Coordinates LKAS modules via shared memory                │
│  • Provides visualization                                    │
└──────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌───────────────────┐  ┌──────────────────┐
│  lkas/         │  │   lkas/           │  │    simulation/   │
│  detection/    │  │   decision/       │  │    carla_api/    │
│                │  │                   │  │                  │
│ • CV Detection │  │ • Lane Analysis   │  │ • Connection     │
│ • DL Detection │  │ • PD Controller   │  │ • Vehicle        │
│ • Shared Mem   │  │ • Steering Calc   │  │ • Sensors        │
└────────────────┘  └───────────────────┘  └──────────────────┘
```

### Module Responsibilities

**`simulation/`** - CARLA Integration & Orchestration
- Connects to CARLA simulator
- Manages vehicles and sensors
- Orchestrates LKAS modules via shared memory
- **Contains:** CARLA API wrappers, orchestrator, visualization

**`lkas/detection/`** - Pure Lane Detection
- Detects lanes from images (CV or DL)
- Runs as separate process with shared memory IPC
- No CARLA dependencies
- **Contains:** detection algorithms, server/client, shared memory channels

**`lkas/decision/`** - Control Decisions
- Analyzes lane position from detection results
- Generates steering commands via PD controller
- Runs as separate process with shared memory IPC
- **Contains:** analyzer, controller, server/client

## 🎮 Usage

### Basic Usage (Local)

```bash
# Integrated mode (easiest)
lkas --method cv --viewer web --web-port 8080

# Or modular mode (separate processes)
# Terminal 1: Detection server
lane-detection --method cv

# Terminal 2: Decision server
decision-server

# Terminal 3: Simulation
simulation --viewer web --web-port 8080
```

### Remote CARLA Server

```bash
# Simulation connects to remote CARLA
simulation \
  --host <CARLA_HOST> \
  --port 2000 \
  --viewer web \
  --web-port 8080
```

### Deep Learning Detection

```bash
# Integrated mode with DL
lkas --method dl --viewer web

# Or modular mode with DL
lane-detection --method dl
decision-server
simulation --viewer web
```

### Viewer Options

```bash
# Web viewer (works in Docker, no X11 needed)
lkas --viewer web --web-port 8080

# OpenCV window (requires X11)
lkas --viewer opencv

# Pygame window
lkas --viewer pygame

# No visualization (headless)
lkas --no-display
```

## 🔧 Configuration

The system automatically loads `config.yaml` from the project root. You can also specify a custom config:

```bash
# Use project root config.yaml (default)
simulation

# Use custom config
simulation --config /path/to/custom-config.yaml

# Use built-in defaults (no file)
simulation --config default
```

### Configuration File Structure

Edit `config.yaml` in the project root:

```yaml
# CARLA Connection
carla:
  host: "localhost"
  port: 2000
  vehicle_type: "vehicle.tesla.model3"

# Camera Settings
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

# Lane Analysis & Control
lane_analyzer:
  kp: 0.5              # Proportional gain
  kd: 0.1              # Derivative gain
  drift_threshold: 0.15
  departure_threshold: 0.35

# Adaptive Throttle Policy
throttle_policy:
  base: 0.15           # Base throttle
  min: 0.05            # Minimum during turns
  steer_threshold: 0.15
  steer_max: 0.70
```

See [config.yaml](config.yaml) for full configuration options.

## 🧪 Testing

### Verify Installation

```bash
# Check if entry points are installed
which simulation
which lane-detection

# Test import
python -c "import detection; import simulation; import decision; print('✓ All modules imported')"
```

### Test Detection Server

```bash
# Terminal 1: Start server
lane-detection --method cv --port 5556

# Terminal 2: Test connection
python -c "from simulation.integration.communication import DetectionClient; print('✓ Detection server works')"
```

### Run Tests (if dev dependencies installed)

```bash
# Install with dev tools
pip install -e ".[dev]"

# Run tests
pytest
```

## 🔍 Keyboard Controls

When running with visualization:

- **Q** - Quit
- **S** - Toggle autopilot
- **O** - Toggle spectator overlay
- **F** - Toggle spectator follow mode
- **R** - Respawn vehicle
- **T** - Teleport to next spawn point

## 📊 Performance Metrics

```
Frame 00150 | FPS: 28.5 | Lanes: LR | Steering: +0.123 | Timeouts: 0
```

## 📋 System Requirements

### For M1 Mac Development
- Docker Desktop with Rosetta 2 enabled
- VSCode with Dev Containers extension
- Remote Linux machine running CARLA server

### For Native Linux Development
- Ubuntu 18.04+
- CARLA 0.9.15+ simulator
- Python 3.10+
- GPU (optional, for deep learning)

## 🚀 Development Setup

### Native Development

```bash
# Clone and install
git clone <repository-url>
cd seame-ads
pip install -e ".[dev]"

# Start developing
lane-detection --help
simulation --help
```

### Dev Container (M1 Mac / Remote Development)

1. **Open in Dev Container:**
   ```bash
   cd seame-ads
   code .
   # VSCode: Cmd+Shift+P → "Reopen in Container"
   ```

2. **Package is auto-installed in container**
   ```bash
   # Use entry points directly
   lane-detection --method cv --port 5556
   simulation --detector-url tcp://localhost:5556 --viewer web
   ```

See [.docs/DEVCONTAINER_SETUP.md](.docs/DEVCONTAINER_SETUP.md) for details.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [src/lkas/detection/README.md](src/lkas/detection/README.md) | Detection module guide |
| [src/simulation/README.md](src/simulation/README.md) | Simulation module guide |
| [src/viewer/README.md](src/viewer/README.md) | Viewer module guide |

## 🎓 For Students

This project demonstrates:

- ✅ **Clean Architecture**: Separation of concerns
- ✅ **Design Patterns**: Factory, Strategy, Observer
- ✅ **Distributed Systems**: ZMQ communication
- ✅ **Multiple Algorithms**: CV and DL approaches
- ✅ **Production Ready**: Error handling, logging, metrics

## 🆘 Quick Reference

### Installed Commands

After `pip install -e .`, you get two entry points:

| Command | Purpose | Equivalent Python Module |
|---------|---------|--------------------------|
| `lkas` | Integrated LKAS | `python -m lkas.run` |
| `simulation` | CARLA simulation | `python -m simulation.run` |
| `lane-detection` | Detection server | `python -m lkas.detection.run` |
| `decision-server` | Decision server | `python -m lkas.decision.run` |
| `viewer` | Web viewer | `python -m viewer.run` |

### Command Templates

```bash
# Integrated mode (simplest)
lkas --method cv --viewer web --web-port 8080

# Modular mode (separate processes)
lane-detection --method cv
decision-server
simulation --viewer web --web-port 8080

# Remote CARLA + custom config
simulation \
  --host <REMOTE_IP> \
  --port 2000 \
  --config /path/to/config.yaml \
  --viewer web
```

### Package Structure

After installation, import modules directly:

```python
# Import LKAS detection
from lkas.detection.core.config import ConfigManager
from lkas.detection.core.models import Lane, DetectionResult
from lkas.detection import LaneDetection, DetectionClient

# Import LKAS decision
from lkas.decision import DecisionServer, DecisionClient

# Import simulation
from simulation import SimulationOrchestrator
from simulation.integration import DetectionClient, DecisionClient
```

## ✅ Why This Structure?

1. **`lkas/` is self-contained** - Complete lane keeping system, reusable in any project
2. **`lkas/detection/` is pure algorithms** - No CARLA dependency, works anywhere
3. **`lkas/decision/` is reusable logic** - Works with any detection system
4. **`simulation/` orchestrates** - CARLA-specific integration and coordination
5. **Shared memory IPC** - Low-latency inter-process communication
6. **Clear responsibilities** - Each module has ONE job
7. **Easy to test** - Pure functions, no entangled dependencies

## 🎁 Modern Python Package Benefits

This project uses modern Python packaging (`pyproject.toml`) instead of legacy `setup.py` and `requirements.txt`:

### ✅ Benefits

1. **Single Source of Truth** - All configuration in `pyproject.toml`
   - Dependencies, metadata, build config, tool settings
   - No more scattered `setup.py`, `requirements.txt`, `setup.cfg`, etc.

2. **Clean Imports** - No more `sys.path` hacks!
   ```python
   # ❌ Old way (brittle)
   sys.path.insert(0, str(Path(__file__).parent.parent))
   from detection.core.models import Lane

   # ✅ New way (clean)
   from detection.core.models import Lane
   ```

3. **Entry Point Scripts** - Installed commands available system-wide
   ```bash
   simulation --help      # Works from any directory
   lane-detection --help  # No need to cd into specific folders
   ```

4. **Editable Install** - Changes reflect immediately
   ```bash
   pip install -e .       # Edit code and run without reinstalling
   ```

5. **Optional Dependencies** - Install only what you need
   ```bash
   pip install -e .           # Basic install
   pip install -e ".[dev]"    # + development tools
   pip install -e ".[train]"  # + ML training tools
   pip install -e ".[all]"    # Everything
   ```

6. **Auto-Config Discovery** - Config file found automatically
   - Looks for `pyproject.toml` to find project root
   - Loads `config.yaml` from project root automatically
   - No hardcoded paths or relative path issues

7. **Tool Configuration** - Unified config for dev tools
   - pytest, black, mypy, isort all configured in `pyproject.toml`
   - Consistent formatting across team

### 📦 Package Info

- **Name**: `ads-skynet`
- **Version**: 0.1.0
- **Python**: 3.10+
- **License**: See LICENSE file

## 📝 License

See [LICENSE](LICENSE) file.

---

**Ready to start?** 👉 See [Quick Start](#-quick-start) above
