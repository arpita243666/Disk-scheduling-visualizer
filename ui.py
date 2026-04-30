"""
ui.py
Main GUI Module — PyQt5 Dark-themed Disk Scheduling Visualizer
Requires: PyQt5, matplotlib
"""

import sys
import os
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QTabWidget, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QSplitter, QGroupBox, QRadioButton,
    QButtonGroup, QTextEdit, QScrollArea, QProgressBar, QSlider,
    QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, QSize
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QIntValidator
)

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from algorithms import fcfs, sstf, scan, cscan, look, clook, run_all
from visualization import (
    plot_seek, plot_comparison, plot_efficiency,
    plot_all_on_one, save_figure, ALGO_COLORS
)
from export import export_csv, export_pdf


# ─────────────────────────── Color constants ──────────────────────────────────
C_BG        = "#1e1e2e"
C_PANEL     = "#2a2a3e"
C_CARD      = "#313150"
C_BORDER    = "#44446a"
C_TEXT      = "#e0e0ef"
C_MUTED     = "#9090b0"
C_ACCENT    = "#7c7cff"
C_SUCCESS   = "#1D9E75"
C_WARNING   = "#E67E22"
C_DANGER    = "#D85A30"
C_GOLD      = "#FFD700"

ALGO_LIST = ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"]


# ─────────────────────────── Helper widgets ───────────────────────────────────

def styled_label(text: str, size: int = 11, bold: bool = False,
                 color: str = C_TEXT) -> QLabel:
    lbl = QLabel(text)
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    return lbl


def styled_input(placeholder: str = "", width: int = 200) -> QLineEdit:
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    inp.setFixedHeight(36)
    inp.setMinimumWidth(width)
    inp.setStyleSheet(f"""
        QLineEdit {{
            background: {C_BG};
            color: {C_TEXT};
            border: 1px solid {C_BORDER};
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1.5px solid {C_ACCENT};
        }}
    """)
    return inp


