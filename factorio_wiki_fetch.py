#!/usr/bin/env python3
"""
Fetch a Factorio Wiki page via the MediaWiki parse API and save it as JSON.

Usage:
    python3 factorio_wiki_fetch.py <url-or-page-name> [--output FILENAME]

Arguments:
    url-or-page-name  Full URL (https://wiki.factorio.com/Page_Name) or bare
                      page name (Page_Name). URL and bare name are both accepted.
    --output FILENAME Override the output filename (default: <page_name>.json).
                      Output always goes to WikiArticles/.
"""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

WIKI_API = "https://wiki.factorio.com/api.php"
OUTPUT_DIR = pathlib.Path(__file__).parent / "WikiArticles"


def _resolve_page_name(arg: str) -> str:
    if arg.startswith(("http://", "https://")):
        parsed = urllib.parse.urlparse(arg)
        return parsed.path.removeprefix("/")
    return arg


def _fetch_wikitext(page: str) -> dict:
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json",
    })
    url = f"{WIKI_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "factorio-wiki-fetch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        print(f"Error: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Error: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: response was not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a Factorio Wiki page and save the MediaWiki API response as JSON."
    )
    parser.add_argument(
        "page",
        metavar="url-or-page-name",
        help="Full wiki URL or bare page name.",
    )
    parser.add_argument(
        "--output",
        metavar="FILENAME",
        help="Output filename (default: <page_name>.json). Saved to WikiArticles/.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    page_name = _resolve_page_name(args.page)

    data = _fetch_wikitext(page_name)

    if "error" in data:
        err = data["error"]
        print(f"Error: MediaWiki API error: {err.get('code', '?')}: {err.get('info', err)}", file=sys.stderr)
        sys.exit(1)

    filename = pathlib.Path(args.output).name if args.output else f"{page_name.split('/')[-1]}.json"
    out_path = OUTPUT_DIR / filename
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
