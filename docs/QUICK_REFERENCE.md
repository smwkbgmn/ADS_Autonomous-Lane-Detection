# Terminal Display Quick Reference

## What You Asked For

### 1. Two-Section Output (Footer Line)
✅ **Implemented**: Persistent footer at bottom, scrolling content above
- Like `npm install`, `cargo build`, `apt upgrade` progress displays
- Footer updates in-place without scrolling

### 2. Ordered Initialization Messages
✅ **Implemented**: Messages from concurrent Detection and Decision servers appear in order
- Detection initialization completes first
- Decision initialization follows
- No more mixed/interleaved output

## Quick Commands

```bash
# Run the demo
python test_terminal_display.py

# Run LKAS with new display
lkas --method cv

# Test syntax
python -m py_compile src/lkas/utils/terminal.py
python -m py_compile src/lkas/run.py
```

## Code Usage

### Print Messages
```python
from lkas.utils.terminal import TerminalDisplay

terminal = TerminalDisplay(enable_footer=True)
terminal.print("Starting server...", prefix="[LKAS]")
```

### Update Footer
```python
terminal.update_footer("FPS: 30.2 | Frame: 1234 | Time: 15.2ms")
```

### Ordered Logging
```python
from lkas.utils.terminal import OrderedLogger

logger = OrderedLogger("[DETECTION]", terminal)
logger.log("Loading...")      # Buffer
logger.log("✓ Loaded")        # Buffer
logger.flush()                # Print all at once
```

## Visual Example

```
Normal Messages (Scroll)
↓
[LKAS] Starting detection server...
[DETECTION] ✓ Configuration loaded
[DETECTION] ✓ Detector ready
[DECISION ] ✓ Configuration loaded
[LKAS] System running
[LKAS] Checkpoint: 150 frames
                                          ← Scrolls up as new messages arrive
─────────────────────────────────────────
[DET] 30.2 FPS | Frame 1234 | [DEC] 30.5 FPS   ← Stays at bottom, updates in-place
```

## Key Files

```
src/lkas/utils/
├── terminal.py              # Main implementation
├── README.md                # Detailed docs
└── ARCHITECTURE.md          # Technical details

src/lkas/
└── run.py                   # Integrated into LKAS launcher

test_terminal_display.py     # Demo script
TERMINAL_DISPLAY_GUIDE.md    # Complete guide
```

## How It Works

1. **Regular messages** → `terminal.print()` → Scrolling area
2. **Stats lines** (with "FPS") → Detected → Footer update
3. **Initialization** → Buffered → Flushed in order (Detection, then Decision)

## Benefits

| Before | After |
|--------|-------|
| Mixed initialization messages | Clean, ordered initialization |
| Stats scroll away | Stats persist in footer |
| Hard to see current status | Always visible at bottom |
| Looks unprofessional | Professional appearance |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Footer not showing | Check terminal supports ANSI codes |
| Messages still mixed | Increase initialization timeout |
| Stats not in footer | Verify line contains "FPS" |
| Garbled output | Set `enable_footer=False` |

## Documentation

- **TERMINAL_DISPLAY_GUIDE.md** - Complete implementation guide
- **src/lkas/utils/README.md** - API documentation
- **src/lkas/utils/ARCHITECTURE.md** - Technical architecture
- **This file** - Quick reference

## Summary

✅ Footer line stays at bottom (like install progress)
✅ Initialization messages print in order (Detection → Decision)
✅ Thread-safe for concurrent processes
✅ Easy to use API
✅ Professional appearance
