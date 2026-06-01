#!/usr/bin/env python3
"""
WebSecScan — Website Security Scanner
Replicates CheckVibe-style automated security checks.
Usage: python security_scanner.py <url> [--output report.html]
"""

import sys
import re
import ssl
import json
import socket
import argparse
import urllib.parse
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("Missing dependency: pip install requests")
    sys.exit(1)

# ── Data structures ────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4, "pass": 5}

SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high":     "#f97316",
    "medium":   "#eab308",
    "low":      "#3b82f6",
    "info":     "#8b5cf6",
    "pass":     "#22c55e",
}

@dataclass
class Finding:
    check_id: str
    title: str
    severity: str          # critical | high | medium | low | info | pass
    description: str
    detail: str = ""
    fix: str = ""
    category: str = "General"

@dataclass
class ScanResult:
    url: str
    scanned_at: str
    findings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    duration_ms: int = 0


# ── Helpers ────────────────────────────────────────────────────────────────────

def safe_get(url: str, timeout: int = 10, verify: bool = True,
             allow_redirects: bool = True, **kwargs) -> Optional[requests.Response]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (WebSecScan/1.0; security-audit)"}
        return requests.get(url, timeout=timeout, verify=verify,
                            allow_redirects=allow_redirects, headers=headers, **kwargs)
    except Exception:
        return None


def safe_head(url: str, timeout: int = 8, verify: bool = True) -> Optional[requests.Response]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (WebSecScan/1.0; security-audit)"}
        return requests.head(url, timeout=timeout, verify=verify,
                             allow_redirects=True, headers=headers)
    except Exception:
        return None


# ── Security Checks ────────────────────────────────────────────────────────────

def check_https(url: str, parsed) -> list[Finding]:
    findings = []
    if parsed.scheme == "http":
        https_url = url.replace("http://", "https://", 1)
        r = safe_head(https_url)
        if r and r.status_code < 400:
            findings.append(Finding(
                check_id="HTTPS-001",
                title="Site accessible over HTTP (HTTPS available)",
                severity="medium",
                description="The site is reachable over unencrypted HTTP. Attackers can intercept traffic.",
                detail=f"HTTP {url} is live. HTTPS is also available at {https_url}.",
                fix="Redirect all HTTP traffic to HTTPS and set HSTS. In Django: set SECURE_SSL_REDIRECT = True and SECURE_HSTS_SECONDS = 31536000.",
                category="Transport Security",
            ))
        else:
            findings.append(Finding(
                check_id="HTTPS-001",
                title="Site running on HTTP only — no HTTPS",
                severity="critical",
                description="The site has no HTTPS. All data is transmitted in plaintext.",
                detail=f"HTTPS endpoint {https_url} returned no valid response.",
                fix="Install a TLS certificate (free via Let's Encrypt). Force HTTPS in your web server config.",
                category="Transport Security",
            ))
    else:
        findings.append(Finding(
            check_id="HTTPS-001",
            title="HTTPS in use",
            severity="pass",
            description="Site is served over HTTPS.",
            category="Transport Security",
        ))
    return findings


def check_https_redirect(url: str, parsed) -> list[Finding]:
    if parsed.scheme != "https":
        return []
    http_url = "http://" + parsed.netloc + parsed.path
    r = safe_get(http_url, allow_redirects=False, timeout=8)
    if r is None:
        return []
    if r.status_code in (301, 302, 307, 308):
        loc = r.headers.get("Location", "")
        if loc.startswith("https"):
            return [Finding(
                check_id="HTTPS-002",
                title="HTTP redirects to HTTPS",
                severity="pass",
                description="Server correctly redirects HTTP requests to HTTPS.",
                category="Transport Security",
            )]
    return [Finding(
        check_id="HTTPS-002",
        title="HTTP does not redirect to HTTPS",
        severity="medium",
        description="Requests to the HTTP version of the site are not automatically redirected to HTTPS.",
        detail=f"HTTP {http_url} returned status {r.status_code} without an HTTPS redirect.",
        fix="Configure your web server to issue a 301 redirect from HTTP to HTTPS for all requests.",
        category="Transport Security",
    )]


