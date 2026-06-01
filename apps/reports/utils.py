"""Helpers for report views — date parsing and queryset filters."""
from __future__ import annotations

from datetime import datetime

from django.utils.dateparse import parse_date


def parse_report_date_filters(request):
    """
    Parse optional start_date / end_date from GET, returning ISO date strings or None.
    Invalid dates are ignored (middleware blocks malicious strings).
    """
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    out = {'start_date': None, 'end_date': None}
    if start:
        parsed = parse_date(start)
        if parsed:
            out['start_date'] = parsed.isoformat()
    if end:
        parsed = parse_date(end)
        if parsed:
            out['end_date'] = parsed.isoformat()
    return out


def apply_date_filter(qs, field_name: str, filters: dict):
    """Apply start/end date filters to a queryset when values are present."""
    if filters.get('start_date'):
        qs = qs.filter(**{f'{field_name}__gte': filters['start_date']})
    if filters.get('end_date'):
        qs = qs.filter(**{f'{field_name}__lte': filters['end_date']})
    return qs
