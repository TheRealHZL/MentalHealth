"""
Input Sanitization Module

Provides utilities to sanitize user input and prevent XSS, injection attacks.
"""

import bleach
from typing import Optional, List
import re


# Allowed HTML tags for user-generated content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title']
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(text: str, strip: bool = True) -> str:
    """
    Sanitize HTML content to prevent XSS attacks

    Args:
        text: Raw HTML input
        strip: If True, strip all HTML. If False, allow safe tags.

    Returns:
        Sanitized HTML
    """
    if not text:
        return ""

    if strip:
        # Remove ALL HTML tags
        return bleach.clean(text, tags=[], strip=True)
    else:
        # Allow only safe HTML tags
        return bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )


def sanitize_text(text: str) -> str:
    """
    Sanitize plain text input (strip all HTML)

    Use this for fields that should NEVER contain HTML:
    - User names
    - Titles
    - Short descriptions
    """
    return sanitize_html(text, strip=True)


def sanitize_rich_text(text: str) -> str:
    """
    Sanitize rich text input (allow safe HTML)

    Use this for fields that may contain formatting:
    - Mood notes
    - Dream descriptions
    - Therapy notes
    """
    return sanitize_html(text, strip=False)


def sanitize_email(email: str) -> str:
    """
    Sanitize email address

    - Convert to lowercase
    - Strip whitespace
    - Remove HTML
    """
    if not email:
        return ""

    # Strip HTML
    email = sanitize_text(email)

    # Lowercase and strip
    email = email.lower().strip()

    return email


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize URL to prevent javascript: and data: URLs

    Returns None if URL is invalid/dangerous
    """
    if not url:
        return None

    # Strip HTML first
    url = sanitize_text(url)
    url = url.strip()

    # Block dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
    for protocol in dangerous_protocols:
        if url.lower().startswith(protocol):
            return None

    # Only allow http/https
    if not url.startswith(('http://', 'https://', '/')):
        return None

    return url


def sanitize_sql_like(text: str) -> str:
    """
    Escape special characters in SQL LIKE queries

    Prevents SQL injection in LIKE clauses
    """
    if not text:
        return ""

    # Escape special SQL LIKE characters
    text = text.replace('\\', '\\\\')  # Escape backslash first!
    text = text.replace('%', '\\%')
    text = text.replace('_', '\\_')

    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal

    - Remove path separators
    - Remove null bytes
    - Limit length
    """
    if not filename:
        return "unnamed"

    # Remove HTML
    filename = sanitize_text(filename)

    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')

    # Only allow alphanumeric, dash, underscore, dot
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 255 - len(ext) - 1
        filename = name[:max_name_len] + '.' + ext if ext else name[:255]

    return filename or "unnamed"


def detect_suspicious_patterns(text: str) -> List[str]:
    """
    Detect potentially malicious patterns in user input

    Returns list of detected suspicious patterns (for logging/alerting)
    """
    if not text:
        return []

    suspicious = []

    # SQL injection attempts
    sql_patterns = [
        r"(\bor\b|\band\b).+?[=<>]",  # OR 1=1, AND 1=1
        r";\s*drop\s+table",  # ; DROP TABLE
        r";\s*delete\s+from",  # ; DELETE FROM
        r"union\s+select",  # UNION SELECT
        r"exec(\s|\()+",  # EXEC(
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            suspicious.append(f"SQL injection pattern: {pattern}")

    # XSS attempts
    xss_patterns = [
        r"<script",  # <script> tags
        r"javascript:",  # javascript: protocol
        r"on\w+\s*=",  # onclick=, onerror=, etc.
        r"<iframe",  # <iframe> tags
    ]

    for pattern in xss_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            suspicious.append(f"XSS pattern: {pattern}")

    # Path traversal
    if "../" in text or "..
" in text:
        suspicious.append("Path traversal attempt")

    return suspicious