def check_ssl_cert(parsed) -> list[Finding]:
    if parsed.scheme != "https":
        return []
    hostname = parsed.hostname
    findings = []
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.create_connection((hostname, 443), timeout=8),
                             server_hostname=hostname) as s:
            cert = s.getpeercert()
            expire_str = cert.get("notAfter", "")
            if expire_str:
                expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                days_left = (expire_dt - datetime.now(timezone.utc)).days
                if days_left < 0:
                    findings.append(Finding(
                        check_id="SSL-001",
                        title="SSL certificate has expired",
                        severity="critical",
                        description="The TLS certificate is expired. Browsers will display security warnings.",
                        detail=f"Certificate expired {abs(days_left)} days ago on {expire_str}.",
                        fix="Renew your SSL certificate immediately. If using Let's Encrypt, run: certbot renew",
                        category="SSL / TLS",
                    ))
                elif days_left < 30:
                    findings.append(Finding(
                        check_id="SSL-001",
                        title=f"SSL certificate expiring soon ({days_left} days)",
                        severity="high",
                        description="Certificate is about to expire. Plan renewal now.",
                        detail=f"Expires: {expire_str}",
                        fix="Renew the certificate before it expires. Enable auto-renewal if possible.",
                        category="SSL / TLS",
                    ))
                else:
                    findings.append(Finding(
                        check_id="SSL-001",
                        title=f"SSL certificate valid ({days_left} days remaining)",
                        severity="pass",
                        description=f"Certificate expires on {expire_str}.",
                        category="SSL / TLS",
                    ))
            version = s.version()
            if version in ("TLSv1", "TLSv1.1", "SSLv2", "SSLv3"):
                findings.append(Finding(
                    check_id="SSL-002",
                    title=f"Weak TLS version in use: {version}",
                    severity="high",
                    description=f"{version} is deprecated and has known vulnerabilities.",
                    fix="Configure your server to use TLS 1.2 or 1.3 only. Disable TLS 1.0 and 1.1.",
                    category="SSL / TLS",
                ))
            else:
                findings.append(Finding(
                    check_id="SSL-002",
                    title=f"TLS version acceptable: {version}",
                    severity="pass",
                    description=f"Server negotiated {version}.",
                    category="SSL / TLS",
                ))
    except ssl.SSLCertVerificationError as e:
        findings.append(Finding(
            check_id="SSL-001",
            title="SSL certificate validation failed",
            severity="critical",
            description="The certificate could not be validated — may be self-signed or misconfigured.",
            detail=str(e),
            fix="Install a certificate from a trusted CA. Check hostname matches the certificate Common Name.",
            category="SSL / TLS",
        ))
    except Exception:
        pass
    return findings


