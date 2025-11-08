# LKAS Terminal Display - Implementation Guide

## Overview

Your LKAS system now has a **structured terminal display** with two key features:

### 1. **Persistent Footer Line**
Live stats that stay at the bottom (like npm/apt install progress):
```
[DET] 30.2 FPS | Frame 1234 | Processing: 15.20ms | [DEC] 30.5 FPS | Steering: +0.125
```

### 2. **Ordered Initialization Messages**
Messages from concurrent Detection and Decision servers now appear in order instead of being mixed/interleaved.

## Quick Start

### Test the Demo
```bash
python test_terminal_display.py
```

This shows:
- How initialization messages appear in order
- How the footer stays at the bottom while logs scroll above
- Live stats updates

### Run LKAS with New Display
```bash
lkas --method cv
```

You'll see:
- Clean, ordered initialization from both servers
- Live processing stats in the footer (updated every 3 seconds)
- All messages properly organized with `[DETECTION]` and `[DECISION]` prefixes

## What Changed

### Before
```
[DETECTION] ✓ Detector ready
[DECISION ] Loading configuration...
[DETECTION] Creating shared memory...
[DECISION ] ✓ Configuration loaded
28.5 FPS | Frame 1234 | Processing: 15.20ms
29.1 FPS | Frame 1234 | Decision: 2.10ms
28.7 FPS | Frame 1235 | Processing: 15.30ms
```
❌ Initialization messages mixed
❌ Stats messages scroll away
❌ Hard to see current status

### After
```
======================================================================
[DETECTION] Loading configuration...
[DETECTION] ✓ Configuration loaded
[DETECTION] ✓ Detector ready
[DETECTION] Creating shared memory...

[DECISION ] Loading configuration...
[DECISION ] ✓ Configuration loaded
[DECISION ] ✓ Decision controller ready
======================================================================

[DET] 28.5 FPS | Frame 1234 | Processing: 15.20ms | [DEC] 29.1 FPS | Decision: 2.10ms
```
✓ Initialization messages appear in order (Detection first, then Decision)
✓ Stats stay in persistent footer at bottom
✓ Current status always visible

## Architecture

### New Module: `src/lkas/utils/terminal.py`

**`TerminalDisplay`**
- Manages two-section terminal output
- Main area: scrolling logs
- Footer area: persistent status line
- Uses ANSI escape codes for in-place updates

**`OrderedLogger`**
- Buffers messages from concurrent processes
- Flushes in specified order
- Prevents interleaved output

**Utility Functions**
- `format_fps_stats()`: Format statistics for footer
- `create_progress_bar()`: ASCII progress bars

### Updated: `src/lkas/run.py`

**Key Changes:**
1. **Terminal Display Integration**
   ```python
   self.terminal = TerminalDisplay(enable_footer=True)
   ```

2. **Ordered Loggers for Each Server**
   ```python
   self.detection_logger = OrderedLogger("[DETECTION]", self.terminal)
   self.decision_logger = OrderedLogger("[DECISION ]", self.terminal)
   ```

3. **Stats Detection & Footer Update**
   - Detects FPS stats lines from subprocess output
   - Updates footer instead of letting them scroll
   - Combines stats from both servers in one line

4. **Buffered Initialization**
   - Reads initialization output into buffers
   - Flushes Detection first, then Decision
   - Ensures clean, ordered startup display

## How It Works

### During Initialization (Ordered)
```python
# Buffer detection initialization (5 seconds)
while time.time() < init_timeout:
    self._read_process_output(self.detection_process, "DETECTION", self.detection_logger)
self.detection_logger.flush()  # Print all at once

# Then buffer decision initialization (3 seconds)
while time.time() < init_timeout:
    self._read_process_output(self.decision_process, "DECISION", self.decision_logger)
self.decision_logger.flush()  # Print all at once
```

### During Runtime (Live Footer)
```python
def _read_process_output(self, process, prefix, logger):
    line = process.stdout.readline()

    # Check if it's a stats line
    if line.startswith('\r') or 'FPS' in line:
        # Update stats tracking
        if prefix == "DETECTION":
            self.last_detection_stats = line
        else:
            self.last_decision_stats = line
        self._update_footer()  # Update persistent footer
    else:
        # Regular message - print to scrolling area
        logger.print_immediate(line)
```

### Footer Update
```python
def _update_footer(self):
    parts = []
    if self.last_detection_stats:
        parts.append(f"[DET] {self.last_detection_stats}")
    if self.last_decision_stats:
        parts.append(f"[DEC] {self.last_decision_stats}")

    footer_text = " | ".join(parts)
    self.terminal.update_footer(footer_text)
```

## Benefits

### 1. **Professional Appearance**
- Similar to modern package managers (npm, cargo, pip)
- Clean, organized output
- Always see what's happening

### 2. **Better Debugging**
- Initialization messages in logical order
- Easy to spot where issues occur
- Stats always visible at bottom

