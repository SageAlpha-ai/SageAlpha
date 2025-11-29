# app/pdf_routes_playwright.py
from flask import Blueprint, render_template, make_response, current_app
from playwright.sync_api import sync_playwright
import logging

bp = Blueprint("pdf_playwright", __name__)

@bp.route("/download-report-playwright")
def download_report_playwright():
    """
    Renders 'templates/sagealpha_report.html' to PDF using Playwright (Chromium).
    Returns PDF bytes as attachment.
    If Playwright fails, falls back to returning the HTML (so user can Print -> Save as PDF).
    """
    try:
        html = render_template("sagealpha_report.html")

        # Use sync_playwright to keep code simple in Flask
        with sync_playwright() as pw:
            # Launch Chromium headless. Use no-sandbox on restrictive containers.
            browser = pw.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            # Set HTML content and wait for network idle so fonts and images load
            page.set_content(html, wait_until="networkidle")
            # produce PDF (printBackground ensures background colors/images are included)
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
            )
            browser.close()

        resp = make_response(pdf_bytes)
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = 'attachment; filename="SageAlpha_CRH_Report.pdf"'
        resp.headers["X-PDF-Generated"] = "yes (playwright)"
        return resp
    except Exception as e:
        current_app.logger.exception("Playwright PDF generation failed: %s", e)
        # fallback: render HTML inline so user can print->save
        html = render_template("sagealpha_report.html")
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Content-Disposition"] = 'inline; filename="SageAlpha_CRH_Report.html"'
        resp.headers["X-PDF-Generated"] = "no (fallback)"
        return resp
