import os
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field

logger = logging.getLogger(__name__)

def validate_file_extension(value):
    """Validate file extensions against a whitelist."""
    valid_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in valid_extensions:
        allowed = ", ".join(sorted(valid_extensions))
        raise ValidationError(
            _('Unsupported file extension ".%(ext)s". Allowed extensions: %(allowed)s.'),
            params={'ext': ext, 'allowed': allowed},
        )

def validate_file_size(value):
    """Ensure file size does not exceed MAX_UPLOAD_SIZE_MB from settings."""
    max_size_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)
    max_bytes = max_size_mb * 1024 * 1024
    if value.size > max_bytes:
        raise ValidationError(
            _('Maximum file size is %(max_size)dMB. Your file is too large.'),
            params={'max_size': max_size_mb},
        )

def validate_file_virus(value):
    """Dynamically handles virus scanning with graceful degradation."""
    
    # 1. Check if virus scanning is enabled
    if not getattr(settings, 'ENABLE_VIRUS_SCANNING', False):
        return  # Skip scanning if disabled

    # 2. Check if file is empty
    if not value:
        return

    # 3. Attempt connection to ClamAV with circuit breaker pattern
    clamd_available = False
    try:
        import pyclamd
        cd = pyclamd.ClamdNetworkSocket()
        cd.ping()
        clamd_available = True
    except Exception as e:
        logger.warning(f"ClamAV unavailable: {str(e)}")
        if getattr(settings, 'FAIL_IF_SCANNER_UNAVAILABLE', False):
            raise ValidationError(_('Virus scanning service is currently unavailable'))

    # 4. Perform scan if available
    if clamd_available:
        try:
            # Stream file in chunks to avoid memory issues
            def file_chunks():
                value.seek(0)
                while chunk := value.read(1024 * 1024):  # 1MB chunks
                    yield chunk

            # Build complete content from the chunks for scanning
            scanned_content = b"".join(file_chunks())
            # Reset the file pointer for further processing
            value.seek(0)
            
            result = cd.scan_stream(scanned_content)
            if result:
                raise ValidationError(
                    _('The uploaded file appears to be infected: %(result)s'),
                    params={'result': result},
                )
                
        except Exception as e:
            logger.error(f"Virus scan failed: {str(e)}")
            if getattr(settings, 'FAIL_ON_SCAN_ERROR', True):
                raise ValidationError(_('Virus scan failed during processing'))

    # Optional: Final reset of the file pointer, if needed by later processing.
    value.seek(0)

def validate_engagement_document_extension(value):
    """Validate file extensions for engagement documents. Only allows PDF, DOC, DOCX, XLSX, PPTX."""
    valid_extensions = {'pdf', 'doc', 'docx', 'xlsx', 'pptx'}
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in valid_extensions:
        allowed = ", ".join(sorted(valid_extensions))
        raise ValidationError(
            _('Unsupported file extension ".%(ext)s". Allowed extensions for engagement documents: %(allowed)s.'),
            params={'ext': ext, 'allowed': allowed},
        )