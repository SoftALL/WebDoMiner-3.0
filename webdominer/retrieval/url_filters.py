from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse, urldefrag


TRACKING_QUERY_PREFIXES = (
    "utm_",
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
)

LOW_VALUE_DOMAINS = {
    "zhihu.com",
    "www.zhihu.com",
    "zhidao.baidu.com",
    "stackoverflow.com",
    "superuser.com",
    "serverfault.com",
    "english.stackexchange.com",
    "ell.stackexchange.com",
    "quora.com",
    "www.quora.com",
    "ask.com",
}


def normalize_url(url: str) -> str:
    """
    Normalize a URL for stable deduplication.

    - remove fragments
    - lowercase scheme and netloc
    - remove default ports
    - remove common tracking query params
    - remove trailing slash from non-root paths
    """
    url, _ = urldefrag(url.strip())

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    filtered_query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered_key = key.lower()
        if lowered_key.startswith(TRACKING_QUERY_PREFIXES):
            continue
        if lowered_key in TRACKING_QUERY_PREFIXES:
            continue
        filtered_query_items.append((key, value))

    query = urlencode(filtered_query_items, doseq=True)

    if path != "/" and path.endswith("/"):
        path = path[:-1]

    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    return normalized


def is_low_value_domain(url: str) -> bool:
    """
    Return True if the URL belongs to a domain that is usually low-value for
    domain corpus generation from RS documents.
    """
    netloc = urlparse(url).netloc.lower()
    return netloc in LOW_VALUE_DOMAINS


def is_probably_html_url(
    url: str,
    allowed_schemes: tuple[str, ...],
    bad_extensions: tuple[str, ...],
    bad_url_patterns: tuple[str, ...],
) -> bool:
    """
    Return True if the URL is likely to point to an HTML content page.
    """
    if not url or not url.strip():
        return False

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in allowed_schemes:
        return False

    if not parsed.netloc:
        return False

    lowered_url = url.lower()
    lowered_path = parsed.path.lower()

    if any(lowered_path.endswith(ext) for ext in bad_extensions):
        return False

    if any(pattern in lowered_url for pattern in bad_url_patterns):
        return False

    if is_low_value_domain(url):
        return False

    return True


def get_url_domain(url: str) -> str:
    """
    Extract the normalized domain from a URL.
    """
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_same_domain(url_a: str, url_b: str) -> bool:
    """
    Return True if both URLs belong to the same domain.
    """
    return get_url_domain(url_a) == get_url_domain(url_b)