#!/usr/bin/env python3
"""
LKAS System Launcher

Starts both Detection and Decision servers as a unified system.
Combines debug logs from both processes into one terminal.

Usage:
    # Start LKAS with Computer Vision detector
    lkas --method cv

    # Start LKAS with Deep Learning detector on GPU
    lkas --method dl --gpu 0

    # Custom configuration
    lkas --method cv --config path/to/config.yaml
"""

import argparse
import sys
import os
import subprocess
import signal
import time
import select
from pathlib import Path
from typing import Optional, List


class LKASLauncher:
    """Launches and manages both detection and decision servers."""

    def __init__(
        self,
        method: str = "cv",
        config: Optional[str] = None,
        gpu: Optional[int] = None,
        image_shm_name: str = "camera_feed",
        detection_shm_name: str = "detection_results",
        control_shm_name: str = "control_commands",
    ):
        """
        Initialize LKAS launcher.

        Args:
            method: Detection method (cv or dl)
            config: Path to configuration file
            gpu: GPU device ID (for DL method)
            image_shm_name: Shared memory name for camera images
            detection_shm_name: Shared memory name for detection results
            control_shm_name: Shared memory name for control commands
        """
        self.method = method
        self.config = config
        self.gpu = gpu
        self.image_shm_name = image_shm_name
        self.detection_shm_name = detection_shm_name
        self.control_shm_name = control_shm_name

        self.detection_process: Optional[subprocess.Popen] = None
        self.decision_process: Optional[subprocess.Popen] = None
        self.running = False

    def _build_detection_cmd(self) -> List[str]:
        """Build command for detection server."""
        cmd = [
            sys.executable,
            "-m",
            "lkas.detection.run",
            "--method",
            self.method,
            "--image-shm-name",
            self.image_shm_name,
            "--detection-shm-name",
            self.detection_shm_name,
            "--retry-count",
            "60",  # Wait up to 30 seconds for simulation
            "--retry-delay",
            "0.5",
        ]

        if self.config:
            cmd.extend(["--config", self.config])

        if self.gpu is not None and self.method == "dl":
            cmd.extend(["--gpu", str(self.gpu)])

        return cmd

    def _build_decision_cmd(self) -> List[str]:
        """Build command for decision server."""
        cmd = [
            sys.executable,
            "-m",
            "lkas.decision.run",
            "--detection-shm-name",
            self.detection_shm_name,
            "--control-shm-name",
            self.control_shm_name,
            "--retry-count",
            "60",  # Wait up to 30 seconds for detection server
            "--retry-delay",
            "0.5",
        ]

        if self.config:
            cmd.extend(["--config", self.config])

        return cmd

    def _print_header(self):
        """Print startup header."""
        print("\n" + "=" * 70)
        print(" " * 20 + "LKAS System Launcher")
        print("=" * 70)
        print(f"  Detection Method: {self.method.upper()}")
        if self.gpu is not None:
            print(f"  GPU Device: {self.gpu}")
        if self.config:
            print(f"  Config: {self.config}")
        print(f"  Image SHM: {self.image_shm_name}")
        print(f"  Detection SHM: {self.detection_shm_name}")
        print(f"  Control SHM: {self.control_shm_name}")
        print("=" * 70)
        print()

    def _read_process_output(self, process: subprocess.Popen, prefix: str):
        """
        Read and print process output with prefix.
        Non-blocking read using select.
        """
        if process.stdout is None:
            return

        # Use select to check if there's data to read (Unix-like systems)
        if hasattr(select, 'select'):
            ready, _, _ = select.select([process.stdout], [], [], 0)
            if not ready:
                return

            try:
                line = process.stdout.readline()
                if line:
                    line = line.decode('utf-8').rstrip()
                    if line:  # Only print non-empty lines
                        output = f"[{prefix}] {line}"
                        print(output)
                        if hasattr(self, 'log_file') and self.log_file:
                            self.log_file.write(output + "\n")
            except Exception:
                pass
        else:
            # Fallback for Windows (less efficient)
            try:
                line = process.stdout.readline()
                if line:
                    line = line.decode('utf-8').rstrip()
                    if line:
                        output = f"[{prefix}] {line}"
                        print(output)
                        if hasattr(self, 'log_file') and self.log_file:
                            self.log_file.write(output + "\n")
            except Exception:
                pass

    def _read_process_output_stderr(self, process: subprocess.Popen, prefix: str):
        """Read and print process stderr with prefix."""
        if process.stderr is None:
            return

        if hasattr(select, 'select'):
            ready, _, _ = select.select([process.stderr], [], [], 0)
            if not ready:
                return

            try:
                line = process.stderr.readline()
                if line:
                    line = line.decode('utf-8').rstrip()
                    if line:  # Only print non-empty lines
                        print(f"[{prefix}] {line}")
            except Exception:
                pass
        else:
            try:
                line = process.stderr.readline()
                if line:
                    line = line.decode('utf-8').rstrip()
                    if line:
                        print(f"[{prefix}] {line}")
            except Exception:
                pass

    def run(self):
        """Start both servers and manage their lifecycle."""
        self._print_header()

        # Open log file
        self.log_file = open("lkas_run.log", "w", buffering=1)
        print("[LKAS] Logging output to lkas_run.log")

        # Register signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            print("\n\n[LKAS] Received interrupt signal - shutting down...")
            if hasattr(self, 'log_file') and self.log_file:
                self.log_file.close()
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Start detection server
            print("[LKAS] Starting detection server...")
            detection_cmd = self._build_detection_cmd()
            self.detection_process = subprocess.Popen(
                detection_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,  # Unbuffered
            )
            print(f"[LKAS] ✓ Detection server started (PID: {self.detection_process.pid})")

            # Give detection server time to initialize and create detection_results
            time.sleep(3.0)

            # Check if detection server is still running
            if self.detection_process.poll() is not None:
                print("[LKAS] ✗ Detection server failed to start!")
                return 1

            # Start decision server
            print("[LKAS] Starting decision server...")
            decision_cmd = self._build_decision_cmd()
            self.decision_process = subprocess.Popen(
                decision_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr to stdout
                bufsize=0,  # Unbuffered
            )
            print(f"[LKAS] ✓ Decision server started (PID: {self.decision_process.pid})")

            # Give decision server time to initialize
            time.sleep(2.0)

            # Check if decision server is still running
            if self.decision_process.poll() is not None:
                print("[LKAS] ✗ Decision server failed to start!")
                self.stop()
                return 1

            print("\n" + "=" * 70)
            print("[LKAS] System running - Press Ctrl+C to stop")
            print("[LKAS]")
            print("[LKAS] Servers will wait up to 30 seconds for connections:")
            print("[LKAS]   - Detection server waiting for camera_feed from simulation")
            print("[LKAS]   - Decision server waiting for detection_results from detection")
            print("[LKAS]")
            print("[LKAS] Ready! Start 'simulation' in another terminal to begin processing")
            print("=" * 70 + "\n")

            self.running = True

            # Main loop - multiplex output from both processes
            while self.running:
                # Read output from both processes FIRST
                self._read_process_output(self.detection_process, "DETECTION")
                self._read_process_output(self.decision_process, "DECISION ")

                # Then check if processes are still alive
                detection_alive = self.detection_process.poll() is None
                decision_alive = self.decision_process.poll() is None

                if not detection_alive:
                    # Try to read remaining output
                    for _ in range(10):
                        self._read_process_output(self.detection_process, "DETECTION")
                    print("[LKAS] ✗ Detection server died unexpectedly!")
                    self.running = False
                    break

                if not decision_alive:
                    # Try to read remaining output before reporting death
                    print("[LKAS] Decision server process ended, reading final output...")
                    time.sleep(0.1)  # Give output a moment to flush
                    for _ in range(20):
                        self._read_process_output(self.decision_process, "DECISION ")
                    print("[LKAS] ✗ Decision server died unexpectedly!")
                    self.running = False
                    break

                # Small sleep to prevent busy-waiting
                time.sleep(0.01)

        except Exception as e:
            print(f"[LKAS] ✗ Error: {e}")
            return 1
        finally:
            if hasattr(self, 'log_file') and self.log_file:
                self.log_file.close()
            self.stop()

        return 0

    def stop(self):
        """Stop both servers gracefully."""
        self.running = False

        print("\n[LKAS] Stopping servers...")

        # Stop decision server first (consumer)
        if self.decision_process and self.decision_process.poll() is None:
            print("[LKAS] Stopping decision server...")
            self.decision_process.terminate()
            try:
                self.decision_process.wait(timeout=5.0)
                print("[LKAS] ✓ Decision server stopped")
            except subprocess.TimeoutExpired:
                print("[LKAS] ! Decision server not responding, killing...")
                self.decision_process.kill()
                self.decision_process.wait()

        # Then stop detection server (producer)
        if self.detection_process and self.detection_process.poll() is None:
            print("[LKAS] Stopping detection server...")
            self.detection_process.terminate()
            try:
                self.detection_process.wait(timeout=5.0)
                print("[LKAS] ✓ Detection server stopped")
            except subprocess.TimeoutExpired:
                print("[LKAS] ! Detection server not responding, killing...")
                self.detection_process.kill()
                self.detection_process.wait()

        print("[LKAS] ✓ Cleanup complete")


