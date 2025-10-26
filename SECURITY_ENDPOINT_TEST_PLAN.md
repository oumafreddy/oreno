# Oreno GRC – Endpoint Security & Tenancy Assurance Test Plan

Version: 1.0
Status: Draft for execution
Owner: Engineering / Security

Note: Only `/public/` URLs are publicly accessible without authentication. All other routes must enforce authentication and tenant context.

## Objectives
- Verify every HTTP endpoint (web views and APIs) enforces:
  - Authentication and authorization per role/permission (except `/public/`)
  - Strict tenant scoping for data access and side effects
  - Input validation and sanitization at Django Forms and DRF Serializers
  - Correct middleware-driven tenant context on all requests
  - Rate limiting on authentication and API endpoints
  - Comprehensive, tenant-aware audit logging of security events
  - Transport security assumptions (HTTPS, secure cookies)

## Scope
- All URL patterns in `config/urls.py`, each app’s `urls.py`, and API routes under `/api/*`.
- Apps: `users`, `organizations`, `audit`, `risk`, `compliance`, `contracts`, `document_management`, `legal`, `ai_governance`, `reports`, `admin_module`, `core`, `common`.
- Environments: Local dev; tenant-aware hosts/domains.

## Artifacts Produced
- Endpoint inventory (CSV/JSON) with auth, tenancy, methods, params
- Test results with pass/fail and evidence (responses, logs)
- Issues list with severity and remediation

---

## 1) Endpoint Inventory and Mapping

### 1.1 Discovery Process
- Parse `config/urls.py` and each app’s `urls.py` to enumerate:
  - Path pattern, name, view, allowed methods
  - Namespace, app
  - Public vs tenant routes (flag `/public/*` as unauthenticated; everything else requires auth)
- For API views: capture DRF view classes, serializers, permissions.

### 1.2 Generated Inventory Fields
- `app`, `namespace`, `name`, `path`, `methods`, `view`, `is_api`, `requires_auth`, `rate_limited`, `tenant_scoped`, `serializer_or_form`, `permissions`, `throttles`.

### 1.3 Tools
- Django `show_urls` (django-extensions) if available; fallback: script to introspect `urlpatterns` and DRF routes.

---

## 2) Authentication & Authorization Tests

### 2.1 Unauthenticated Access
- For endpoints with `requires_auth=True`:
  - Send request without session/JWT: expect 302→login (web) or 401/403 (API).
- For `/public/*` endpoints:
  - Confirm accessible without authentication; no sensitive data leakage.

### 2.2 Authenticated Access – Role Matrix
- Create test users: `admin`, `manager`, `staff`, `risk_champion`, minimal user.
- Verify access per `permission_classes` and view mixins.

### 2.3 Token/JWT Handling (API)
- Validate `Authorization: Bearer <token>` where expected.
- Expired/blacklisted token → 401.
- Token for different tenant → 403 if tenant mismatch.

### 2.4 Session Security (Web)
- Secure cookie flags (Secure, HttpOnly, SameSite) set per settings.
- Session fixation: new session on login.

Evidence: response codes, headers, redirected URLs, screenshots where relevant.

---

## 3) Tenant Scoping & Row-Level Isolation

### 3.1 Middleware Context
- Confirm tenant resolution per host/domain.
- `request.tenant` and `request.organization` set on all authenticated requests.

### 3.2 Cross-Tenant Access Attempts
- Tenants A and B, users UA and UB:
  - UA requests B domain → logout/deny.
  - UA queries B object → 404/403; never returns B data.

### 3.3 Query Enforcement
- Verify querysets and writes are tenant-filtered.

Evidence: cross-domain request pairs, DB assertions, tenant-tagged logs.

---

## 4) Input Validation & Sanitization

### 4.1 DRF Serializers
- Valid payloads → 2xx.
- Invalid/out-of-range/disallowed fields → 400 with explicit errors.
- HTML/JS injection attempts → escaped/rejected.

### 4.2 Django Forms (Web)
- Server-side validation; CSRF present; file limits enforced.

### 4.3 IDOR & Overposting
- Attempts to set foreign keys to other-tenant IDs → rejected/ignored.

Evidence: error payloads; DB checks; rendering checks.

---

## 5) Rate Limiting & Abuse Controls

### 5.1 Authentication Endpoints
- `/accounts/login/`, `/api/token/`, OTP verify/resend: throttle classes enforced.
- Burst testing → 429 with `Retry-After`.

### 5.2 API Throttling
- Validate DRF throttle rates for anon/user per settings.

Evidence: 429 responses, headers, logs.

---

## 6) Logging & Audit Trails

- Coverage: login success/failure, logout, password changes, OTP, access denied, tenant mismatch.
- Tenant-aware logs include tenant schema/name and user id/email.
- Errors logged to file and email as configured.

Evidence: log excerpts with tenant markers.

---

## 7) Transport & Security Headers

- HTTPS enforcement; HSTS in production.
- CSP, X-Frame-Options, X-Content-Type-Options.
- Cookies: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `HttpOnly`, `SameSite`.

Evidence: headers from representative endpoints (including `/public/*`).

---

## 8) Test Data & Fixtures

- Seed two tenants with distinct data sets.
- Create users per role in each tenant.

---

## 9) Execution Strategy

### 9.1 Tooling
- `pytest`, `pytest-django`, `pytest-xdist`, `httpx`/`requests`.
- Optional: `locust`/`k6` for rate-limit stress checks.

### 9.2 Phases
- Inventory + smoke; tenancy isolation; validation/sanitization; throttle; headers; regression.

---

## 10) Sample Test Snippets (Illustrative)

```python
# pytest + httpx examples (not executed here)
import httpx

def test_public_pages_accessible(public_base_url):
    r = httpx.get(f"{public_base_url}/public/docs/")
    assert r.status_code == 200


def test_api_requires_auth(base_url):
    r = httpx.get(f"{base_url}/api/risk/risks/")
    assert r.status_code in (401, 403)


def test_cross_tenant_denied(tenant_a_url, auth_b_token):
    r = httpx.get(f"{tenant_a_url}/api/risk/risks/", headers={"Authorization": f"Bearer {auth_b_token}"})
    assert r.status_code in (401, 403)


def test_throttle_login_excessive(base_url):
    for _ in range(0, 20):
        httpx.post(f"{base_url}/accounts/login/", data={"username": "u", "password": "p"})
    r = httpx.post(f"{base_url}/accounts/login/", data={"username": "u", "password": "p"})
    assert r.status_code == 429
```

---

## 11) Acceptance Criteria
- 100% endpoints inventoried with metadata
- No unauthorized access paths (except `/public/*`) found
- No cross-tenant leaks detected
- All inputs validated; overposting blocked
- Throttling enforced on auth/API endpoints
- Logs include tenant identifiers consistently

---

## 12) Reporting
- Daily execution summary
- Detailed defect log with reproduction and remediation
- Final attestation with evidence bundle