### 3. **Real-time Monitoring**
- Live FPS from both Detection and Decision
- Frame processing times
- Current steering/throttle values
- No more scrolling to see status

### 4. **Thread-Safe**
- Works with concurrent processes
- Prevents race conditions
- Clean output even with multiple writers

## Examples

### Example 1: Successful Startup
```
======================================================================
                    LKAS System Launcher
======================================================================
  Detection Method: CV
  Image SHM: camera_feed
  Detection SHM: detection_results
======================================================================

[LKAS] Starting detection server...
[LKAS] ✓ Detection server started (PID: 12345)

[DETECTION] Loading configuration...
[DETECTION] ✓ Configuration loaded
[DETECTION] Initializing CV detector...
[DETECTION] ✓ Detector ready: CVLaneDetector
[DETECTION] Creating detection shared memory 'detection_results'...
[DETECTION] ✓ Created detection output
[DETECTION] Connecting to image shared memory 'camera_feed'...
[DETECTION] ✓ Connected to image input

[LKAS] Starting decision server...
[LKAS] ✓ Decision server started (PID: 12346)

[DECISION ] Loading configuration...
[DECISION ] ✓ Configuration loaded
[DECISION ] Initializing decision controller...
[DECISION ] ✓ Decision controller ready
[DECISION ] Connecting to detection shared memory 'detection_results'...
[DECISION ] ✓ Connected to detection input

======================================================================
[LKAS] System running - Press Ctrl+C to stop
======================================================================

[DET] 30.2 FPS | Frame 1234 | Processing: 15.20ms | Lanes: L=True R=True | [DEC] 30.5 FPS | Frame 1234 | Decision: 2.10ms | Steering: +0.125 | Throttle: 0.650
```

### Example 2: Runtime with Occasional Messages
```
[LKAS] Checkpoint: Processed 150 frames successfully
[DETECTION] Model confidence: 0.96

[DET] 29.8 FPS | Frame 1567 | Processing: 15.80ms | Lanes: L=True R=True | [DEC] 30.1 FPS | Frame 1567 | Decision: 2.15ms | Steering: -0.032 | Throttle: 0.720
```
The footer line stays at bottom, updating continuously while messages appear above.

## Customization

### Disable Footer
If you prefer traditional scrolling output:
```python
self.terminal = TerminalDisplay(enable_footer=False)
```

### Change Footer Format
Edit `_update_footer()` in `src/lkas/run.py`:
```python
def _update_footer(self):
    # Custom format
    footer = f"Detection: {self.last_detection_stats}\nDecision: {self.last_decision_stats}"
    self.terminal.update_footer(footer)
```

### Add More Stats
Track additional metrics:
```python
self.last_frame_id = 0
self.total_frames = 0

# In footer:
footer = f"Total: {self.total_frames} | Current: {self.last_frame_id} | {stats}"
```

## Files Added/Modified

### New Files
- `src/lkas/utils/__init__.py` - Package marker
- `src/lkas/utils/terminal.py` - Terminal display utilities
- `src/lkas/utils/README.md` - Detailed utility documentation
- `test_terminal_display.py` - Demo script
- `TERMINAL_DISPLAY_GUIDE.md` - This guide

### Modified Files
- `src/lkas/run.py` - Integrated terminal display

## Troubleshooting

### Footer not visible
- **Cause**: Terminal doesn't support ANSI escape codes
- **Solution**: Set `enable_footer=False`

### Messages still mixed
- **Cause**: Initialization timeout too short
- **Solution**: Increase timeout in `run()` method

### Footer overwriting messages
- **Cause**: Thread timing issue
- **Solution**: Already handled by locks, but increase `time.sleep()` if needed

### Stats not appearing in footer
- **Cause**: Stats line format not detected
- **Solution**: Check pattern in `_read_process_output()` - looks for `\r` or `'FPS'` in line

## Future Enhancements

Possible additions:
1. **Color coding** - Different colors for Detection vs Decision
2. **Progress bars** - Show initialization progress
3. **Split footer** - Separate lines for each server
4. **Web dashboard** - Expose stats via HTTP endpoint
5. **Logging levels** - Filter messages by severity

## Testing

### Unit Tests
```bash
python -m pytest src/lkas/utils/ -v
```

### Integration Test
```bash
# Terminal 1: Start LKAS
lkas --method cv

# Terminal 2: Start simulation
simulation --autopilot-duration 10

# Observe:
# - Ordered initialization messages
# - Live stats in footer
# - Messages scroll above footer
```

### Demo Test
```bash
python test_terminal_display.py
```

## Summary

You now have:
✅ **Persistent footer** showing live FPS and processing stats
✅ **Ordered initialization** messages from concurrent servers
✅ **Professional output** similar to modern CLI tools
✅ **Thread-safe** implementation for concurrent processes
✅ **Easy to use** API for future enhancements

The terminal display makes it much easier to monitor your LKAS system in real-time and debug issues during initialization!
