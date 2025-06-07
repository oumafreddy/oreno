import typing

def csp_nonce(request: typing.Any) -> dict:
    """Return the CSP nonce for the current request."""
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}
