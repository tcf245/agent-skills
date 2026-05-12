#!/usr/bin/env python3
"""
Search for Quark pan links via tvso.uk → Google → fallback sites.

Usage:
  python search_quark.py "影视名称"

Outputs JSON array of candidates, sorted by quality_score desc.
Each item: {title, url, quality_score, is_tc, valid, pub_date}
"""
import sys, json, re, time
import urllib.request, urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
QUARK_RE = re.compile(r"https://pan\.quark\.cn/s/([a-zA-Z0-9]+)")


def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[fetch error] {url}: {e}", file=sys.stderr)
        return ""


def quality_score(text):
    t = text.lower()
    if any(x in t for x in ["4k", "2160p", "uhd"]):
        return 3
    if any(x in t for x in ["原盘", "blu-ray", "bluray"]):
        return 2
    if any(x in t for x in ["1080p", "1080i"]):
        return 1
    return 0


def is_tc(text):
    t = text.lower()
    return any(x in t for x in ["tc版", "枪版", "tc.avi", "tcam", " tc "])


def check_valid(url, timeout=6):
    """HEAD request to check if quark link is still alive."""
    req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 400
    except Exception:
        return False


def search_tvso(keyword):
    """Search tvso.uk for quark links."""
    candidates = []
    encoded = urllib.parse.quote(keyword)
    url = f"https://tvso.uk/s?keyword={encoded}"
    html = fetch(url)
    if not html:
        return candidates

    # Find article links that go to quark
    articles = re.findall(r'href="(https://tvso\.uk/d/[^"]+)"[^>]*>([^<]+)<', html)
    # Also look for direct quark links
    direct = QUARK_RE.findall(html)
    for code in direct[:5]:
        q_url = f"https://pan.quark.cn/s/{code}"
        candidates.append({
            "title": keyword,
            "url": q_url,
            "quality_score": 0,
            "is_tc": False,
            "valid": None,
            "pub_date": None,
            "source": "tvso_direct"
        })

    # Fetch each article page
    for article_url, title in articles[:5]:
        art_html = fetch(article_url)
        if not art_html:
            continue
        codes = QUARK_RE.findall(art_html)
        pub = re.search(r'(\d{4}-\d{2}-\d{2})', art_html)
        pub_date = pub.group(1) if pub else None
        for code in codes[:3]:
            q_url = f"https://pan.quark.cn/s/{code}"
            candidates.append({
                "title": title.strip(),
                "url": q_url,
                "quality_score": quality_score(title + art_html[:500]),
                "is_tc": is_tc(title + art_html[:500]),
                "valid": None,
                "pub_date": pub_date,
                "source": "tvso_article"
            })

    return candidates


def search_google(keyword, site_hint="pan.quark.cn/s"):
    """Google search for quark links."""
    candidates = []
    query = urllib.parse.quote(f"{keyword} {site_hint}")
    url = f"https://www.google.com/search?q={query}&num=20&hl=zh-CN"
    html = fetch(url)
    if not html:
        return candidates

    codes = QUARK_RE.findall(html)
    titles = re.findall(r'<h3[^>]*>([^<]+)</h3>', html)

    for i, code in enumerate(codes[:10]):
        q_url = f"https://pan.quark.cn/s/{code}"
        title = titles[i] if i < len(titles) else keyword
        # Strip HTML tags from title
        title = re.sub(r'<[^>]+>', '', title)
        candidates.append({
            "title": title.strip(),
            "url": q_url,
            "quality_score": quality_score(title),
            "is_tc": is_tc(title),
            "valid": None,
            "pub_date": None,
            "source": "google"
        })

    return candidates


def deduplicate(candidates):
    seen = set()
    result = []
    for c in candidates:
        if c["url"] not in seen:
            seen.add(c["url"])
            result.append(c)
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: search_quark.py '影视名称'", file=sys.stderr)
        sys.exit(1)

    keyword = sys.argv[1]
    print(f"[search] Searching for: {keyword}", file=sys.stderr)

    # Step 1: tvso.uk
    candidates = search_tvso(keyword)
    print(f"[tvso] Found {len(candidates)} candidates", file=sys.stderr)

    # Step 2: Google fallback if < 3 results
    if len(candidates) < 3:
        print("[search] Falling back to Google...", file=sys.stderr)
        candidates += search_google(keyword)
        candidates = deduplicate(candidates)

    # Step 3: Validate top 3 non-TC links
    validated = 0
    for c in sorted(candidates, key=lambda x: -x["quality_score"]):
        if validated >= 3:
            break
        if c["is_tc"]:
            c["valid"] = False
            continue
        print(f"[validate] {c['url']}", file=sys.stderr)
        c["valid"] = check_valid(c["url"])
        validated += 1
        time.sleep(0.5)

    # Sort: valid first, then by quality_score desc, then by pub_date desc
    def sort_key(c):
        valid_score = 1 if c["valid"] else (0 if c["valid"] is None else -1)
        date_score = c["pub_date"] or "0000-00-00"
        return (-valid_score, -c["quality_score"], -ord(date_score[0]) if date_score else 0)

    candidates.sort(key=lambda c: (
        -(1 if c["valid"] else 0),
        -c["quality_score"],
        -(c["pub_date"] or "0")
    ))

    print(json.dumps(candidates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
