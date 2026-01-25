"""
PDF API Views for Bill and Invoice downloads and previews

Provides REST API endpoints for downloading and previewing bills and invoices as PDF files.
"""

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from apps.sales.services.pdf_generator import BillPDFGenerator, InvoicePDFGenerator
import logging

logger = logging.getLogger(__name__)


class BillPDFMixin:
    """Mixin to add PDF download and preview functionality to Bill ViewSet"""
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """
        Download bill as PDF
        
        GET /api/bills/{id}/download_pdf/
        
        Returns:
            PDF file as attachment (downloaded)
        """
        try:
            bill = self.get_object()
            
            # Generate PDF
            pdf_file = BillPDFGenerator.generate(bill)
            
            # Return as file response with attachment
            return FileResponse(
                pdf_file,
                as_attachment=True,
                filename=f'bill_{bill.id}.pdf',
                content_type='application/pdf'
            )
        except Exception as e:
            logger.error(f"Error generating bill PDF: {str(e)}")
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview_pdf(self, request, pk=None):
        """
        Preview bill as PDF in browser
        
        GET /api/bills/{id}/preview_pdf/
        
        Returns:
            PDF file as inline preview (viewed in browser)
        """
        try:
            bill = self.get_object()
            
            # Generate PDF
            pdf_file = BillPDFGenerator.generate(bill)
            
            # Return as file response inline (for preview/viewing in browser)
            return FileResponse(
                pdf_file,
                as_attachment=False,
                filename=f'bill_{bill.id}.pdf',
                content_type='application/pdf'
            )
        except Exception as e:
            logger.error(f"Error generating bill PDF preview: {str(e)}")
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InvoicePDFMixin:
    """Mixin to add PDF download and preview functionality to Invoice ViewSet"""
    
    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        """
        Download invoice as PDF
        
        GET /api/invoices/{id}/download_pdf/
        
        Returns:
            PDF file as attachment (downloaded)
        """
        try:
            invoice = self.get_object()
            
            # Generate PDF
            pdf_file = InvoicePDFGenerator.generate(invoice)
            
            # Return as file response with attachment
            return FileResponse(
                pdf_file,
                as_attachment=True,
                filename=f'invoice_{invoice.invoice_number}.pdf',
                content_type='application/pdf'
            )
        except Exception as e:
            logger.error(f"Error generating invoice PDF: {str(e)}")
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='preview-pdf')
    def preview_pdf(self, request, pk=None):
        """
        Preview invoice as PDF in browser
        
        GET /api/invoices/{id}/preview_pdf/
        
        Returns:
            PDF file as inline preview (viewed in browser)
        """
        try:
            invoice = self.get_object()
            
            # Generate PDF
            pdf_file = InvoicePDFGenerator.generate(invoice)
            
            # Return as file response inline (for preview/viewing in browser)
            return FileResponse(
                pdf_file,
                as_attachment=False,
                filename=f'invoice_{invoice.invoice_number}.pdf',
                content_type='application/pdf'
            )
        except Exception as e:
            logger.error(f"Error generating invoice PDF preview: {str(e)}")
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
