#!/usr/bin/env python3
"""
Scientific PDF Report Generator for NASA Space Apps: Earth Systems Trend Detective
Generates comprehensive PDF research dossiers with:
- Challenge & Project Header
- Investigation Scope (Variable, Region, Date Range, Observations)
- Statistical Scorecard (OLS, Mann-Kendall, Sen's Slope)
- Scientific Interpretation
- Provenance & Data Quality Caveats
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf(data, output_path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Space Theme Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0b1d3a')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4b5563')
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=10,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1f2937')
    )
    
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # Header Banner
    story.append(Paragraph("NASA SPACE APPS CHALLENGE 2026", subtitle_style))
    story.append(Paragraph("EARTH SYSTEMS TREND DETECTIVE — RESEARCH DOSSIER", title_style))
    story.append(Paragraph("Scientific Investigation of Decadal Atmospheric & Climatological Trajectories across India", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    # Investigation Metadata Table
    var_name = data.get("variable_name", data.get("variable", "Air Temperature at 2m"))
    reg_name = data.get("region_name", data.get("region", "All India"))
    unit = data.get("units", "°C")
    d_range = data.get("date_range", {})
    start_d = d_range.get("start", "2015-01")
    end_d = d_range.get("end", "2024-12")
    n_obs = d_range.get("n_months", 120)

    meta_table_data = [
        [
            Paragraph("<b>Target Variable:</b>", body_style), Paragraph(f"{var_name} ({unit})", body_style),
            Paragraph("<b>Geographic Scope:</b>", body_style), Paragraph(f"{reg_name}", body_style)
        ],
        [
            Paragraph("<b>Time Span:</b>", body_style), Paragraph(f"{start_d} to {end_d} ({n_obs} months)", body_style),
            Paragraph("<b>Generated:</b>", body_style), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M UTC"), body_style)
        ],
        [
            Paragraph("<b>Data Provider:</b>", body_style), Paragraph("NASA POWER (MERRA-2 Assimilation)", body_style),
            Paragraph("<b>Spatial Grid:</b>", body_style), Paragraph("2.0° Spherical Mesh (255 Nodes)", body_style)
        ]
    ]

    t_meta = Table(meta_table_data, colWidths=[100, 170, 110, 160])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    # Statistical Results Section
    story.append(Paragraph("1. STATISTICAL TREND DETECTION & RIGOROUS HYPOTHESIS TESTING", h2_style))
    ols = data.get("ols", {})
    mk = data.get("mann_kendall", {})
    sen = data.get("sen_slope", {})

    stat_rows = [
        ["Statistical Metric", "Calculated Value", "Statistical Significance & 95% Confidence Interval"],
        ["Ordinary Least Squares (OLS) Slope", f"{ols.get('slope_per_year', 0):+.4f} {unit}/yr", f"95% CI: [{ols.get('ci_lower_per_year', 0):+.4f}, {ols.get('ci_upper_per_year', 0):+.4f}] (p = {ols.get('p_value', 1.0):.4f})"],
        ["Decadal Projected Trajectory", f"{ols.get('slope_per_decade', 0):+.3f} {unit}/decade", f"Coefficient of Determination: R² = {ols.get('r_squared', 0):.4f}"],
        ["Mann-Kendall Rank S Statistic", f"S = {mk.get('S', 0)}, Z = {mk.get('Z', 0):.2f}", f"Two-tailed exact p-value = {mk.get('p_value', 1.0):.4f} (α = 0.05)"],
        ["Mann-Kendall Rank Correlation (τ)", f"τ = {mk.get('tau', 0):+.4f}", f"Verdict: {'Significant Trend' if mk.get('is_significant', False) else 'No Significant Trend'}"],
        ["Theil-Sen Robust Median Slope", f"{sen.get('slope_per_year', 0):+.4f} {unit}/yr", f"Robust 95% CI: [{sen.get('ci_lower_per_year', 0):+.4f}, {sen.get('ci_upper_per_year', 0):+.4f}] {unit}/yr"]
    ]

    t_stat = Table(stat_rows, colWidths=[180, 140, 220])
    t_stat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 10))

    # Plain Language Interpretation
    story.append(Paragraph("2. SCIENTIFIC INTERPRETATION & ENVIRONMENTAL CONTEXT", h2_style))
    interp = data.get("interpretation", {})
    summary_text = interp.get("summary", "No summary provided.")
    conf_text = interp.get("confidence_assessment", "")
    rec_text = interp.get("recommendation", "")

    interp_box = [
        [Paragraph(f"<b>Executive Finding:</b> {summary_text}", body_style)],
        [Paragraph(f"<b>Statistical Rigor:</b> {conf_text}", body_style)],
        [Paragraph(f"<b>Domain Caveat:</b> {rec_text}", callout_style)]
    ]
    t_interp = Table(interp_box, colWidths=[540])
    t_interp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3b82f6')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_interp)
    story.append(Spacer(1, 10))

    # Methodological Provenance & Space Apps Compliance
    story.append(Paragraph("3. METHODOLOGICAL COMPLIANCE WITH NASA CHALLENGE", h2_style))
    method_text = (
        "This dossier directly fulfills the four mandatory objectives of the NASA Space Apps 2026 Challenge "
        "<i>'Be An Earth System Trend Detective!'</i>: (1) Systematically identified Earth science variables "
        "(Air Temperature, Precipitation, Relative Humidity, Wind Speed, Atmospheric Methane); (2) Acquired data "
        "over verified 2-degree geographic partitions across India; (3) Generated and analyzed continuous 10-year monthly "
        "time series (2015-2024); (4) Quantified the rate of change using both parametric (OLS) and non-parametric (Sen's slope) "
        "estimators and formally tested statistical significance via the Mann-Kendall rank trend test at α = 0.05."
    )
    story.append(Paragraph(method_text, body_style))
    story.append(Spacer(1, 8))

    limitation_text = (
        "<b>Scientific Integrity Notice:</b> Methane observations from Sentinel-5P TROPOMI are pilot atmospheric "
        "soundings (226 node-months across 4 snapshots) and must not be conflated with direct surface emissions fluxes. "
        "Machine learning models are secondary research exploratory baselines exhibiting negative R² due to spatial sparsity "
        "and monsoon cloud contamination."
    )
    story.append(Paragraph(limitation_text, callout_style))
    story.append(Spacer(1, 12))

    # Footer note
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=6))
    story.append(Paragraph("NASA Space Apps Challenge 2026 | Earth Systems Trend Detective | Open Environmental Intelligence", subtitle_style))

    doc.build(story)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="PDF Report Generator")
    parser.add_argument("--input_json", type=str, required=True, help="Path to input analysis JSON file or raw JSON string")
    parser.add_argument("--output_pdf", type=str, required=True, help="Output PDF file path")

    args = parser.parse_args()

    # Load input data
    in_path = Path(args.input_json)
    if in_path.exists():
        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(args.input_json)

    out_file = Path(args.output_pdf)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    generate_pdf(data, out_file)
    print(json.dumps({"success": True, "output_pdf": str(out_file)}))


if __name__ == "__main__":
    main()