def check_security_headers(resp: requests.Response) -> list[Finding]:
    findings = []
    headers = {k.lower(): v for k, v in resp.headers.items()}

    # HSTS
    hsts = headers.get("strict-transport-security", "")
    if not hsts:
        findings.append(Finding(
            check_id="HDR-001",
            title="Missing Strict-Transport-Security (HSTS)",
            severity="medium",
            description="HSTS is not set. Browsers won't enforce HTTPS on repeat visits.",
            fix='Add header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload\nDjango: SECURE_HSTS_SECONDS = 31536000',
            category="Security Headers",
        ))
    else:
        max_age = re.search(r"max-age=(\d+)", hsts)
        if max_age and int(max_age.group(1)) < 3600:
            findings.append(Finding(
                check_id="HDR-001",
                title="HSTS max-age too short",
                severity="low",
                description=f"HSTS max-age is only {max_age.group(1)} seconds. Recommended minimum is 31536000 (1 year).",
                fix="Increase max-age to at least 31536000.",
                category="Security Headers",
            ))
        else:
            findings.append(Finding(
                check_id="HDR-001", title="HSTS header present",
                severity="pass", description=f"Value: {hsts}", category="Security Headers",
            ))

    # CSP
    csp = headers.get("content-security-policy", "")
    if not csp:
        findings.append(Finding(
            check_id="HDR-002",
            title="Missing Content-Security-Policy (CSP)",
            severity="high",
            description="No CSP header. XSS attacks have no browser-level mitigation.",
            fix="Define a CSP that restricts script sources. Start with:\nContent-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'\nDjango: use django-csp package.",
            category="Security Headers",
        ))
    elif "unsafe-inline" in csp and "unsafe-eval" in csp:
        findings.append(Finding(
            check_id="HDR-002",
            title="CSP uses both 'unsafe-inline' and 'unsafe-eval'",
            severity="high",
            description="CSP is effectively bypassed. Both unsafe directives allow XSS.",
            detail=f"CSP: {csp[:200]}",
            fix="Remove 'unsafe-inline' and 'unsafe-eval'. Use nonces or hashes for inline scripts.",
            category="Security Headers",
        ))
    elif "unsafe-inline" in csp or "unsafe-eval" in csp:
        findings.append(Finding(
            check_id="HDR-002",
            title="CSP contains unsafe directive",
            severity="medium",
            description="CSP weakened by 'unsafe-inline' or 'unsafe-eval'.",
            detail=f"CSP: {csp[:200]}",
            fix="Replace 'unsafe-inline' with script nonces. Replace 'unsafe-eval' with safer alternatives.",
            category="Security Headers",
        ))
    else:
        findings.append(Finding(
            check_id="HDR-002", title="Content-Security-Policy header present",
            severity="pass", description=f"Value: {csp[:150]}", category="Security Headers",
        ))

    # X-Frame-Options
    xfo = headers.get("x-frame-options", "")
    if not xfo:
        if csp and "frame-ancestors" in csp:
            findings.append(Finding(
                check_id="HDR-003", title="Clickjacking protection via CSP frame-ancestors",
                severity="pass", description="CSP frame-ancestors directive provides clickjacking protection.",
                category="Security Headers",
            ))
        else:
            findings.append(Finding(
                check_id="HDR-003",
                title="Missing X-Frame-Options (clickjacking protection)",
                severity="medium",
                description="The site can be embedded in iframes, enabling clickjacking attacks.",
                fix='Add header: X-Frame-Options: DENY\nDjango: X_FRAME_OPTIONS = "DENY"',
                category="Security Headers",
            ))
    else:
        findings.append(Finding(
            check_id="HDR-003", title="X-Frame-Options header present",
            severity="pass", description=f"Value: {xfo}", category="Security Headers",
        ))

    # X-Content-Type-Options
    xcto = headers.get("x-content-type-options", "")
    if xcto.lower() != "nosniff":
        findings.append(Finding(
            check_id="HDR-004",
            title="Missing X-Content-Type-Options: nosniff",
            severity="low",
            description="Browsers may MIME-sniff responses, enabling content injection attacks.",
            fix='Add header: X-Content-Type-Options: nosniff\nDjango: SECURE_CONTENT_TYPE_NOSNIFF = True',
            category="Security Headers",
        ))
    else:
        findings.append(Finding(
            check_id="HDR-004", title="X-Content-Type-Options: nosniff set",
            severity="pass", category="Security Headers",
        ))

    # Referrer-Policy
    rp = headers.get("referrer-policy", "")
    weak_rp = {"unsafe-url", "no-referrer-when-downgrade", ""}
    if not rp or rp.lower() in weak_rp:
        findings.append(Finding(
            check_id="HDR-005",
            title="Missing or weak Referrer-Policy",
            severity="low",
            description="Full URLs (including paths and query strings) may be leaked to third parties via the Referer header.",
            fix='Add header: Referrer-Policy: strict-origin-when-cross-origin',
            category="Security Headers",
        ))
    else:
        findings.append(Finding(
            check_id="HDR-005", title="Referrer-Policy set",
            severity="pass", description=f"Value: {rp}", category="Security Headers",
        ))

    # Permissions-Policy
    pp = headers.get("permissions-policy", "") or headers.get("feature-policy", "")
    if not pp:
        findings.append(Finding(
            check_id="HDR-006",
            title="Missing Permissions-Policy header",
            severity="low",
            description="No restrictions on browser features (camera, microphone, geolocation). Malicious scripts could abuse them.",
            fix='Add header: Permissions-Policy: geolocation=(), microphone=(), camera=()',
            category="Security Headers",
        ))
    else:
        findings.append(Finding(
            check_id="HDR-006", title="Permissions-Policy header present",
            severity="pass", description=f"Value: {pp[:150]}", category="Security Headers",
        ))

    return findings


def check_information_disclosure(resp: requests.Response) -> list[Finding]:
    findings = []
    headers = {k.lower(): v for k, v in resp.headers.items()}

    # Server header
    server = headers.get("server", "")
    if server:
        version_pattern = re.search(r"[\d.]{3,}", server)
        if version_pattern:
            findings.append(Finding(
                check_id="INF-001",
                title="Server header discloses version information",
                severity="low",
                description=f"Server header reveals software version: '{server}'. Attackers can target known CVEs.",
                fix="Remove or genericise the Server header in your web server config (nginx: server_tokens off; Apache: ServerTokens Prod).",
                category="Information Disclosure",
            ))
        else:
            findings.append(Finding(
                check_id="INF-001",
                title="Server header present (version not disclosed)",
                severity="info",
                description=f"Server header value: '{server}'. Consider removing entirely.",
                category="Information Disclosure",
            ))
    else:
        findings.append(Finding(
            check_id="INF-001", title="Server header not disclosed",
            severity="pass", description="Server version is not advertised in HTTP headers.",
            category="Information Disclosure",
        ))

    # X-Powered-By
    xpb = headers.get("x-powered-by", "")
    if xpb:
        findings.append(Finding(
            check_id="INF-002",
            title=f"X-Powered-By header discloses technology: '{xpb}'",
            severity="low",
            description="Reveals the underlying framework/language. Helps attackers fingerprint the stack.",
            fix="Remove this header. Django does not send it by default. In Express: app.disable('x-powered-by').",
            category="Information Disclosure",
        ))
    else:
        findings.append(Finding(
            check_id="INF-002", title="X-Powered-By header not present",
            severity="pass", description="Technology stack is not disclosed via X-Powered-By.",
            category="Information Disclosure",
        ))

    # X-Generator / X-WordPress-*
    for h in headers:
        if any(k in h for k in ("generator", "wordpress", "drupal", "joomla", "wix")):
            findings.append(Finding(
                check_id="INF-003",
                title=f"CMS/framework fingerprint header: {h}: {headers[h]}",
                severity="low",
                description="The CMS version is being advertised in HTTP headers.",
                fix="Remove CMS version headers to reduce fingerprinting surface.",
                category="Information Disclosure",
            ))
            break

    return findings