def styled_button(text: str, color: str = C_ACCENT,
                  height: int = 38) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(height)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: #ffffff;
            border: none;
            border-radius: 7px;
            padding: 0 18px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {color}cc;
        }}
        QPushButton:pressed {{
            background: {color}88;
        }}
        QPushButton:disabled {{
            background: {C_BORDER};
            color: {C_MUTED};
        }}
    """)
    return btn


def card_frame(title: str = "") -> QGroupBox:
    box = QGroupBox(title)
    box.setStyleSheet(f"""
        QGroupBox {{
            background: {C_CARD};
            border: 1px solid {C_BORDER};
            border-radius: 10px;
            margin-top: 14px;
            font-size: 12px;
            font-weight: bold;
            color: {C_MUTED};
            padding: 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            left: 14px;
        }}
    """)
    return box


# ─────────────────────────── Matplotlib Canvas ────────────────────────────────

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=4.5):
        self.fig = Figure(figsize=(width, height), dpi=96)
        self.fig.patch.set_facecolor("#1e1e2e")
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def clear(self):
        self.fig.clear()
        self.draw()


# ─────────────────────────── Animation Worker ─────────────────────────────────

class AnimationWorker(QThread):
    """Emits one step at a time for animated seek visualization."""
    step_signal = pyqtSignal(list, int)   # partial_sequence, step_index
    done_signal = pyqtSignal()

    def __init__(self, sequence: list, delay_ms: int = 350):
        super().__init__()
        self.sequence = sequence
        self.delay_ms = delay_ms
        self._stop = False

    def run(self):
        import time
        for i in range(1, len(self.sequence) + 1):
            if self._stop:
                break
            self.step_signal.emit(self.sequence[:i], i - 1)
            time.sleep(self.delay_ms / 1000)
        self.done_signal.emit()

    def stop(self):
        self._stop = True


# ─────────────────────────── Main Window ──────────────────────────────────────

class DiskSchedulerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disk Scheduling Algorithm Visualizer")
        self.setMinimumSize(1200, 780)
        self.resize(1400, 860)

        self._results = {}
        self._current_algo = "FCFS"
        self._anim_worker = None

        self._apply_dark_palette()
        self._build_ui()
        self._connect_signals()

    # ── Dark palette ──────────────────────────────────────────────────────────
    def _apply_dark_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor(C_BG))
        palette.setColor(QPalette.WindowText,      QColor(C_TEXT))
        palette.setColor(QPalette.Base,            QColor(C_PANEL))
        palette.setColor(QPalette.AlternateBase,   QColor(C_CARD))
        palette.setColor(QPalette.Text,            QColor(C_TEXT))
        palette.setColor(QPalette.Button,          QColor(C_PANEL))
        palette.setColor(QPalette.ButtonText,      QColor(C_TEXT))
        palette.setColor(QPalette.Highlight,       QColor(C_ACCENT))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        self.setPalette(palette)
        self.setStyleSheet(f"""
            QMainWindow {{ background: {C_BG}; }}
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: {C_PANEL}; border-radius: 6px; }}
            QTabBar::tab {{
                background: {C_CARD}; color: {C_MUTED};
                padding: 9px 18px; border-radius: 6px 6px 0 0;
                margin-right: 3px; font-size: 12px;
            }}
            QTabBar::tab:selected {{ background: {C_ACCENT}; color: #fff; font-weight: bold; }}
            QTabBar::tab:hover {{ background: {C_BORDER}; color: {C_TEXT}; }}
            QScrollBar:vertical {{ background: {C_PANEL}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {C_BORDER}; border-radius: 4px; }}
            QComboBox {{
                background: {C_BG}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; border-radius: 6px;
                padding: 4px 10px; font-size: 13px; min-height: 30px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {C_PANEL}; color: {C_TEXT};
                border: 1px solid {C_BORDER};
                selection-background-color: {C_ACCENT};
            }}
            QTableWidget {{
                background: {C_CARD}; color: {C_TEXT};
                gridline-color: {C_BORDER}; border: none;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {C_PANEL}; color: {C_MUTED};
                padding: 7px; border: none;
                font-size: 11px; font-weight: bold;
            }}
            QTableWidget::item:selected {{ background: {C_ACCENT}44; }}
            QRadioButton {{ color: {C_TEXT}; font-size: 12px; }}
            QRadioButton::indicator {{ width: 14px; height: 14px; }}
            QCheckBox {{ color: {C_TEXT}; font-size: 12px; }}
            QSlider::groove:horizontal {{
                height: 5px; background: {C_BORDER}; border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {C_ACCENT}; width: 16px; height: 16px;
                margin: -6px 0; border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{ background: {C_ACCENT}; border-radius: 3px; }}
            QProgressBar {{
                background: {C_BORDER}; border-radius: 4px; height: 8px;
            }}
            QProgressBar::chunk {{ background: {C_ACCENT}; border-radius: 4px; }}
        """)

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        root_layout.addWidget(self._make_header())

        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {C_BORDER}; }}")

        splitter.addWidget(self._make_left_panel())
        splitter.addWidget(self._make_right_panel())
        splitter.setSizes([340, 960])

        root_layout.addWidget(splitter, 1)
        root_layout.addWidget(self._make_status_bar())

    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {C_CARD}, stop:1 {C_PANEL});
            border-bottom: 1px solid {C_BORDER};
        """)
        layout = QHBoxLayout(hdr)
        layout.setContentsMargins(20, 0, 20, 0)

        icon_lbl = QLabel("💿")
        icon_lbl.setFont(QFont("Segoe UI", 22))
        layout.addWidget(icon_lbl)

        title = QLabel("Disk Scheduling Visualizer")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {C_TEXT}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("FCFS · SSTF · SCAN · C-SCAN · LOOK · C-LOOK")
        subtitle.setStyleSheet(f"color: {C_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(subtitle)

        layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return hdr

    def _make_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(360)
        panel.setStyleSheet(f"background: {C_PANEL};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # ── Input card ──
        input_card = card_frame("⚙  Input Parameters")
        input_layout = QVBoxLayout(input_card)
        input_layout.setSpacing(10)

        # Disk size
        input_layout.addWidget(styled_label("Disk Size (cylinders)"))
        self.disk_size_input = styled_input("e.g. 200", 280)
        self.disk_size_input.setText("200")
        input_layout.addWidget(self.disk_size_input)

        # Head position
        input_layout.addWidget(styled_label("Initial Head Position"))
        self.head_input = styled_input("e.g. 53", 280)
        self.head_input.setText("53")
        input_layout.addWidget(self.head_input)

        # Request queue
        input_layout.addWidget(styled_label("Request Queue (comma-separated)"))
        self.queue_input = styled_input("e.g. 98,183,37,122,14,124,65,67", 280)
        self.queue_input.setText("98,183,37,122,14,124,65,67")
        input_layout.addWidget(self.queue_input)

        # Direction
        input_layout.addWidget(styled_label("Head Direction (SCAN/C-SCAN/LOOK/C-LOOK)"))
        dir_row = QHBoxLayout()
        self.dir_right = QRadioButton("Right  →")
        self.dir_left  = QRadioButton("Left  ←")
        self.dir_right.setChecked(True)
        dir_group = QButtonGroup(self)
        dir_group.addButton(self.dir_right)
        dir_group.addButton(self.dir_left)
        dir_row.addWidget(self.dir_right)
        dir_row.addWidget(self.dir_left)
        dir_row.addStretch()
        input_layout.addLayout(dir_row)

        layout.addWidget(input_card)

        # ── Algorithm card ──
        algo_card = card_frame("🧮  Algorithm")
        algo_layout = QVBoxLayout(algo_card)
        algo_layout.setSpacing(10)

        algo_layout.addWidget(styled_label("Select Algorithm"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(ALGO_LIST)
        self.algo_combo.setFixedHeight(36)
        algo_layout.addWidget(self.algo_combo)

        # Animation speed
        algo_layout.addWidget(styled_label("Animation Speed"))
        speed_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(100, 1200)
        self.speed_slider.setValue(400)
        self.speed_slider.setInvertedAppearance(True)
        self.speed_label = styled_label("400 ms/step", 10, color=C_MUTED)
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_label)
        algo_layout.addLayout(speed_row)

        layout.addWidget(algo_card)

        # ── Action buttons ──
        btn_card = card_frame("▶  Actions")
        btn_layout = QVBoxLayout(btn_card)
        btn_layout.setSpacing(8)

        self.btn_run = styled_button("▶  Run Simulation", C_ACCENT)
        self.btn_animate = styled_button("⚡  Animate", C_SUCCESS)
        self.btn_compare = styled_button("📊  Compare All", C_WARNING)
        self.btn_reset   = styled_button("↺  Reset", C_BORDER)
        self.btn_export_csv = styled_button("⬇  Export CSV", "#555575")
        self.btn_export_pdf = styled_button("📄  Export PDF", "#555575")

        for btn in [self.btn_run, self.btn_animate, self.btn_compare,
                    self.btn_reset, self.btn_export_csv, self.btn_export_pdf]:
            btn_layout.addWidget(btn)

        layout.addWidget(btn_card)
        layout.addStretch()

        return panel

    def _make_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {C_BG};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 14, 10)
        layout.setSpacing(8)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1 — Seek chart
        self.tab_chart = QWidget()
        tab1_layout = QVBoxLayout(self.tab_chart)
        self.plot_canvas = PlotCanvas(height=4.8)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self.tab_chart)
        self.plot_toolbar.setStyleSheet(
            f"background: {C_PANEL}; color: {C_TEXT}; border: none;"
        )
        tab1_layout.addWidget(self.plot_toolbar)
        tab1_layout.addWidget(self.plot_canvas, 1)

        # Result info strip
        info_strip = QHBoxLayout()
        self.lbl_seq    = styled_label("Sequence: —", 10, color=C_MUTED)
        self.lbl_total  = styled_label("Total Seek: —", 11, bold=True, color=C_GOLD)
        self.lbl_avg    = styled_label("Avg: —", 10, color=C_MUTED)
        self.lbl_seq.setWordWrap(True)
        info_strip.addWidget(self.lbl_seq, 3)
        info_strip.addWidget(self.lbl_total)
        info_strip.addWidget(self.lbl_avg)
        tab1_layout.addLayout(info_strip)
        self.tabs.addTab(self.tab_chart, "📈  Seek Chart")

        # Tab 2 — Comparison
        self.tab_compare = QWidget()
        cmp_layout = QVBoxLayout(self.tab_compare)

        self.cmp_canvas = PlotCanvas(height=4.5)
        self.eff_canvas = PlotCanvas(height=3.5)
        cmp_layout.addWidget(self.cmp_canvas, 3)
        cmp_layout.addWidget(self.eff_canvas, 2)
        self.tabs.addTab(self.tab_compare, "📊  Comparison")

        # Tab 3 — Table
        self.tab_table = QWidget()
        tbl_layout = QVBoxLayout(self.tab_table)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([
            "Algorithm", "Total Seek", "Avg / Request",
            "Efficiency %", "Rank", "Status"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        tbl_layout.addWidget(self.result_table)
        self.tabs.addTab(self.tab_table, "📋  Results Table")

        # Tab 4 — Overlay
        self.tab_overlay = QWidget()
        ov_layout = QVBoxLayout(self.tab_overlay)
        self.overlay_canvas = PlotCanvas(height=5)
        ov_layout.addWidget(self.overlay_canvas)
        self.tabs.addTab(self.tab_overlay, "🔀  All Algorithms")

        # Tab 5 — Sequence detail
        self.tab_detail = QWidget()
        det_layout = QVBoxLayout(self.tab_detail)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet(f"""
            QTextEdit {{
                background: {C_CARD}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; border-radius: 6px;
                font-family: 'Consolas', monospace; font-size: 12px;
                padding: 10px;
            }}
        """)
        det_layout.addWidget(self.detail_text)
        self.tabs.addTab(self.tab_detail, "🔍  Sequence Detail")

        return panel

    def _make_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet(f"background: {C_CARD}; border-top: 1px solid {C_BORDER};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        self.status_label = QLabel("Ready — Enter parameters and click Run Simulation")
        self.status_label.setStyleSheet(f"color: {C_MUTED}; font-size: 11px; background: transparent;")
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.status_right = QLabel("v1.0")
        self.status_right.setStyleSheet(f"color: {C_BORDER}; font-size: 10px; background: transparent;")
        layout.addWidget(self.status_right)
        return bar

    # ── Signal connections ─────────────────────────────────────────────────────
    def _connect_signals(self):
        self.btn_run.clicked.connect(self._run_simulation)
        self.btn_animate.clicked.connect(self._run_animation)
        self.btn_compare.clicked.connect(self._run_compare)
        self.btn_reset.clicked.connect(self._reset)
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        self.algo_combo.currentTextChanged.connect(self._on_algo_changed)
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v} ms/step"))

    # ── Input validation ───────────────────────────────────────────────────────
    def _parse_inputs(self) -> tuple | None:
        try:
            disk_size = int(self.disk_size_input.text().strip())
            if disk_size < 10 or disk_size > 10000:
                raise ValueError("Disk size must be between 10 and 10000.")
        except ValueError as e:
            self._error(f"Invalid disk size: {e}")
            return None

        try:
            head = int(self.head_input.text().strip())
            if not (0 <= head < disk_size):
                raise ValueError(f"Head must be between 0 and {disk_size - 1}.")
        except ValueError as e:
            self._error(f"Invalid head position: {e}")
            return None

        try:
            raw = self.queue_input.text().strip()
            queue = [int(x.strip()) for x in raw.split(",") if x.strip()]
            if not queue:
                raise ValueError("Queue cannot be empty.")
            for val in queue:
                if not (0 <= val < disk_size):
                    raise ValueError(f"Track {val} is outside [0, {disk_size - 1}].")
        except ValueError as e:
            self._error(f"Invalid request queue: {e}")
            return None

        direction = "right" if self.dir_right.isChecked() else "left"
        return queue, head, disk_size, direction

    def _error(self, msg: str):
        QMessageBox.critical(self, "Input Error", msg)

    def _set_status(self, msg: str, color: str = C_MUTED):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent;")

    # ── Run single simulation ──────────────────────────────────────────────────
    def _run_simulation(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        queue, head, disk_size, direction = parsed
        algo = self.algo_combo.currentText()
        self._current_algo = algo

        seq, total = self._compute(algo, queue, head, disk_size, direction)
        n = len(queue)
        avg = round(total / n, 2)

        # Update info strip
        seq_str = " → ".join(map(str, seq))
        self.lbl_seq.setText(f"Sequence: {seq_str}")
        self.lbl_total.setText(f"Total Seek: {total}")
        self.lbl_avg.setText(f"Avg: {avg}/req")

        # Draw chart
        plot_seek(seq, algo, total, disk_size, embed_fig=self.plot_canvas.fig)
        self.plot_canvas.draw()
        self.tabs.setCurrentIndex(0)
        self._set_status(f"{algo} — Total seek: {total} cylinders  |  Avg: {avg}", C_SUCCESS)

    def _compute(self, algo, queue, head, disk_size, direction):
        fns = {
            "FCFS":   lambda: fcfs(queue, head, disk_size),
            "SSTF":   lambda: sstf(queue, head, disk_size),
            "SCAN":   lambda: scan(queue, head, disk_size, direction),
            "C-SCAN": lambda: cscan(queue, head, disk_size, direction),
            "LOOK":   lambda: look(queue, head, disk_size, direction),
            "C-LOOK": lambda: clook(queue, head, disk_size, direction),
        }
        return fns[algo]()

    # ── Animation ─────────────────────────────────────────────────────────────
    def _run_animation(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        queue, head, disk_size, direction = parsed
        algo = self.algo_combo.currentText()
        seq, total = self._compute(algo, queue, head, disk_size, direction)

        if self._anim_worker and self._anim_worker.isRunning():
            self._anim_worker.stop()
            self._anim_worker.wait()

        delay = self.speed_slider.value()
        self._anim_worker = AnimationWorker(seq, delay)
        self._anim_worker.step_signal.connect(
            lambda partial_seq, idx: self._anim_step(partial_seq, algo, total, disk_size))
        self._anim_worker.done_signal.connect(
            lambda: self._set_status(f"Animation complete — {algo}: {total} cylinders", C_SUCCESS))
        self._anim_worker.start()
        self.tabs.setCurrentIndex(0)
        self._set_status(f"Animating {algo}…", C_ACCENT)

    def _anim_step(self, partial_seq, algo, total, disk_size):
        fig = self.plot_canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        from visualization import _apply_dark_style, ALGO_COLORS
        color = ALGO_COLORS.get(algo, "#7c7cff")
        steps = list(range(len(partial_seq)))
        ax.plot(steps, partial_seq, color=color, linewidth=2.2,
                marker="o", markersize=6, markerfacecolor="white",
                markeredgecolor=color, markeredgewidth=1.8)
        ax.set_xlim(-0.5, max(10, len(partial_seq) + 0.5))
        ax.set_ylim(-5, disk_size + 5)
        ax.set_xlabel("Step", fontsize=10)
        ax.set_ylabel("Cylinder", fontsize=10)
        ax.set_title(f"{algo}  (animating…  step {len(partial_seq)-1})",
                     fontsize=12, fontweight="bold")
        _apply_dark_style(ax, fig)
        fig.tight_layout()
        self.plot_canvas.draw()

    # ── Compare all ───────────────────────────────────────────────────────────
    def _run_compare(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        queue, head, disk_size, direction = parsed

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self._results = run_all(queue, head, disk_size, direction)
        self.progress_bar.setValue(50)

        # Comparison bar chart
        plot_comparison(self._results, embed_fig=self.cmp_canvas.fig)
        self.cmp_canvas.draw()
        self.progress_bar.setValue(70)

        # Efficiency chart
        plot_efficiency(self._results, embed_fig=self.eff_canvas.fig)
        self.eff_canvas.draw()
        self.progress_bar.setValue(85)

        # Overlay chart
        plot_all_on_one(self._results, disk_size, embed_fig=self.overlay_canvas.fig)
        self.overlay_canvas.draw()

        # Fill table
        self._fill_table(queue)

        # Fill detail text
        self._fill_detail()

        self.progress_bar.setValue(100)
        QTimer.singleShot(1200, lambda: self.progress_bar.setVisible(False))

        best = min(self._results, key=lambda k: self._results[k]["total"])
        self.tabs.setCurrentIndex(1)
        self._set_status(f"Comparison done — Best: {best} ({self._results[best]['total']} cylinders)", C_GOLD)

    def _fill_table(self, queue):
        self.result_table.setRowCount(0)
        totals = [v["total"] for v in self._results.values()]
        min_seek = min(totals)
        sorted_res = sorted(self._results.items(), key=lambda x: x[1]["total"])

        for rank, (name, data) in enumerate(sorted_res, 1):
            eff = round((min_seek / data["total"]) * 100, 1) if data["total"] else 100
            status = "★ Best" if rank == 1 else ("Good" if eff >= 80 else "Fair")
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            items = [name, str(data["total"]), str(data["avg"]),
                     f"{eff}%", str(rank), status]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if rank == 1:
                    item.setForeground(QColor(C_GOLD))
                    item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                else:
                    item.setForeground(QColor(C_TEXT))
                self.result_table.setItem(row, col, item)

    def _fill_detail(self):
        lines = []
        totals = [v["total"] for v in self._results.values()]
        min_seek = min(totals)
        for name, data in sorted(self._results.items(), key=lambda x: x[1]["total"]):
            eff = round((min_seek / data["total"]) * 100, 1)
            lines.append(f"{'─'*56}")
            lines.append(f"  {name:8s}  |  Total: {data['total']:5d}  |  Avg: {data['avg']:6.2f}  |  Eff: {eff}%")
            lines.append(f"{'─'*56}")
            seq_str = " → ".join(map(str, data["sequence"]))
            # Wrap at ~80 chars
            while len(seq_str) > 80:
                idx = seq_str.rfind(" ", 0, 80)
                lines.append("  " + seq_str[:idx])
                seq_str = "  " + seq_str[idx+1:]
            lines.append("  " + seq_str)
            lines.append("")
        self.detail_text.setPlainText("\n".join(lines))

    # ── Reset ─────────────────────────────────────────────────────────────────
    def _reset(self):
        if self._anim_worker and self._anim_worker.isRunning():
            self._anim_worker.stop()
        self.disk_size_input.setText("200")
        self.head_input.setText("53")
        self.queue_input.setText("98,183,37,122,14,124,65,67")
        self.dir_right.setChecked(True)
        self.algo_combo.setCurrentIndex(0)
        self.plot_canvas.clear()
        self.cmp_canvas.clear()
        self.eff_canvas.clear()
        self.overlay_canvas.clear()
        self.result_table.setRowCount(0)
        self.detail_text.clear()
        self.lbl_seq.setText("Sequence: —")
        self.lbl_total.setText("Total Seek: —")
        self.lbl_avg.setText("Avg: —")
        self._results = {}
        self._set_status("Reset — Enter parameters and click Run Simulation")

    # ── Algo combo change ──────────────────────────────────────────────────────
    def _on_algo_changed(self, algo: str):
        self._current_algo = algo
        needs_dir = algo in ("SCAN", "C-SCAN", "LOOK", "C-LOOK")
        self.dir_right.setEnabled(needs_dir)
        self.dir_left.setEnabled(needs_dir)

    # ── Export CSV ────────────────────────────────────────────────────────────
    def _export_csv(self):
        if not self._results:
            QMessageBox.warning(self, "No Data", "Run Compare All first to generate results.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "disk_results.csv", "CSV Files (*.csv)")
        if not path:
            return
        parsed = self._parse_inputs()
        if not parsed:
            return
        queue, head, disk_size, direction = parsed
        try:
            export_csv(self._results, queue, head, disk_size, direction, path)
            QMessageBox.information(self, "Exported", f"CSV saved to:\n{path}")
            self._set_status(f"CSV exported → {path}", C_SUCCESS)
        except Exception as e:
            self._error(str(e))

    # ── Export PDF ────────────────────────────────────────────────────────────
    def _export_pdf(self):
        if not self._results:
            QMessageBox.warning(self, "No Data", "Run Compare All first to generate results.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "disk_report.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        parsed = self._parse_inputs()
        if not parsed:
            return
        queue, head, disk_size, direction = parsed

        # Save chart images to temp files
        tmp_dir = tempfile.mkdtemp()
        chart_paths = []
        try:
            for name, data in self._results.items():
                fig = Figure(figsize=(9, 4.5), dpi=100)
                plot_seek(data["sequence"], name, data["total"], disk_size, embed_fig=fig)
                img_path = os.path.join(tmp_dir, f"{name}.png")
                save_figure(fig, img_path)
                chart_paths.append(img_path)

            fig2 = Figure(figsize=(9, 4.5), dpi=100)
            plot_comparison(self._results, embed_fig=fig2)
            cmp_path = os.path.join(tmp_dir, "comparison.png")
            save_figure(fig2, cmp_path)
            chart_paths.append(cmp_path)

            export_pdf(self._results, queue, head, disk_size, direction,
                       chart_paths, path)
            QMessageBox.information(self, "Exported", f"PDF saved to:\n{path}")
            self._set_status(f"PDF exported → {path}", C_SUCCESS)
        except Exception as e:
            self._error(str(e))
        finally:
            for p in chart_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass


# ─────────────────────────── Entry point ──────────────────────────────────────

def launch():
    app = QApplication(sys.argv)
    app.setApplicationName("Disk Scheduling Visualizer")
    app.setStyle("Fusion")
    window = DiskSchedulerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch()
