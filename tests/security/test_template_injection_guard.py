"""Tests for SSTI / template-probe request blocking."""
import pytest  # type: ignore[reportMissingImports]
from django.test import Client, override_settings


@override_settings(TEMPLATE_INJECTION_GUARD_ENABLED=True, DEBUG=False)
def test_blocks_template_probe_in_search_query(client_public):
    response = client_public.get('/public/', {'search': '{{7*7}}'})
    assert response.status_code == 400


@override_settings(TEMPLATE_INJECTION_GUARD_ENABLED=True, DEBUG=False)
def test_allows_normal_search_query(client_public):
    response = client_public.get('/public/', {'search': 'audit workplan'})
    assert response.status_code in (200, 301, 302)