def check_cors(resp: requests.Response, url: str) -> list[Finding]:
    acao = resp.headers.get("Access-Control-Allow-Origin", "")
    acac = resp.headers.get("Access-Control-Allow-Credentials", "").lower()
    if not acao:
        return [Finding(
            check_id="CORS-001", title="No CORS policy set",
            severity="info",
            description="No Access-Control-Allow-Origin header. Cross-origin requests will be blocked by default.",
            category="CORS",
        )]
    if acao == "*" and acac == "true":
        return [Finding(
            check_id="CORS-001",
            title="Critical CORS misconfiguration: wildcard origin with credentials",
            severity="critical",
            description="Access-Control-Allow-Origin: * combined with Allow-Credentials: true allows any site to make authenticated cross-origin requests.",
            fix="Never combine ACAO: * with credentials. Specify explicit allowed origins instead.",
            category="CORS",
        )]
    if acao == "*":
        return [Finding(
            check_id="CORS-001",
            title="CORS allows all origins (wildcard)",
            severity="medium",
            description="Any website can read responses from this server. Acceptable for public APIs, risky for authenticated endpoints.",
            fix="Restrict CORS to known trusted origins rather than using *.",
            category="CORS",
        )]
    return [Finding(
        check_id="CORS-001", title=f"CORS restricted to: {acao}",
        severity="pass", description="CORS is configured to specific origins.", category="CORS",
    )]


def check_cookies(resp: requests.Response, parsed) -> list[Finding]:
    findings = []
    cookies = resp.cookies
    if not cookies:
        return findings
    is_https = parsed.scheme == "https"
    for cookie in cookies:
        issues = []
        if is_https and not cookie.secure:
            issues.append("missing Secure flag (cookie sent over HTTP)")
        if not cookie.has_nonstandard_attr("HttpOnly"):
            issues.append("missing HttpOnly flag (accessible by JavaScript)")
        samesite = cookie._rest.get("SameSite", "") if hasattr(cookie, "_rest") else ""
        if not samesite:
            issues.append("missing SameSite attribute (CSRF risk)")
        if issues:
            findings.append(Finding(
                check_id="COOK-001",
                title=f"Cookie '{cookie.name}' has security issues",
                severity="medium",
                description=f"Cookie flags missing: {', '.join(issues)}.",
                fix=f"Set cookie as: Set-Cookie: {cookie.name}=...; Secure; HttpOnly; SameSite=Strict\nDjango: SESSION_COOKIE_SECURE = True, SESSION_COOKIE_HTTPONLY = True, SESSION_COOKIE_SAMESITE = 'Strict'",
                category="Cookies",
            ))
        else:
            findings.append(Finding(
                check_id="COOK-001",
                title=f"Cookie '{cookie.name}' has correct security flags",
                severity="pass", category="Cookies",
            ))
    return findings


SENSITIVE_PATHS = [
    ("/.git/HEAD",         "critical", "Exposed .git directory", "The .git directory is publicly accessible. Full source code and history can be downloaded.", "Block .git in your web server config: location ~ /\\.git { deny all; }"),
    ("/.env",              "critical", "Exposed .env file", "Environment file exposed. Likely contains DB credentials, API keys, and secrets.", "Block .env files at the web server level. Never store secrets in web root."),
    ("/.env.local",        "critical", "Exposed .env.local file", "Local environment file exposed publicly.", "Block dot-files at web server level."),
    ("/.env.production",   "critical", "Exposed .env.production file", "Production environment file publicly accessible.", "Block dot-files at web server level."),
    ("/config.php",        "high",     "Exposed config.php", "PHP configuration file accessible. May contain DB credentials.", "Block config files from public access."),
    ("/wp-config.php",     "critical", "Exposed wp-config.php", "WordPress config file accessible. Contains DB credentials and secret keys.", "Deny access to wp-config.php in .htaccess."),
    ("/phpinfo.php",       "high",     "PHP info page exposed", "phpinfo() output reveals server configuration, PHP version, and environment variables.", "Remove phpinfo.php from production."),
    ("/admin",             "info",     "Admin panel accessible", "An /admin path is responding. Verify it requires authentication.", "Ensure strong auth, rate limiting, and consider moving to a non-standard path."),
    ("/wp-admin",          "info",     "WordPress admin panel accessible", "WordPress admin is publicly reachable.", "Restrict /wp-admin by IP if possible."),
    ("/backup",            "high",     "Backup directory accessible", "A /backup path is responding — may expose database dumps or source archives.", "Remove or restrict backup directories from public access."),
    ("/backup.zip",        "high",     "backup.zip accessible", "Backup archive may be downloadable.", "Remove backup archives from web root."),
    ("/db.sql",            "critical", "Database dump accessible", "A SQL dump file is publicly accessible.", "Remove all database dumps from web root immediately."),
    ("/server-status",     "medium",   "Apache server-status exposed", "Apache mod_status page reveals server internals and active requests.", "Restrict /server-status to localhost: Allow from 127.0.0.1"),
    ("/robots.txt",        "info",     "robots.txt accessible", "robots.txt is present.", ""),
    ("/.well-known/security.txt", "info", "security.txt present", "Security disclosure policy found.", ""),
]

