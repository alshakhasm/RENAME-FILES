# Docker GUI Setup Guide

## Prerequisites

### 1. Install XQuartz (macOS X11 Server)

```bash
brew install --cask xquartz
```

**OR** download from: https://www.xquartz.org/

### 2. Configure XQuartz

1. **Open XQuartz** from Applications/Utilities
2. Go to **XQuartz → Preferences** (or Settings)
3. Click the **Security** tab
4. **Enable** "Allow connections from network clients"
5. **Restart XQuartz** completely (Quit and reopen)

### 3. Configure X11 Access

After XQuartz is running, open Terminal and run:

```bash
# Allow localhost to access X11
xhost + 127.0.0.1
```

You'll see: `127.0.0.1 being added to access control list`

## Building the Docker Image

### Fix Docker Desktop Issues (if needed)

If you see "input/output error" during build:

1. **Restart Docker Desktop**:
   - Click Docker icon in menu bar
   - Select "Restart"
   
2. **If that doesn't work, reset Docker**:
   - Docker Desktop → Preferences → Resources → Advanced
   - Click "Reset to defaults"
   - Or: Troubleshoot → "Reset to factory defaults"

### Build the Image

```bash
cd "/Users/Mohammad/Documents/app development folder/RE-N"
docker-compose build
```

This will:
- Create a Python 3.11 image with tkinter
- Install X11 utilities (xdpyinfo for display checking)
- Copy the application code and GUI
- Set up proper permissions

## Running the GUI

### Option 1: Using docker-compose (Recommended)

```bash
# Make sure XQuartz is running and xhost configured
xhost + 127.0.0.1

# Launch the GUI
docker-compose up
```

The GUI window should appear on your screen!

### Option 2: Manual Docker Run

```bash
# Set display variable
export DISPLAY=host.docker.internal:0

# Run with volume mounting
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v ~/Documents:/data:rw \
  --network host \
  date-prefix-renamer:latest
```

## Troubleshooting

### "Cannot open display" Error

**Cause**: X11 forwarding not configured properly

**Solution**:
```bash
# 1. Verify XQuartz is running
ps aux | grep XQuartz

# 2. Check DISPLAY variable
echo $DISPLAY  # Should show :0 or similar

# 3. Re-allow access
xhost + 127.0.0.1

# 4. Try again
docker-compose up
```

### "Connection refused" Error

**Cause**: XQuartz not accepting network connections

**Solution**:
1. Open XQuartz Preferences
2. Security tab
3. Enable "Allow connections from network clients"
4. **Restart XQuartz completely**

### GUI Window Not Appearing

**Check Docker logs**:
```bash
docker-compose logs
```

**Look for**:
- "✓ X11 display available" - Good!
- "✗ X11 display not accessible" - Fix XQuartz config

### Permission Denied on /data

**Solution**:
```bash
# Check permissions on your mounted directory
ls -la ~/Documents

# Fix if needed
chmod -R 755 ~/Documents
```

## Testing Without Docker

To verify the GUI works on your system directly:

```bash
cd "/Users/Mohammad/Documents/app development folder/RE-N"
python3.11 modern_gui.py
```

If this works but Docker doesn't, it's a Docker X11 configuration issue.

## CLI Mode (No GUI)

If you can't get the GUI working, you can still use CLI mode:

```bash
# Process a directory
docker run --rm \
  -v ~/Documents:/data \
  date-prefix-renamer:latest \
  cli /data/your-folder

# Preview changes only (dry-run)
docker run --rm \
  -v ~/Documents:/data \
  date-prefix-renamer:latest \
  cli /data/your-folder --dry-run
```

## Docker Compose Configuration

The `docker-compose.yml` includes:

```yaml
environment:
  - DISPLAY=host.docker.internal:0  # Route to macOS X11

volumes:
  - ~/Documents:/data:rw            # Your files (read/write)
  - /tmp/.X11-unix:/tmp/.X11-unix:rw  # X11 socket

network_mode: "host"                # Access host network for X11
```

**Customize**: Edit `docker-compose.yml` to change the mounted directory from `~/Documents` to your preferred location.

## Advanced: XQuartz Configuration via CLI

```bash
# Enable remote connections (requires XQuartz restart)
defaults write org.xquartz.X11 nolisten_tcp -boolean false

# Verify setting
defaults read org.xquartz.X11 nolisten_tcp  # Should show 0

# Restart XQuartz for changes to take effect
```

## Quick Start Checklist

- [ ] XQuartz installed
- [ ] XQuartz "Allow connections from network clients" enabled
- [ ] XQuartz restarted after configuration
- [ ] XQuartz is currently running
- [ ] `xhost + 127.0.0.1` executed in Terminal
- [ ] Docker Desktop running without errors
- [ ] Docker image built: `docker-compose build`
- [ ] Launch: `docker-compose up`

## Support

If you continue to have issues:

1. **Check Docker version**: `docker --version` (should be 20.10+)
2. **Check XQuartz version**: XQuartz → About (should be 2.7.11+)
3. **Test X11 locally**: `xclock` should show a clock window
4. **Test Docker X11**: `docker run --rm -e DISPLAY=host.docker.internal:0 -v /tmp/.X11-unix:/tmp/.X11-unix:rw gns3/xeyes`

## References

- XQuartz: https://www.xquartz.org/
- Docker Desktop for Mac: https://docs.docker.com/desktop/install/mac-install/
- tkinter documentation: https://docs.python.org/3/library/tkinter.html
