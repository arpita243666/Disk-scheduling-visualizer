"""
export.py
Export Module — saves results as CSV and PDF
Dependencies: csv (stdlib), reportlab (pip install reportlab)
"""

import csv
import os
from datetime import datetime


# ── CSV Export ─────────────────────────────────────────────────────────────────

def export_csv(results: dict, requests: list[int], head: int,
               disk_size: int, direction: str, filepath: str) -> None:
    """
    Export simulation results to a CSV file.
    Each algorithm occupies a block of rows.
    """
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header metadata
        writer.writerow(["Disk Scheduling Simulator — Results"])
        writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        writer.writerow(["--- Input Parameters ---"])
        writer.writerow(["Disk Size", disk_size])
        writer.writerow(["Initial Head", head])
        writer.writerow(["Direction", direction])
        writer.writerow(["Request Queue", ", ".join(map(str, requests))])
        writer.writerow([])

        # Summary table
        writer.writerow(["--- Summary ---"])
        writer.writerow(["Algorithm", "Total Seek", "Avg Seek / Request", "Efficiency (%)"])

        totals = [v["total"] for v in results.values()]
        min_seek = min(totals) if totals else 1

        for name, data in results.items():
            eff = round((min_seek / data["total"]) * 100, 1) if data["total"] else 100
            writer.writerow([name, data["total"], data["avg"], eff])

        writer.writerow([])

        # Seek sequences
        writer.writerow(["--- Seek Sequences ---"])
        for name, data in results.items():
            writer.writerow([f"{name} Sequence"])
            writer.writerow(["Step"] + list(range(len(data["sequence"]))))
            writer.writerow(["Cylinder"] + data["sequence"])
            moves = [abs(data["sequence"][i] - data["sequence"][i - 1])
                     for i in range(1, len(data["sequence"]))]
            writer.writerow(["Move"] + ["—"] + moves)
            writer.writerow([])


# ── PDF Export ─────────────────────────────────────────────────────────────────

def export_pdf(results: dict, requests: list[int], head: int,
               disk_size: int, direction: str,
               chart_image_paths: list[str], filepath: str) -> None:
    """
    Export a styled PDF report with:
    - Input parameters
    - Results table
    - Embedded chart images
    Requires: pip install reportlab
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, Image, HRFlowable,
                                        PageBreak)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise ImportError(
            "reportlab is required for PDF export.\n"
            "Install it with:  pip install reportlab"
        )

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ──
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#34495e"),
        spaceBefore=14,
        spaceAfter=6,
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=4,
    )

    story.append(Paragraph("Disk Scheduling Algorithm Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#bdc3c7"), spaceAfter=14))

    # ── Input Parameters ──
    story.append(Paragraph("Input Parameters", section_style))
    params = [
        ["Parameter", "Value"],
        ["Disk Size", str(disk_size)],
        ["Initial Head Position", str(head)],
        ["Head Direction", direction.capitalize()],
        ["Request Queue", ", ".join(map(str, requests))],
        ["Total Requests", str(len(requests))],
    ]
    param_table = Table(params, colWidths=[6 * cm, 11 * cm])
    param_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#ecf0f1"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(param_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Results Summary ──
    story.append(Paragraph("Performance Summary", section_style))

    totals = [v["total"] for v in results.values()]
    min_seek = min(totals) if totals else 1
    best_algo = min(results, key=lambda k: results[k]["total"])

    summary_data = [["Algorithm", "Total Seek", "Avg / Request", "Efficiency %", "Rank"]]
    sorted_results = sorted(results.items(), key=lambda x: x[1]["total"])
    for rank, (name, data) in enumerate(sorted_results, 1):
        eff = round((min_seek / data["total"]) * 100, 1) if data["total"] else 100
        marker = "★ Best" if name == best_algo else ""
        summary_data.append([
            f"{name} {marker}",
            str(data["total"]),
            str(data["avg"]),
            f"{eff}%",
            str(rank),
        ])

    summary_table = Table(summary_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 2*cm])
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [colors.HexColor("#ecf0f1"), colors.white]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
    ]
    # Highlight best row (row 1 after sort)
    style_cmds.append(("BACKGROUND", (0, 1), (-1, 1),
                        colors.HexColor("#ffeaa7")))
    summary_table.setStyle(TableStyle(style_cmds))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Seek Sequences ──
    story.append(Paragraph("Seek Sequences", section_style))
    for name, data in results.items():
        seq_str = " → ".join(map(str, data["sequence"]))
        story.append(Paragraph(
            f"<b>{name}:</b>  {seq_str}",
            body_style
        ))

    # ── Charts ──
    if chart_image_paths:
        story.append(PageBreak())
        story.append(Paragraph("Visualization Charts", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                 color=colors.HexColor("#bdc3c7"),
                                 spaceAfter=10))
        for img_path in chart_image_paths:
            if os.path.exists(img_path):
                img = Image(img_path, width=17 * cm, height=9 * cm)
                story.append(img)
                story.append(Spacer(1, 0.5 * cm))

    doc.build(story)


# ── Quick standalone test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "FCFS":   {"sequence": [53, 98, 183, 37, 122, 14, 124, 65, 67], "total": 640, "avg": 80.0},
        "SSTF":   {"sequence": [53, 65, 67, 37, 14, 98, 122, 124, 183], "total": 236, "avg": 29.5},
    }
    export_csv(sample, [98, 183, 37, 122, 14, 124, 65, 67], 53, 200,
               "right", "/tmp/test_export.csv")
    print("CSV exported to /tmp/test_export.csv")
