from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse

def generate_pdf_report(analysis_result):
    """Generate secure PDF report"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # PDF content generation
    p.drawString(100, 750, "Land Change Analysis Report")
    p.drawString(100, 730, f"Analysis ID: {analysis_result.id}")
    p.drawString(100, 710, f"Change Percentage: {analysis_result.change_percentage}%")
    p.drawString(100, 690, f"Processing Time: {analysis_result.processing_time} seconds")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

def pdf_response(analysis_result):
    """Create HTTP response with PDF"""
    buffer = generate_pdf_report(analysis_result)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analysis_{analysis_result.id}.pdf"'
    return response