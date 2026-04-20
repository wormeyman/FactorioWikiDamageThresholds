# Wiki Fetch Tool Design

**Date:** 2026-04-20
**Script:** `factorio_wiki_fetch.py`

## Purpose

Fetch a Factorio Wiki page via the MediaWiki `action=parse` API and save the raw JSON response to `WikiArticles/`. Replaces manual browser-based API calls used to produce files like `enemies_wiki.json` and `Technologies.json`.

## CLI Interface

```
python3 factorio_wiki_fetch.py <url-or-page-name> [--output FILENAME]
```

- `url-or-page-name` - full URL or bare page name (both accepted)
- `--output FILENAME` - override output filename only; path is always `WikiArticles/`
- Default filename: `<page_name>.json`

## Input Resolution

If the argument starts with `http`, the page name is extracted from the URL path (leading `/` stripped). Otherwise the argument is used as-is.

Examples:
- `https://wiki.factorio.com/Mining_productivity_(research)` -> `Mining_productivity_(research)`
- `Mining_productivity_(research)` -> `Mining_productivity_(research)`

## API Call

```
GET https://wiki.factorio.com/api.php?action=parse&page=<PAGE>&prop=wikitext&format=json
```

Uses `urllib.request` (stdlib only). Response is written as pretty-printed JSON (`indent=2`).

## Output Structure

The saved file is the raw MediaWiki API response:

```json
{
  "parse": {
    "title": "Page Title",
    "pageid": 123,
    "wikitext": {
      "*": "...raw wikitext..."
    }
  }
}
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Non-200 HTTP response | Print descriptive error to stderr, exit 1 |
| MediaWiki `error` field in response | Print error code and info to stderr, exit 1 |
| Output file already exists | Overwrite silently |

## Implementation Notes

- Stdlib only: `argparse`, `json`, `pathlib`, `sys`, `urllib.parse`, `urllib.request`
- Type hints on all function signatures
- Private helpers prefixed with `_`
- `User-Agent` header set to avoid API rejections
