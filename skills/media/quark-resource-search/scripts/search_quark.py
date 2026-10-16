#!/usr/bin/env python3
"""
Search for Quark pan links via tvso.uk → Google → fallback sites.

Usage:
  python search_quark.py "影视名称"
  python search_quark.py "影视名称" --want "Dune: Part Two (2024), 4K, Chinese subs" --top 5

Outputs JSON array of candidates: valid first, then Jev match score (with --want),
then quality_score, then newest pub_date.
Each item: {title, url, quality_score, is_tc, valid, pub_date, source, snippet[, jev_score, jev_conf]}

--want sends every candidate's title/snippet to Jev (`jev rank`) so link validation and
the final pick focus on what actually matches; without it, keyword quality_score is used.
"""
import sys, json, re, time, argparse, subprocess
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


def page_text(html, limit=300):
    """Visible text of a page, collapsed, for Jev to judge a candidate."""
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()[:limit]


JEV_LEVELS = [
    "A different title, a different year or season than wanted, or a camera/TC rip",
    "The wanted title, but low or unknown picture quality, or only part of what was wanted",
    "The wanted title in 1080p, complete",
    "The wanted title in 4K/UHD, remux or original disc, complete",
]


def rank_with_jev(candidates, want, runner=subprocess.run):
    """Attach jev_score (0-3, see JEV_LEVELS) to each candidate. On any failure, leave them unscored."""
    items = [{"title": c["title"], "snippet": c.get("snippet", ""), "source": c["source"]}
             for c in candidates]
    cmd = ["jev", "rank", "-c", "What we want: " + want,
           "-q", "How well does this Quark share link (title and page snippet) match what we want?",
           "-l", *JEV_LEVELS]
    try:
        r = runner(cmd, input=json.dumps(items, ensure_ascii=False), capture_output=True,
                   text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip()[-300:])
        for line in r.stdout.splitlines():
            row = json.loads(line)
            candidates[row["i"]]["jev_score"] = row["score"]
            candidates[row["i"]]["jev_conf"] = row["conf"]
        print(f"[jev] {r.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"[jev] skipped ({e}); falling back to keyword quality_score", file=sys.stderr)


def validate(candidates, check=check_valid, limit=3, pause=0.5):
    """HEAD-check the top `limit` plausible candidates; TC rips and Jev-rejected titles are marked invalid."""
    order = sorted(candidates, key=lambda c: (-c.get("jev_score", 0), -c["quality_score"]))
    checked = 0
    for c in order:
        if c["is_tc"] or c.get("jev_score", 1) < 1:
            c["valid"] = False
            continue
        if checked >= limit:
            break
        print(f"[validate] {c['url']}", file=sys.stderr)
        c["valid"] = check(c["url"])
        checked += 1
        time.sleep(pause)


def normalize_candidates(rows):
    """Turn externally collected rows ({title, url, snippet?, pub_date?}, e.g. from a browser) into candidates."""
    out = []
    for r in rows:
        if not QUARK_RE.search(r.get("url") or ""):
            continue
        text = (r.get("title") or "") + " " + (r.get("snippet") or "")
        out.append({"title": r.get("title") or "", "url": r["url"], "quality_score": quality_score(text),
                    "is_tc": is_tc(text), "valid": None, "pub_date": r.get("pub_date"),
                    "source": "external", "snippet": r.get("snippet") or ""})
    return out


def sort_candidates(candidates):
    """Valid first, then Jev match, then keyword quality, then newest pub_date."""
    candidates.sort(key=lambda c: (c["pub_date"] or "0000-00-00"), reverse=True)
    candidates.sort(key=lambda c: (-(1 if c["valid"] else 0), -c.get("jev_score", 0),
                                   -c["quality_score"]))
    return candidates


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
            "source": "tvso_direct",
            "snippet": ""
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
                "source": "tvso_article",
                "snippet": page_text(art_html)
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
            "source": "google",
            "snippet": ""
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
    ap = argparse.ArgumentParser(description="Search Quark share links")
    ap.add_argument("keyword", nargs="?", help="影视名称")
    ap.add_argument("--want", help="what we want, in words (title, year, season, quality); enables Jev ranking")
    ap.add_argument("--top", type=int, help="print only the best N candidates")
    ap.add_argument("--candidates", help="JSON file of rows collected elsewhere (e.g. browser); skips scraping")
    args = ap.parse_args()
    if not args.keyword and not args.candidates:
        ap.error("give a keyword or --candidates FILE")

    if args.candidates:
        with open(args.candidates) as f:
            candidates = normalize_candidates(json.load(f))
        print(f"[external] Loaded {len(candidates)} candidates", file=sys.stderr)
    else:
        keyword = args.keyword
        print(f"[search] Searching for: {keyword}", file=sys.stderr)
        # Step 1: tvso.uk
        candidates = search_tvso(keyword)
        print(f"[tvso] Found {len(candidates)} candidates", file=sys.stderr)

    # Step 2: Google fallback if < 3 results
    if not args.candidates and len(candidates) < 3:
        print("[search] Falling back to Google...", file=sys.stderr)
        candidates += search_google(keyword)
        candidates = deduplicate(candidates)

    # Step 3: Jev judges which candidates match what we want
    if args.want and candidates:
        rank_with_jev(candidates, args.want)

    # Step 4: Validate the top 3 plausible links
    validate(candidates)

    sort_candidates(candidates)
    if args.top:
        candidates = candidates[:args.top]
    print(json.dumps(candidates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
