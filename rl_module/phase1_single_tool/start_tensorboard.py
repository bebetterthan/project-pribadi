"""
START TENSORBOARD MONITORING
============================

Automatically launches TensorBoard for Phase 1 training monitoring.

FEATURES:
- Real-time training metrics
- Episode rewards and lengths
- Custom metrics (discovery rate, efficiency)
- Loss curves
- Learning rate schedule

USAGE:
    python start_tensorboard.py
    
    Then open: http://localhost:6006
"""

import subprocess
import sys
from pathlib import Path
import time
import webbrowser


def find_latest_run():
    """Find the latest training run directory"""
    outputs_dir = Path(__file__).parent / "outputs"
    
    if not outputs_dir.exists():
        return None
    
    runs = sorted(outputs_dir.glob("run_*"), reverse=True)
    if runs:
        return runs[0] / "tensorboard"
    
    return None


def main():
    print("="*60)
    print("📊 TENSORBOARD MONITORING - PHASE 1")
    print("="*60)
    
    # Check if training is running or has run
    outputs_dir = Path(__file__).parent / "outputs"
    
    if not outputs_dir.exists():
        print("\n⚠️ No training runs found yet.")
        print("   Start training first with: python train_local.py")
        return
    
    # Find log directory
    latest_run = find_latest_run()
    
    if latest_run and latest_run.exists():
        logdir = latest_run
        print(f"\n📁 Latest run: {latest_run.parent.name}")
    else:
        # Use outputs directory to show all runs
        logdir = outputs_dir
        print(f"\n📁 Monitoring all runs in: {outputs_dir}")
    
    print(f"📊 TensorBoard log directory: {logdir}")
    print(f"🌐 Opening browser at: http://localhost:6006")
    print("\n💡 Press Ctrl+C to stop TensorBoard\n")
    
    # Give user time to read
    time.sleep(2)
    
    # Open browser
    try:
        webbrowser.open("http://localhost:6006")
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")
        print("   Manually open: http://localhost:6006")
    
    # Start TensorBoard
    try:
        subprocess.run([
            sys.executable, "-m", "tensorboard.main",
            "--logdir", str(logdir),
            "--port", "6006",
            "--reload_interval", "5"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ TensorBoard stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nManual command:")
        print(f"tensorboard --logdir={logdir} --port=6006")


if __name__ == "__main__":
    main()
