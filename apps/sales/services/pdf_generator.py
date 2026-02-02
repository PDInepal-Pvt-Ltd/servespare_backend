"""
PDF Generation Service for Bills and Invoices using WeasyPrint

Generates clean, professional HTML-based PDFs with:
- Company logo and header
- Customer information
- Itemized tables
- Tax calculations
- Totals and payment information
"""

from io import BytesIO
from decimal import Decimal
from django.template.loader import render_to_string
from django.conf import settings
try:
    from xhtml2pdf import pisa
except Exception:
    # Optional dependency for PDF generation; allow import-time to succeed in test environments
    pisa = None

import os
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Service for generating PDF documents from HTML templates"""
    
    @staticmethod
    def html_to_pdf(html_content, filename=None):
        """
        Convert HTML content to PDF using xhtml2pdf
        
        Args:
            html_content (str): HTML content to convert
            filename (str): Optional filename
            
        Returns:
            BytesIO: PDF content in bytes
        """
        pdf_file = BytesIO()
        
        if pisa is None:
            raise RuntimeError('xhtml2pdf is not installed; PDF generation is unavailable in this environment')

        try:
            # Generate PDF from HTML with better settings
            pisa_status = pisa.CreatePDF(
                html_content,
                pdf_file,
                show_error_as_pdf=False,
                raise_on_error=False
            )

            if pisa_status.err:
                logger.warning(f"PDF generation warnings: {pisa_status.err}")

            pdf_file.seek(0)
            return pdf_file
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    @staticmethod
    def get_static_url(path):
        """Get absolute URL for static files in PDF context"""
        if path.startswith('http'):
            return path
        
        # For local file system
        static_root = getattr(settings, 'STATIC_ROOT', 'static')
        return os.path.join(static_root, path)


class BillPDFGenerator(PDFGenerator):
    """Service for generating Bill PDFs"""
    
    @staticmethod
    def generate(bill):
        """
        Generate PDF for a Bill
        
        Args:
            bill (Bill): Bill instance
            
        Returns:
            BytesIO: PDF content
        """
        context = {
            'bill': bill,
            'company_name': getattr(settings, 'COMPANY_NAME', 'ServeSpare'),
            'company_logo': getattr(settings, 'COMPANY_LOGO_URL', ''),
            'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
            'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
            'company_email': getattr(settings, 'COMPANY_EMAIL', ''),
            'tax_label': getattr(settings, 'TAX_LABEL', 'VAT'),
        }
        
        # Render template
        html_content = render_to_string('sales/bill_pdf.html', context)
        
        # Generate PDF
        return PDFGenerator.html_to_pdf(html_content, filename=f'bill_{bill.id}.pdf')


class InvoicePDFGenerator(PDFGenerator):
    """Service for generating Invoice PDFs"""
    
    @staticmethod
    def generate(invoice):
        """
        Generate PDF for an Invoice
        
        Args:
            invoice (Invoice): Invoice instance
            
        Returns:
            BytesIO: PDF content
        """
        # Get purchase items if related through sales_order
        purchase_items = []
        if invoice.sales_order:
            purchase_items = invoice.sales_order.items.all()
        
        context = {
            'invoice': invoice,
            'purchase_items': purchase_items,
            'company_name': getattr(settings, 'COMPANY_NAME', 'ServeSpare'),
            'company_logo': getattr(settings, 'COMPANY_LOGO_URL', ''),
            'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
            'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
            'company_email': getattr(settings, 'COMPANY_EMAIL', ''),
            'tax_label': getattr(settings, 'TAX_LABEL', 'VAT'),
        }
        
        # Render template
        html_content = render_to_string('sales/invoice_pdf.html', context)
        
        # Generate PDF
        return PDFGenerator.html_to_pdf(html_content, filename=f'invoice_{invoice.invoice_number}.pdf')