def check_sensitive_paths(base_url: str) -> list[Finding]:
    findings = []
    parsed = urllib.parse.urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    for path, severity, title, description, fix in SENSITIVE_PATHS:
        r = safe_get(base + path, allow_redirects=False, timeout=6, verify=False)
        if r is None:
            continue
        if r.status_code == 200 and len(r.content) > 0:
            if path in ("/robots.txt", "/.well-known/security.txt"):
                findings.append(Finding(
                    check_id="PATH-001",
                    title=title,
                    severity=severity,
                    description=description,
                    detail=f"HTTP 200 at {base + path}",
                    category="Exposed Paths",
                ))
            else:
                findings.append(Finding(
                    check_id="PATH-001",
                    title=title,
                    severity=severity,
                    description=description,
                    detail=f"HTTP 200 at {base + path} ({len(r.content)} bytes)",
                    fix=fix,
                    category="Exposed Paths",
                ))
    if not any(f.check_id == "PATH-001" and f.severity in ("critical", "high", "medium") for f in findings):
        findings.append(Finding(
            check_id="PATH-001",
            title="No critical sensitive paths exposed",
            severity="pass",
            description="Common sensitive paths (.git, .env, wp-config, db dumps) are not publicly accessible.",
            category="Exposed Paths",
        ))
    return findings


SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}",                    "AWS Access Key ID"),
    (r"(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})", "AWS Secret Access Key"),
    (r"(?i)api[_\-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})",  "Generic API Key"),
    (r"(?i)secret[_\-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})","Secret Key"),
    (r"AIza[0-9A-Za-z\-_]{35}",              "Google API Key"),
    (r"(?i)firebase[_\-]?api[_\-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{30,})", "Firebase API Key"),
    (r"sk-[A-Za-z0-9]{48}",                  "OpenAI API Key"),
    (r"ghp_[A-Za-z0-9]{36}",                 "GitHub Personal Access Token"),
    (r"(?i)password\s*[:=]\s*['\"]([^'\"]{6,})['\"]", "Hardcoded Password"),
    (r"(?i)Bearer\s+([A-Za-z0-9\-._~+/]{40,})", "Bearer Token"),
    (r"(?i)private[_\-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})", "Private Key"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "PEM Private Key"),
]

def check_exposed_secrets(resp: requests.Response) -> list[Finding]:
    content = resp.text
    findings = []
    found = []
    for pattern, label in SECRET_PATTERNS:
        match = re.search(pattern, content)
        if match:
            found.append(label)
    if found:
        findings.append(Finding(
            check_id="SEC-001",
            title=f"Potential secrets exposed in page source: {', '.join(found)}",
            severity="critical",
            description="Pattern matches for secrets/credentials found in the page HTML source.",
            detail=f"Matched patterns: {', '.join(found)}",
            fix="Move all secrets to environment variables. Never embed API keys, tokens, or passwords in frontend code.",
            category="Secrets & Credentials",
        ))
    else:
        findings.append(Finding(
            check_id="SEC-001",
            title="No obvious secrets detected in page source",
            severity="pass",
            description="Common secret patterns (API keys, tokens, passwords) not found in HTML source.",
            category="Secrets & Credentials",
        ))
    return findings


def check_mixed_content(resp: requests.Response, parsed) -> list[Finding]:
    if parsed.scheme != "https":
        return []
    content = resp.text
    http_resources = re.findall(r'(?:src|href|action|data-src)\s*=\s*["\']http://[^"\']+["\']', content, re.IGNORECASE)
    http_resources = [r for r in http_resources if "localhost" not in r and "127.0.0.1" not in r]
    if http_resources:
        return [Finding(
            check_id="MIX-001",
            title=f"Mixed content: {len(http_resources)} HTTP resource(s) on HTTPS page",
            severity="medium",
            description="HTTP resources loaded on an HTTPS page. Browsers may block them and the connection is partially unencrypted.",
            detail="\n".join(http_resources[:5]),
            fix="Update all resource URLs to use HTTPS or protocol-relative URLs (//).",
            category="Transport Security",
        )]
    return [Finding(
        check_id="MIX-001", title="No mixed content detected",
        severity="pass", description="All resources appear to be loaded over HTTPS.",
        category="Transport Security",
    )]