def main():
    """Main entry point for LKAS launcher."""
    parser = argparse.ArgumentParser(
        description="LKAS System Launcher - Starts both Detection and Decision servers"
    )

    parser.add_argument(
        "--method",
        type=str,
        default="cv",
        choices=["cv", "dl"],
        help="Lane detection method (cv=Computer Vision, dl=Deep Learning)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (default: <project-root>/config.yaml)",
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=None,
        help="GPU device ID (for DL method)",
    )

    # Shared memory options (advanced)
    parser.add_argument(
        "--image-shm-name",
        type=str,
        default="camera_feed",
        help="Shared memory name for camera images (default: camera_feed)",
    )
    parser.add_argument(
        "--detection-shm-name",
        type=str,
        default="detection_results",
        help="Shared memory name for detection results (default: detection_results)",
    )
    parser.add_argument(
        "--control-shm-name",
        type=str,
        default="control_commands",
        help="Shared memory name for control commands (default: control_commands)",
    )

    args = parser.parse_args()

    # Create and run launcher
    launcher = LKASLauncher(
        method=args.method,
        config=args.config,
        gpu=args.gpu,
        image_shm_name=args.image_shm_name,
        detection_shm_name=args.detection_shm_name,
        control_shm_name=args.control_shm_name,
    )

    return launcher.run()


if __name__ == "__main__":
    sys.exit(main())
