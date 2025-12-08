# app/pdf_routes.py
import os
import subprocess
import tempfile
from flask import Blueprint, render_template, make_response, send_file, current_app
from io import BytesIO

bp = Blueprint("pdf", __name__)

# optional pdfkit
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except Exception:
    pdfkit = None
    PDFKIT_AVAILABLE = False

def find_wkhtmltopdf():
    """Return first usable wkhtmltopdf binary path or None."""
    candidates = [
        os.path.join(os.getcwd(), "bin", "wkhtmltopdf"),
        "/usr/local/bin/wkhtmltopdf",
        "/usr/bin/wkhtmltopdf",
        "/usr/bin/wkhtmltopdf-amd64",
        "/usr/local/bin/wkhtmltox",
    ]
    for p in candidates:
        if p and os.path.exists(p) and os.access(p, os.X_OK):
            return p
    # try common PATH lookup
    for cmd in ("wkhtmltopdf",):
        try:
            which = subprocess.run(["which", cmd], capture_output=True, text=True)
            if which.returncode == 0:
                path = which.stdout.strip().splitlines()[0]
                if path and os.path.exists(path) and os.access(path, os.X_OK):
                    return path
        except Exception:
            continue
    return None

def try_pdfkit_from_string(html):
    """Attempt to generate PDF using pdfkit (python wrapper). Return bytes or None."""
    if not PDFKIT_AVAILABLE:
        return None
    config = None
    try:
        # Try to configure with a known binary location if present
        wk = find_wkhtmltopdf()
        if wk:
            config = pdfkit.configuration(wkhtmltopdf=wk)
        # options similar to your previous config
        options = {
            "page-size": "A4",
            "encoding": "UTF-8",
            "enable-local-file-access": None,
            "quiet": "",
            "margin-top": "10mm",
            "margin-bottom": "10mm",
            "margin-left": "10mm",
            "margin-right": "10mm",
        }
        pdf_bytes = pdfkit.from_string(html, False, configuration=config, options=options)
        if isinstance(pdf_bytes, (bytes, bytearray)):
            return bytes(pdf_bytes)
    except Exception as e:
        current_app.logger.exception("pdfkit.from_string failed: %s", e)
    return None

def try_wkhtmltopdf_subprocess(html):
    """
    Attempt to run wkhtmltopdf binary as a subprocess reading HTML from stdin and capturing stdout PDF.
    Returns bytes or None.
    """
    wk = find_wkhtmltopdf()
    if not wk:
        return None
    # use '-' for stdin input and '-' for stdout output if supported
    # Some wkhtmltopdf builds accept '-' as input and '-' as output. We'll use tempfile fallback too.
    try:
        # prefer to use stdin/stdout piping if binary supports it
        proc = subprocess.Popen([wk, '-', '-'],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        out, err = proc.communicate(input=html.encode('utf-8'), timeout=60)
        if proc.returncode == 0 and out:
            return out
        # If that failed, try tempfile method
        current_app.logger.warning("wkhtmltopdf stdin/stdout failed (rc=%s), stderr: %s", proc.returncode, err.decode('utf-8', errors='ignore'))
    except Exception as e:
        current_app.logger.exception("wkhtmltopdf stdin/stdout attempt failed: %s", e)

    # Tempfile fallback: write html to temp file and run wkhtmltopdf input->output file
    try:
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as in_f:
            in_f.write(html.encode('utf-8'))
            in_path = in_f.name
        out_fd, out_path = tempfile.mkstemp(suffix='.pdf')
        os.close(out_fd)
        try:
            run = subprocess.run([wk, in_path, out_path], capture_output=True, timeout=60)
            if run.returncode == 0 and os.path.exists(out_path):
                with open(out_path, 'rb') as f:
                    data = f.read()
                return data
            else:
                current_app.logger.warning("wkhtmltopdf returned non-zero (%s). stderr: %s", run.returncode, run.stderr.decode('utf-8', errors='ignore'))
        finally:
            try: os.remove(in_path)
            except Exception: pass
            try: os.remove(out_path)
            except Exception: pass
    except Exception as e:
        current_app.logger.exception("wkhtmltopdf tempfile method failed: %s", e)
    return None

@bp.route("/download-report")
def download_report():
    """
    Render the report template. Try pdfkit -> wkhtmltopdf subprocess -> fallback HTML inline.
    Adds an X-PDF-Generated header set to 'yes' or 'no' for easier debugging.
    """
    template_name = "sagealpha_report.html"
    rendered = render_template(template_name)

    # 1) Try pdfkit (python wrapper)
    pdf_bytes = None
    if PDFKIT_AVAILABLE:
        pdf_bytes = try_pdfkit_from_string(rendered)
        if pdf_bytes:
            resp = make_response(pdf_bytes)
            resp.headers["Content-Type"] = "application/pdf"
            resp.headers["Content-Disposition"] = 'attachment; filename="SageAlpha_CRH_Report.pdf"'
            resp.headers["X-PDF-Generated"] = "yes (pdfkit)"
            return resp
        else:
            current_app.logger.info("pdfkit available but failed to produce PDF, falling back to wkhtmltopdf subprocess.")

    # 2) Try wkhtmltopdf binary via subprocess (if present)
    pdf_bytes = try_wkhtmltopdf_subprocess(rendered)
    if pdf_bytes:
        resp = make_response(pdf_bytes)
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = 'attachment; filename="SageAlpha_CRH_Report.pdf"'
        resp.headers["X-PDF-Generated"] = "yes (wkhtmltopdf)"
        return resp

    # 3) Fallback: return HTML inline so user can Print -> Save as PDF
    current_app.logger.warning("PDF generation failed (no pdfkit/wkhtmltopdf); returning HTML fallback.")
    resp = make_response(rendered)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Content-Disposition"] = 'inline; filename="SageAlpha_CRH_Report.html"'
    resp.headers["X-PDF-Generated"] = "no"
    return resp

@bp.route("/download-report-static")
def download_report_static():
    # If you place a pre-generated static PDF at static/sagealpha_report.pdf, this will serve it:
    static_pdf = os.path.join(current_app.static_folder or "static", "sagealpha_report.pdf")
    if os.path.exists(static_pdf):
        return send_file(static_pdf, as_attachment=True, download_name="SageAlpha_CRH_Report.pdf")
    # fallback to dynamic
    return download_report()

# simple test endpoint: serve a small static pdf file if present for client testing
@bp.route("/download-report-test")
def download_report_test():
    static_pdf = os.path.join(current_app.static_folder or "static", "test_report.pdf")
    if os.path.exists(static_pdf):
        return send_file(static_pdf, as_attachment=True, download_name="test_report.pdf")
    return ("Test PDF not found. Place a small PDF at static/test_report.pdf and retry.", 404)
