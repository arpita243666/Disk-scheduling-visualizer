# Disk-scheduling-visualizer
# Disk Scheduling Algorithm Visualizer

A full-featured desktop application for simulating, visualizing, and comparing
disk scheduling algorithms with a modern dark-themed GUI.

---

## Features

- **6 algorithms**: FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
- **Animated visualization** of disk head movement (step-by-step)
- **Compare all** algorithms side-by-side with bar chart + efficiency chart
- **Overlay chart** showing all algorithms on one graph
- **Results table** with ranking, efficiency %, and best-algorithm highlight
- **Sequence detail** panel with per-algorithm seek breakdowns
- **Export**: CSV (full data) and PDF (styled report with charts)
- **Input validation** with clear error messages
- **Dark mode** UI throughout

---

## Project Structure

```
disk_scheduler/
├── main.py            # Entry point — run this file
├── algorithms.py      # All 6 scheduling algorithm implementations
├── ui.py              # PyQt5 GUI (windows, panels, tabs, buttons)
├── visualization.py   # matplotlib chart generation
├── export.py          # CSV and PDF export logic
├── requirements.txt   # Python dependencies
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install PyQt5 matplotlib reportlab
```

### 2. Run the app

```bash
python main.py
```

Or in VS Code: open `main.py` and press **F5** (or right-click → Run Python File).

---

## Usage

| Field | Description |
|-------|-------------|
| Disk Size | Total number of cylinders (default: 200) |
| Initial Head | Starting position of read/write head (default: 53) |
| Request Queue | Comma-separated cylinder numbers (default: 98,183,37,122,14,124,65,67) |
| Direction | For SCAN/C-SCAN/LOOK/C-LOOK: left or right sweep |

### Buttons

| Button | Action |
|--------|--------|
| ▶ Run Simulation | Run selected algorithm and display seek chart |
| ⚡ Animate | Animate head movement step-by-step |
| 📊 Compare All | Run all 6 algorithms and show comparison charts |
| ↺ Reset | Clear all inputs and charts |
| ⬇ Export CSV | Save results to a CSV file |
| 📄 Export PDF | Save styled PDF report with charts |

---

## Algorithm Descriptions

| Algorithm | Description |
|-----------|-------------|
| **FCFS** | Services requests in arrival order. Simple but inefficient. |
| **SSTF** | Always picks the nearest cylinder. Minimizes seek but may cause starvation. |
| **SCAN** | Sweeps in one direction, then reverses (elevator). Balanced. |
| **C-SCAN** | Like SCAN but wraps to start instead of reversing. More uniform wait. |
| **LOOK** | Like SCAN but only goes as far as the last request (not disk boundary). |
| **C-LOOK** | Like C-SCAN but wraps to the smallest request. Most efficient SCAN variant. |

---

## Example Input

```
Disk Size:     200
Head Position: 53
Request Queue: 98, 183, 37, 122, 14, 124, 65, 67
Direction:     Right
```

Expected total seek distances (approximate):
- FCFS: 640 cylinders
- SSTF: 236 cylinders
- SCAN: 208 cylinders
- C-SCAN: 382 cylinders
- LOOK: 208 cylinders
- C-LOOK: 226 cylinders

---

## Dependencies

- **Python** 3.9+
- **PyQt5** — GUI framework
- **matplotlib** — chart generation
- **reportlab** — PDF export (optional but recommended)
