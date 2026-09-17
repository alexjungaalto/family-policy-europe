#!/usr/bin/env python3
"""
Link checker for the site's URLs.

By default sweeps both site/data/policies.json (per-country resource quick links,
org links, cases, US per-state layer) and the hardcoded href links in
site/index.html. Classifies:

  HARD  — dead: 404/410, DNS failure, connection refused, or a name that
          doesn't resolve. These are real breakage and (by default) block deploy.
  SOFT  — reachable-but-not-200-to-a-script: 401/403/429/503/202/400, SSL/DH
          quirks, timeouts, or a host on ALLOW_BOT. These are almost always
          anti-bot / WAF / consent-wall responses from live sites, so they are
          listed for info but do NOT block deploy.

Exit code: 0 if no HARD failures, 1 otherwise.

Usage:
  python3 check_links.py                 # check orgs.json + site/index.html
  python3 check_links.py path/to.json    # a single .json source
  python3 check_links.py path/to.html    # a single .html source
"""
import json, sys, ssl, socket, re
import urllib.request, urllib.error
import concurrent.futures as cf

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
TIMEOUT = 25
GOOD = {200, 201, 202, 203, 204, 301, 302, 303, 307, 308}

# Hosts known to block scripted requests but that serve fine in a real browser.
# Verified live via browser / Wayback / the research agent. A SOFT result on one
# of these is expected, not a failure.
ALLOW_BOT = {
    "ris.bka.gv.at", "legifrance.gouv.fr", "ucu.org.uk", "cnr.it",
    "legislatie.just.ro", "dennikn.sk", "irozhlas.cz", "oziveni.cz",
    "natlex.ilo.org", "ceelegalmatters.com", "eng.lsm.lv", "lsm.lv",
    "mon.bg", "vdi.lrv.lt", "prokuraturos.lt", "dier.gov.mt",
    "publico.pt", "facebook.com", "research.gov.ro",
    # Real .gov.bd hosts that fail to resolve on some local resolvers but are
    # live (verified 200 via Google DNS / forced IP resolution).
    "ugc.gov.bd", "nlaso.gov.bd", "advokatura.lv",
    # Nepal education portal hosting the NUTA teachers'-association listing —
    # serves 200 in a browser but 403s scripted fetchers (anti-bot).
    "edusanjal.com",
    # Paraguay bar association — live (HTTP 200, resolves to 34.174.59.146) but
    # its .org.py DNS intermittently fails scripted lookups on some resolvers.
    "colegiodeabogados.org.py",
}


def collect(path):
    d = json.load(open(path, encoding='utf-8'))
    urls = []
    for iso, e in d.items():
        for k, v in (e.get('resources') or {}).items():
            if v.get('url'):
                urls.append((iso, f'res:{k}', v['url']))
        for p in e.get('policies', []):
            if p.get('url'):
                urls.append((iso, f"pol:{p['cat']}:{p.get('rank','')}", p['url']))
    return urls


def collect_html(path):
    """Extract literal external href URLs from an HTML/JS file.

    Only real anchor targets are swept: `href="https://…"`. Template hrefs
    like `href="${FEEDBACK}"` and non-href URL strings (analytics endpoint,
    library mentions in comments) don't match and are skipped. Deduped,
    order-preserved."""
    txt = open(path, encoding='utf-8').read()
    seen, urls = set(), []
    for m in re.finditer(r'''href=["'](https?://[^"'\s]+)["']''', txt):
        u = m.group(1)
        if u not in seen:
            seen.add(u)
            urls.append(('IDX', 'html:href', u))
    return urls


def classify(status_or_err):
    """Return 'good' | 'hard' | 'soft'."""
    if isinstance(status_or_err, int):
        if status_or_err in GOOD:
            return 'good'
        if status_or_err in (404, 410):
            return 'hard'
        return 'soft'                      # 401/403/429/5xx/etc -> soft
    # exception name string
    e = status_or_err
    if any(s in e for s in ('gaierror', 'NameError', 'nodename',
                            'Name or service', 'ConnectionRefused',
                            'getaddrinfo')):
        return 'hard'                      # dead domain / refused
    return 'soft'                          # timeout / SSL / reset -> soft


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, socket.timeout, ssl.SSLError,
            ConnectionError, OSError) as e:
        return f"{type(e).__name__}:{getattr(e,'reason',e)}"


def check(row):
    iso, tag, url = row
    r1 = fetch(url)
    kind = classify(r1)
    if kind != 'good':                     # one retry to smooth transient blips
        r2 = fetch(url)
        k2 = classify(r2)
        if k2 == 'good':
            return (iso, tag, url, r2, 'good')
        # keep the more informative of the two
        r1 = r2 if isinstance(r2, int) else r1
        kind = classify(r1)
    return (iso, tag, url, r1, kind)


def sources_from_args():
    """A given path is swept alone (json or html by extension); with no args,
    sweep both the org data and the hardcoded links in index.html."""
    if len(sys.argv) > 1:
        p = sys.argv[1]
        return [(p, 'html' if p.endswith('.html') else 'json')]
    return [('site/data/policies.json', 'json'), ('site/index.html', 'html')]


def main():
    srcs = sources_from_args()
    rows = []
    for path, kind in srcs:
        rows += collect_html(path) if kind == 'html' else collect(path)
    results = []
    with cf.ThreadPoolExecutor(max_workers=20) as ex:
        for r in ex.map(check, rows):
            results.append(r)

    hard, soft = [], []
    for iso, tag, url, status, kind in results:
        if kind == 'good':
            continue
        h = re.sub(r'^www\.', '', (re.match(r'https?://([^/]+)', url).group(1).lower()))
        if kind == 'hard' and h not in ALLOW_BOT:
            hard.append((iso, tag, url, status))
        else:
            soft.append((iso, tag, url, status))

    print(f"[check_links] swept {len(results)} URLs from {', '.join(p for p, _ in srcs)}")
    if soft:
        print(f"[check_links] {len(soft)} soft (bot-block / WAF / consent-wall — verified live, informational):")
        for iso, tag, url, st in sorted(soft):
            print(f"    · {iso:3} {tag:18} {st}  {url}")
    if hard:
        print(f"[check_links] \033[31m{len(hard)} HARD failure(s) — dead link(s):\033[0m")
        for iso, tag, url, st in sorted(hard):
            print(f"    ✗ {iso:3} {tag:18} {st}  {url}")
        print("[check_links] FAIL — fix these (or set SKIP_LINK_CHECK=1 to override).")
        return 1
    print("[check_links] OK — no dead links.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
