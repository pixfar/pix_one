"""
Domain Service for PixOne SaaS Platform
Handles subdomain availability, validation, suggestions, and reservation.

Pattern: every tenant gets  <subdomain>.<base_domain>
Example: pixfar.pixone.com
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

import frappe
from frappe import _
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Hard-coded fallback reserved list (PixOne System Settings can extend this)
_BUILTIN_RESERVED = frozenset([
    # Infrastructure / well-known
    "www", "api", "app", "apps", "m", "mobile", "wap",
    # Mail
    "mail", "smtp", "imap", "pop", "pop3", "mx", "email",
    # Network services
    "ftp", "ssh", "sftp", "vpn", "proxy", "relay", "ns", "ns1", "ns2",
    # CDN / static
    "cdn", "static", "assets", "media", "files", "uploads", "img", "images",
    # Product / brand
    "pixone", "pix", "pix_one", "frappe", "erpnext", "pixfar",
    # Auth / identity
    "auth", "oauth", "sso", "saml", "login", "logout", "register",
    "signup", "signin", "account", "accounts",
    # Portals
    "admin", "administrator", "root", "superuser", "portal",
    "console", "control", "panel", "cp", "management",
    # Dashboard / app
    "dashboard", "home", "index",
    # Developer
    "dev", "develop", "development", "staging", "stage", "test",
    "testing", "qa", "uat", "sandbox", "demo", "preview",
    # Support
    "support", "help", "helpdesk", "docs", "documentation", "kb",
    "knowledgebase", "wiki", "forum", "community",
    # Marketing
    "blog", "news", "press", "marketing", "landing",
    # Status / monitoring
    "status", "health", "ping", "monitor", "metrics",
    # Billing
    "billing", "payment", "payments", "invoice", "invoices",
    "checkout", "cart", "shop", "store", "marketplace",
    # System
    "system", "internal", "intranet", "localhost", "local",
    # Legal
    "terms", "privacy", "legal", "gdpr", "compliance",
])

_SUBDOMAIN_RE = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$')


def _get_settings() -> Tuple[str, int, frozenset]:
    """Return (base_domain, max_length, reserved_set) from PixOne System Settings."""
    try:
        s = frappe.get_cached_doc("PixOne System Settings")
        base_domain = (s.base_domain or "pixone.com").strip().lower().rstrip(".")
        max_len = int(s.max_subdomain_length or 63)
        extra = frozenset(
            p.strip().lower()
            for p in (s.reserved_subdomains or "").split(",")
            if p.strip()
        )
    except Exception:
        base_domain = "pixone.com"
        max_len = 63
        extra = frozenset()

    return base_domain, max_len, _BUILTIN_RESERVED | extra


def _slugify(text: str) -> str:
    """
    Convert any business name to a valid subdomain slug.
    'Pixfar Ltd.'  →  'pixfar-ltd'
    'أكمي'        →  ascii transliteration or empty
    """
    # Normalize unicode (e.g. accented chars → base + diacritic)
    text = unicodedata.normalize("NFKD", text)
    # Keep only ASCII
    text = text.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    text = text.lower()
    # Replace anything that's not alphanum/space/hyphen with hyphen
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    # Collapse whitespace/hyphens into a single hyphen
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    return text


def _is_taken(subdomain: str) -> bool:
    """Return True if a SaaS Company record already holds this subdomain."""
    return bool(frappe.db.exists("SaaS Company", {
        "subdomain": subdomain,
        "status": ["not in", ["Deleted", "Failed"]]
    }))


def _generate_suggestions(base_slug: str, n: int = 5) -> List[str]:
    """
    Generate up to `n` available subdomain suggestions based on base_slug.
    Strategy:
      1. base_slug itself (if short enough and not already taken — caller guarantees it IS taken)
      2. base_slug + numeric suffix 1..99
      3. base_slug + short qualifiers: hq, erp, app, go, io
    """
    _, max_len, reserved = _get_settings()
    suggestions = []

    qualifiers = ["hq", "erp", "app", "go", "io", "hub", "corp", "biz", "bd", "01"]
    candidates = []

    # Numeric suffix first (most neutral)
    for i in range(1, 100):
        candidates.append(f"{base_slug}{i}")

    # Qualifier suffix
    for q in qualifiers:
        candidate = f"{base_slug}-{q}"
        if len(candidate) <= max_len:
            candidates.append(candidate)

    for candidate in candidates:
        if len(suggestions) >= n:
            break
        if (
            len(candidate) >= 3
            and len(candidate) <= max_len
            and bool(_SUBDOMAIN_RE.match(candidate))
            and candidate not in reserved
            and not _is_taken(candidate)
        ):
            suggestions.append(candidate)

    return suggestions


# ---------------------------------------------------------------------------
# Public API endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
@handle_exceptions
def check_subdomain(subdomain: str) -> Dict[str, Any]:
    """
    Check whether a subdomain is available on the platform.

    Args:
        subdomain: The requested subdomain slug (e.g. "pixfar")

    Returns:
        {
            "available": true|false,
            "subdomain": "pixfar",
            "full_domain": "pixfar.pixone.com",
            "reason": null | "taken" | "reserved" | "invalid_format" | "too_short" | "too_long",
            "suggestions": ["pixfar1", "pixfar-hq", ...]   # only when unavailable
        }
    """
    base_domain, max_len, reserved = _get_settings()

    # Normalise input
    slug = (subdomain or "").strip().lower()

    # ── Validation ──────────────────────────────────────────────────────────
    if len(slug) < 3:
        return ResponseFormatter.success(data={
            "available": False,
            "subdomain": slug,
            "full_domain": f"{slug}.{base_domain}",
            "reason": "too_short",
            "message": _("Subdomain must be at least 3 characters."),
            "suggestions": []
        })

    if len(slug) > max_len:
        return ResponseFormatter.success(data={
            "available": False,
            "subdomain": slug,
            "full_domain": f"{slug}.{base_domain}",
            "reason": "too_long",
            "message": _("Subdomain cannot exceed {0} characters.").format(max_len),
            "suggestions": []
        })

    if not _SUBDOMAIN_RE.match(slug):
        return ResponseFormatter.success(data={
            "available": False,
            "subdomain": slug,
            "full_domain": f"{slug}.{base_domain}",
            "reason": "invalid_format",
            "message": _(
                "Subdomain may only contain lowercase letters, numbers, and hyphens. "
                "It must start and end with a letter or number."
            ),
            "suggestions": _generate_suggestions(_slugify(subdomain))
        })

    # ── Reserved check ───────────────────────────────────────────────────────
    if slug in reserved:
        return ResponseFormatter.success(data={
            "available": False,
            "subdomain": slug,
            "full_domain": f"{slug}.{base_domain}",
            "reason": "reserved",
            "message": _("'{0}' is a reserved name and cannot be registered.").format(slug),
            "suggestions": _generate_suggestions(slug)
        })

    # ── Uniqueness check ─────────────────────────────────────────────────────
    if _is_taken(slug):
        return ResponseFormatter.success(data={
            "available": False,
            "subdomain": slug,
            "full_domain": f"{slug}.{base_domain}",
            "reason": "taken",
            "message": _("'{0}.{1}' is already taken.").format(slug, base_domain),
            "suggestions": _generate_suggestions(slug)
        })

    # ── Available ────────────────────────────────────────────────────────────
    return ResponseFormatter.success(data={
        "available": True,
        "subdomain": slug,
        "full_domain": f"{slug}.{base_domain}",
        "reason": None,
        "message": _("'{0}.{1}' is available!").format(slug, base_domain),
        "suggestions": []
    })


@frappe.whitelist(allow_guest=True)
@handle_exceptions
def suggest_subdomains(business_name: str, count: int = 5) -> Dict[str, Any]:
    """
    Generate available subdomain suggestions from a business name.

    Args:
        business_name: Raw business name (e.g. "Pixfar Technologies Ltd.")
        count: How many suggestions to return (max 10)

    Returns:
        {
            "base_slug": "pixfar-technologies-ltd",
            "suggestions": [
                { "subdomain": "pixfar-technologies-ltd", "full_domain": "...", "available": true },
                ...
            ]
        }
    """
    base_domain, max_len, reserved = _get_settings()
    count = min(int(count or 5), 10)

    slug = _slugify(business_name or "")

    # Truncate slug to fit max_len
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")

    if not slug or len(slug) < 2:
        return ResponseFormatter.validation_error(
            _("Could not generate a valid subdomain from the given name. "
              "Please enter a name using English letters.")
        )

    # Collect candidates: exact slug first, then variations
    candidates = []
    if len(slug) >= 3 and _SUBDOMAIN_RE.match(slug) and slug not in reserved and not _is_taken(slug):
        candidates.append(slug)

    candidates.extend(_generate_suggestions(slug, n=count + 2))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    result = [
        {"subdomain": s, "full_domain": f"{s}.{base_domain}", "available": True}
        for s in unique[:count]
    ]

    return ResponseFormatter.success(data={
        "base_slug": slug,
        "base_domain": base_domain,
        "suggestions": result
    })


@frappe.whitelist(allow_guest=True)
@handle_exceptions
def get_base_domain() -> Dict[str, Any]:
    """
    Return the platform's base domain (safe for unauthenticated callers).

    Returns:
        { "base_domain": "pixone.com" }
    """
    base_domain, max_len, _ = _get_settings()
    return ResponseFormatter.success(data={
        "base_domain": base_domain,
        "max_subdomain_length": max_len,
        "example": f"yourbusiness.{base_domain}"
    })