def check_open_redirect(url: str, parsed) -> list[Finding]:
    test_payloads = [
        f"{url}?next=//evil.example.com",
        f"{url}?redirect=//evil.example.com",
        f"{url}?url=//evil.example.com",
        f"{url}?return=//evil.example.com",
    ]
    for payload in test_payloads:
        r = safe_get(payload, allow_redirects=False, timeout=6, verify=False)
        if r and r.status_code in (301, 302, 307, 308):
            loc = r.headers.get("Location", "")
            if "evil.example.com" in loc or loc.startswith("//evil"):
                return [Finding(
                    check_id="REDIR-001",
                    title="Open redirect vulnerability detected",
                    severity="high",
                    description="The site redirects to attacker-controlled URLs via query parameters. Enables phishing attacks.",
                    detail=f"Payload: {payload}\nRedirect Location: {loc}",
                    fix="Validate redirect targets against an allowlist. Never redirect to user-supplied URLs directly.",
                    category="Input Validation",
                )]
    return [Finding(
        check_id="REDIR-001", title="No open redirect detected",
        severity="pass", description="Common open redirect payloads did not trigger external redirects.",
        category="Input Validation",
    )]


def check_sql_injection_indicators(url: str) -> list[Finding]:
    payloads = [
        ("'", ["syntax error", "sql syntax", "mysql_fetch", "ora-01756", "quoted string not properly terminated",
               "unclosed quotation", "pg_query", "sqlite3", "sqlstate"]),
        ("1 AND 1=1", ["sql", "syntax", "mysql", "oracle", "postgres"]),
    ]
    findings = []
    for payload, error_patterns in payloads:
        test_url = url + ("&" if "?" in url else "?") + f"id={urllib.parse.quote(payload)}"
        r = safe_get(test_url, timeout=8, verify=False)
        if r:
            body = r.text.lower()
            for pattern in error_patterns:
                if pattern in body:
                    findings.append(Finding(
                        check_id="SQLI-001",
                        title="Potential SQL injection error disclosure",
                        severity="high",
                        description="SQL error messages are visible in response, indicating possible SQL injection surface.",
                        detail=f"Payload: {payload}\nMatched error keyword: '{pattern}'",
                        fix="Use parameterised queries (ORM or prepared statements). Never interpolate user input into SQL. Suppress SQL error messages in production.",
                        category="Injection",
                    ))
                    return findings
    findings.append(Finding(
        check_id="SQLI-001", title="No SQL error disclosure detected",
        severity="pass",
        description="Basic SQL injection probes did not trigger visible database errors.",
        category="Injection",
    ))
    return findings


def check_xss_indicators(url: str, resp: requests.Response) -> list[Finding]:
    xss_payload = "<script>alert(1)</script>"
    test_url = url + ("&" if "?" in url else "?") + f"q={urllib.parse.quote(xss_payload)}"
    r = safe_get(test_url, timeout=8, verify=False)
    if r and xss_payload in r.text:
        return [Finding(
            check_id="XSS-001",
            title="Reflected XSS: input reflected unescaped in response",
            severity="critical",
            description="A script tag in a query parameter was reflected back unescaped. This is a confirmed reflected XSS vulnerability.",
            detail=f"Payload '{xss_payload}' found unescaped in response body.",
            fix="Escape all user-supplied output in HTML context. Use template auto-escaping (Django templates do this by default). Apply a strong CSP.",
            category="Injection",
        )]
    return [Finding(
        check_id="XSS-001", title="No reflected XSS detected (basic probe)",
        severity="pass",
        description="Basic XSS payload was not reflected unescaped.",
        category="Injection",
    )]


# ── Main scan orchestrator ─────────────────────────────────────────────────────

