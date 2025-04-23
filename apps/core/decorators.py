# apps/core/decorators.py

from functools import wraps

def skip_org_check(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        setattr(request, '_skip_org_check', True)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
