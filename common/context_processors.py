import typing

def csp_nonce(request: typing.Any) -> dict:
    """Return the CSP nonce for the current request."""
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}

def message_context(request: typing.Any) -> dict:
    """Return a message_context variable based on the current app path for message filtering."""
    path = request.path
    if path.startswith('/audit/'):
        return {'message_context': 'audit'}
    elif path.startswith('/risk/'):
        return {'message_context': 'risk'}
    elif path.startswith('/compliance/'):
        return {'message_context': 'compliance'}
    elif path.startswith('/legal/'):
        return {'message_context': 'legal'}
    elif path.startswith('/contracts/'):
        return {'message_context': 'contracts'}
    elif path.startswith('/document_management/'):
        return {'message_context': 'document_management'}
    elif path.startswith('/users/'):
        return {'message_context': 'users'}
    elif path.startswith('/organizations/'):
        return {'message_context': 'organizations'}
    return {'message_context': None}