def run_scan(url: str) -> ScanResult:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urllib.parse.urlparse(url)
    result = ScanResult(url=url, scanned_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
    start = datetime.now()

    print(f"\n  Scanning {url}\n")

    steps = [
        ("Transport & HTTPS",       lambda: check_https(url, parsed)),
        ("HTTPS redirect",          lambda: check_https_redirect(url, parsed)),
        ("SSL certificate",         lambda: check_ssl_cert(parsed)),
        ("Sensitive paths",         lambda: check_sensitive_paths(url)),
    ]

    r = safe_get(url, timeout=12, verify=False)
    if r is None:
        result.errors.append(f"Could not reach {url}")
        result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        return result

    steps += [
        ("Security headers",        lambda: check_security_headers(r)),
        ("Information disclosure",  lambda: check_information_disclosure(r)),
        ("CORS policy",             lambda: check_cors(r, url)),
        ("Cookie security",         lambda: check_cookies(r, parsed)),
        ("Exposed secrets in source", lambda: check_exposed_secrets(r)),
        ("Mixed content",           lambda: check_mixed_content(r, parsed)),
        ("Open redirect",           lambda: check_open_redirect(url, parsed)),
        ("SQL injection indicators", lambda: check_sql_injection_indicators(url)),
        ("XSS indicators",          lambda: check_xss_indicators(url, r)),
    ]

    for label, fn in steps:
        print(f"  Checking {label}...", end="", flush=True)
        try:
            findings = fn()
            result.findings.extend(findings)
            issues = [f for f in findings if f.severity not in ("pass", "info")]
            print(f"  {len(issues)} issue(s)" if issues else "  OK")
        except Exception as e:
            result.errors.append(f"{label}: {e}")
            print(f"  error: {e}")

    result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    return result


# ── HTML Report ────────────────────────────────────────────────────────────────

def severity_badge(severity: str) -> str:
    color = SEVERITY_COLORS.get(severity, "#6b7280")
    label = severity.upper()
    return f'<span class="badge" style="background:{color}">{label}</span>'


def build_html_report(result: ScanResult) -> str:
    findings = sorted(result.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))

    counts = {s: 0 for s in ("critical", "high", "medium", "low", "info", "pass")}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    issues = [f for f in findings if f.severity not in ("pass", "info")]
    total_issues = len(issues)
    score = max(0, 100 - (
        counts["critical"] * 25 + counts["high"] * 15 +
        counts["medium"] * 8 + counts["low"] * 3
    ))

    score_color = "#22c55e" if score >= 80 else "#eab308" if score >= 50 else "#ef4444"

    categories = {}
    for f in findings:
        categories.setdefault(f.category, []).append(f)

    def finding_html(f: Finding) -> str:
        detail_block = f'<div class="detail">{f.detail}</div>' if f.detail else ""
        fix_block = f'<div class="fix"><strong>Fix:</strong><pre>{f.fix}</pre></div>' if f.fix else ""
        return f"""
        <div class="finding {f.severity}">
          <div class="finding-header">
            {severity_badge(f.severity)}
            <span class="finding-title">{f.title}</span>
          </div>
          <div class="finding-desc">{f.description}</div>
          {detail_block}
          {fix_block}
        </div>"""

    cat_sections = ""
    for cat, cat_findings in sorted(categories.items()):
        cat_issues = [f for f in cat_findings if f.severity not in ("pass", "info")]
        cat_passes = [f for f in cat_findings if f.severity == "pass"]
        rows = "".join(finding_html(f) for f in cat_findings)
        indicator = f'<span style="color:#ef4444;font-weight:600">{len(cat_issues)} issue(s)</span>' if cat_issues else '<span style="color:#22c55e">✓ Clean</span>'
        cat_sections += f"""
        <div class="category">
          <div class="cat-header">
            <h3>{cat}</h3>
            <span>{indicator}</span>
          </div>
          {rows}
        </div>"""

    summary_cards = "".join(
        f'<div class="summary-card" style="border-top:3px solid {SEVERITY_COLORS[s]}">'
        f'<div class="card-count" style="color:{SEVERITY_COLORS[s]}">{counts[s]}</div>'
        f'<div class="card-label">{s.upper()}</div></div>'
        for s in ("critical", "high", "medium", "low", "info", "pass")
    )

    errors_html = ""
    if result.errors:
        errors_html = '<div class="errors"><strong>Errors during scan:</strong><ul>' + \
                      "".join(f"<li>{e}</li>" for e in result.errors) + "</ul></div>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WebSecScan Report — {result.url}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; background: #0f0f11; color: #e2e8f0; font-size: 14px; }}
  a {{ color: #60a5fa; }}
  .header {{ background: #18181b; border-bottom: 1px solid #27272a; padding: 24px 40px; }}
  .header h1 {{ font-size: 22px; font-weight: 700; color: #f8fafc; }}
  .header .meta {{ color: #71717a; font-size: 13px; margin-top: 6px; }}
  .header .meta span {{ margin-right: 20px; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 32px 24px; }}
  .score-bar {{ display:flex; align-items:center; gap:24px; background:#18181b;
                border:1px solid #27272a; border-radius:12px; padding:24px 32px; margin-bottom:28px; }}
  .score-circle {{ width:80px; height:80px; border-radius:50%; display:flex; align-items:center;
                   justify-content:center; font-size:26px; font-weight:700; flex-shrink:0;
                   border:4px solid {score_color}; color:{score_color}; }}
  .score-info h2 {{ font-size:18px; color:#f8fafc; }}
  .score-info p {{ color:#71717a; font-size:13px; margin-top:4px; }}
  .summary {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:32px; }}
  .summary-card {{ background:#18181b; border:1px solid #27272a; border-radius:10px;
                   padding:16px 20px; flex:1; min-width:100px; text-align:center; }}
  .card-count {{ font-size:28px; font-weight:700; }}
  .card-label {{ font-size:11px; color:#71717a; margin-top:4px; letter-spacing:.5px; }}
  .category {{ background:#18181b; border:1px solid #27272a; border-radius:10px;
               margin-bottom:20px; overflow:hidden; }}
  .cat-header {{ display:flex; justify-content:space-between; align-items:center;
                 padding:14px 20px; background:#1c1c1f; border-bottom:1px solid #27272a; }}
  .cat-header h3 {{ font-size:14px; font-weight:600; color:#f8fafc; }}
  .finding {{ padding:14px 20px; border-bottom:1px solid #27272a; }}
  .finding:last-child {{ border-bottom:none; }}
  .finding-header {{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }}
  .finding-title {{ font-weight:600; color:#f1f5f9; font-size:13px; }}
  .finding-desc {{ color:#94a3b8; font-size:13px; line-height:1.5; }}
  .detail {{ background:#0f0f11; border-radius:6px; padding:8px 12px; margin-top:8px;
             font-family:monospace; font-size:12px; color:#a5f3fc; white-space:pre-wrap; }}
  .fix {{ margin-top:10px; background:#0a1628; border-left:3px solid #3b82f6;
          border-radius:4px; padding:10px 14px; }}
  .fix strong {{ color:#93c5fd; font-size:12px; display:block; margin-bottom:4px; }}
  .fix pre {{ font-size:12px; color:#bfdbfe; white-space:pre-wrap; font-family:monospace; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px;
            font-weight:700; color:#fff; letter-spacing:.3px; flex-shrink:0; }}
  .errors {{ background:#1c1c1f; border:1px solid #ef444440; border-radius:8px;
             padding:16px; margin-bottom:24px; color:#fca5a5; }}
  .footer {{ text-align:center; color:#3f3f46; font-size:12px; padding:32px 0; }}
  h2 {{ font-size:16px; color:#f8fafc; margin-bottom:16px; }}
</style>
</head>
<body>
<div class="header">
  <h1>WebSecScan — Security Report</h1>
  <div class="meta">
    <span>URL: <strong style="color:#e2e8f0">{result.url}</strong></span>
    <span>Scanned: {result.scanned_at}</span>
    <span>Duration: {result.duration_ms / 1000:.1f}s</span>
    <span>Issues found: <strong style="color:#f97316">{total_issues}</strong></span>
  </div>
</div>
<div class="container">
  <div class="score-bar">
    <div class="score-circle">{score}</div>
    <div class="score-info">
      <h2>Security Score: {score}/100</h2>
      <p>{"Strong security posture" if score >= 80 else "Some issues need attention" if score >= 50 else "Multiple critical issues found — action required"}</p>
      <p style="margin-top:6px">{counts["critical"]} critical &bull; {counts["high"]} high &bull; {counts["medium"]} medium &bull; {counts["low"]} low</p>
    </div>
  </div>
  {errors_html}
  <h2>Check Summary</h2>
  <div class="summary">{summary_cards}</div>
  <h2>Detailed Findings</h2>
  {cat_sections}
</div>
<div class="footer">WebSecScan &bull; Generated {result.scanned_at} &bull; Not a substitute for a full penetration test</div>
</body>
</html>"""


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WebSecScan — automated website security checker")
    parser.add_argument("url", help="Target URL to scan (e.g. https://example.com)")
    parser.add_argument("--output", "-o", help="Output HTML report path", default=None)
    parser.add_argument("--json", "-j", action="store_true", help="Also output JSON results")
    args = parser.parse_args()

    result = run_scan(args.url)

    issues = [f for f in result.findings if f.severity not in ("pass", "info")]
    print(f"\n  Scan complete in {result.duration_ms / 1000:.1f}s — {len(issues)} issues found\n")

    for sev in ("critical", "high", "medium", "low"):
        these = [f for f in issues if f.severity == sev]
        if these:
            print(f"  [{sev.upper()}]")
            for f in these:
                print(f"    • {f.title}")
    print()

    html = build_html_report(result)
    out_path = args.output
    if not out_path:
        safe_host = re.sub(r"[^\w\-]", "_", urllib.parse.urlparse(args.url).netloc)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"security_report_{safe_host}_{ts}.html"

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"  Report saved: {out_path}\n")

    if args.json:
        json_path = out_path.replace(".html", ".json")
        data = {
            "url": result.url,
            "scanned_at": result.scanned_at,
            "duration_ms": result.duration_ms,
            "findings": [
                {"id": f.check_id, "title": f.title, "severity": f.severity,
                 "description": f.description, "category": f.category,
                 "detail": f.detail, "fix": f.fix}
                for f in result.findings
            ]
        }
        with open(json_path, "w") as jf:
            json.dump(data, jf, indent=2)
        print("  JSON saved: " + json_path)

    return 0 if not any(f.severity == "critical" for f in result.findings) else 1


if __name__ == "__main__":
    sys.exit(main())
