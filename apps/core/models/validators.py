import os
import re
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME = re.compile(r'[\\/<>:"|?*\x00]|\.\.')

# Extension → allowed leading magic bytes (partial signatures)
_MIME_SIGNATURES = {
    'pdf': (b'%PDF',),
    'doc': (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',),
    'docx': (b'PK\x03\x04',),
    'xls': (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',),
    'xlsx': (b'PK\x03\x04',),
    'pptx': (b'PK\x03\x04',),
    'txt': None,  # text has no reliable magic; extension check only
    'jpg': (b'\xFF\xD8\xFF',),
    'jpeg': (b'\xFF\xD8\xFF',),
    'png': (b'\x89PNG\r\n\x1a\n',),
    'gif': (b'GIF87a', b'GIF89a',),
}


def validate_safe_filename(value):
    """Reject path traversal and unsafe characters in uploaded filenames."""
    name = os.path.basename(getattr(value, 'name', '') or '')
    if not name or _UNSAFE_FILENAME.search(name):
        raise ValidationError(_('Invalid file name.'))


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

def validate_file_content_signature(value):
    """Verify file content matches extension using magic-byte sniffing."""
    validate_safe_filename(value)
    ext = os.path.splitext(value.name)[1][1:].lower()
    signatures = _MIME_SIGNATURES.get(ext)
    if signatures is None:
        return
    head = value.read(16)
    value.seek(0)
    if not any(head.startswith(sig) for sig in signatures):
        raise ValidationError(
            _('File content does not match the ".%(ext)s" extension.'),
            params={'ext': ext},
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
            # Avoid buffering whole uploads in memory: write to a temp file and scan by path.
            import tempfile
            value.seek(0)
            with tempfile.NamedTemporaryFile(prefix="oreno-upload-", suffix=".bin", delete=True) as tmp:
                for chunk in iter(lambda: value.read(1024 * 1024), b""):
                    tmp.write(chunk)
                tmp.flush()
                result = cd.scan_file(tmp.name)

            # Reset the file pointer for further processing
            value.seek(0)
            if result:
                raise ValidationError(
                    _('The uploaded file appears to be infected: %(result)s'),
                    params={'result': result},
                )
                
        except Exception as e:
            logger.error(f"Virus scan failed: {str(e)}")
            if getattr(settings, 'FAIL_ON_SCAN_ERROR', True):
                raise ValidationError(_('Virus scan failed during processing'))

    value.seek(0)


def file_upload_validators(*, virus_scan: bool = False):
    """Standard validator chain for user-uploaded documents."""
    validators = [
        validate_safe_filename,
        validate_file_extension,
        validate_file_content_signature,
        validate_file_size,
    ]
    if virus_scan:
        validators.append(validate_file_virus)
    return validators


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