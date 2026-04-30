"""
main.py
Entry point for the Disk Scheduling Algorithm Visualizer
────────────────────────────────────────────────────────
Run with:
    python main.py

Requirements:
    pip install PyQt5 matplotlib reportlab
"""

import sys
import os

# Ensure the project directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Verify all required packages are installed before launching."""
    missing = []

    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5")

    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")

    if missing:
        print("=" * 55)
        print("  Missing required packages:")
        for pkg in missing:
            print(f"    • {pkg}")
        print()
        print("  Install them with:")
        print(f"    pip install {' '.join(missing)}")
        print()
        print("  Optional (for PDF export):")
        print("    pip install reportlab")
        print("=" * 55)
        sys.exit(1)


if __name__ == "__main__":
    check_dependencies()
    from ui import launch
    launch()
