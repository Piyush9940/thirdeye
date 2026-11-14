"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Report Service: Automated PDF Investigation Dossier Generator (ReportLab)
"""

import io
from datetime import datetime
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ReportService:
    @staticmethod
    def generate_trend_pdf(data: Dict[str, Any]) -> bytes:
        """
        Generates a PDF research dossier from statistical trend analysis results.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40, leftMargin=40,
            topMargin=40, bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0b3d91'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=15
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#334155')
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("NASA Space Apps Challenge 2026", subtitle_style))
        elements.append(Paragraph("EARTH SYSTEMS TREND DETECTIVE", title_style))
        elements.append(Paragraph(f"Scientific Trend Investigation Dossier • Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
        elements.append(Spacer(1, 10))

        # 2. Metadata Table
        var_name = data.get("variable_name", data.get("variable", "N/A"))
        region_name = data.get("region", "All India")
        start_date = data.get("start_date", "2015-01-01")
        end_date = data.get("end_date", "2024-12-01")
        sample_size = data.get("sample_size", 0)
        unit = data.get("unit", "")

        meta_data = [
            [Paragraph("<b>Environmental Variable:</b>", body_style), Paragraph(f"{var_name} ({unit})", body_style)],
            [Paragraph("<b>Geographic Region:</b>", body_style), Paragraph(f"{region_name}", body_style)],
            [Paragraph("<b>Temporal Horizon:</b>", body_style), Paragraph(f"{start_date} to {end_date} ({sample_size} observations)", body_style)],
            [Paragraph("<b>Data Source:</b>", body_style), Paragraph("NASA POWER Surface Meteorology / Copernicus Sentinel-5P", body_style)],
            [Paragraph("<b>Analysis Standard:</b>", body_style), Paragraph("OLS Regression, Mann-Kendall Trend Test, Sen's Robust Slope", body_style)]
        ]

        meta_table = Table(meta_data, colWidths=[150, 380])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # 3. Statistical Scorecard
        elements.append(Paragraph("Statistical Trend Results", section_heading))
        
        lr = data.get("linear_regression", {})
        mk = data.get("mann_kendall", {})
        sen = data.get("sens_slope", {})
        classification = data.get("trend_classification", "No Clear Trend")
        is_sig = data.get("is_statistically_significant", False)

        sig_color = colors.HexColor('#16a34a') if is_sig else colors.HexColor('#d97706')

        stats_data = [
            [
                Paragraph("<b>Trend Classification:</b>", body_style),
                Paragraph(f"<b><font color='{sig_color.hexval()}'>{classification}</font></b>", body_style)
            ],
            [
                Paragraph("<b>Annualized Rate of Change (OLS):</b>", body_style),
                Paragraph(f"<b>{lr.get('annualized_rate', 0):+.4f}</b> {lr.get('unit', '')}", body_style)
            ],
            [
                Paragraph("<b>Sen's Robust Slope:</b>", body_style),
                Paragraph(f"<b>{sen.get('annualized_rate', 0):+.4f}</b> {sen.get('unit', '')} (95% CI: {sen.get('ci_lower', 0):+.4f} to {sen.get('ci_upper', 0):+.4f})", body_style)
            ],
            [
                Paragraph("<b>Mann-Kendall Rank Test:</b>", body_style),
                Paragraph(f"Kendall's tau: <b>{mk.get('tau', 0):+.4f}</b> | S-stat: {mk.get('s_statistic', 0):.0f}", body_style)
            ],
            [
                Paragraph("<b>Statistical Significance:</b>", body_style),
                Paragraph(f"<b>p = {mk.get('p_value', 1.0):.5f}</b> ({'Significant at alpha = 0.05' if is_sig else 'Not significant'})", body_style)
            ],
            [
                Paragraph("<b>Model Goodness-of-Fit (R²):</b>", body_style),
                Paragraph(f"R² = {lr.get('r_squared', 0):.4f} (Standard Error: {lr.get('std_err', 0):.5f})", body_style)
            ]
        ]

        stats_table = Table(stats_data, colWidths=[180, 350])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 15))

        # 4. Plain Language Scientific Summary
        elements.append(Paragraph("Scientific Interpretation", section_heading))
        summary_text = data.get("plain_language_summary", "No interpretation generated.")
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 15))

        # 5. Scientific Caveats & Limitations
        elements.append(Paragraph("Scientific Caveats & Integrity Standard", section_heading))
        caveats = data.get("scientific_caveats", [
            "Correlation does not establish causality. Atmospheric variables are conditioned by large-scale circulation.",
            "Column atmospheric concentration is not surface emission flux.",
            "Missing observations represent cloudy or QA-filtered soundings, never zero."
        ])
        caveat_text = "<br/>• ".join(["• " + c for c in caveats])
        elements.append(Paragraph(caveat_text, body_style))

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

report_service = ReportService()
