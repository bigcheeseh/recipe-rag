"""Corpus ingestion. Run manually, never at request time."""

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, Tag

from app.models import Recipe


@dataclass
class Rejected:
    title: str
    reason: str


def slugify(title: str) -> str:
    title = title.removeprefix("Cookbook:")
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _classes(tag: Tag) -> list[str]:
    c = tag.get("class")
    return list(c) if isinstance(c, list) else ([c] if c else [])


def _section(soup: BeautifulSoup, heading_id: str) -> list[Tag]:
    """Block elements between the h2 with this id and the next h2."""
    h = soup.find("h2", id=heading_id)
    if not isinstance(h, Tag):
        return []
    # Modern MediaWiki wraps headings: <div class="mw-heading mw-heading2"><h2>...</h2></div>
    start = h.parent if h.parent is not None and "mw-heading" in _classes(h.parent) else h
    out: list[Tag] = []
    for sib in start.next_siblings:
        if not isinstance(sib, Tag):
            continue
        if sib.name == "h2" or "mw-heading2" in _classes(sib):
            break
        out.append(sib)
    return out


def _list_items(blocks: list[Tag]) -> list[str]:
    items: list[str] = []
    for b in blocks:
        for li in b.find_all("li"):
            for sub in li.find_all(["ul", "ol"]):
                sub.extract()  # nested lists become their own items
            text = _clean(li.get_text(" "))
            if text:
                items.append(text)
        for tr in b.find_all("tr"):  # some pages tabulate ingredients: one row = one item
            cells = [_clean(td.get_text(" ")) for td in tr.find_all("td")]
            if any(cells):
                items.append(", ".join(c for c in cells if c))
    return items


def _paragraphs(blocks: list[Tag]) -> list[str]:
    return [t for b in blocks if b.name == "p" and (t := _clean(b.get_text(" ")))]


def _infobox(soup: BeautifulSoup) -> dict[str, str]:
    box = soup.find("table", class_="infobox")
    if not isinstance(box, Tag):
        return {}
    rows = {}
    for tr in box.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) == 2:
            rows[_clean(cells[0].get_text(" "))] = _clean(cells[1].get_text(" "))
    return rows


def parse_recipe(html: str, title: str, url: str, revid: int) -> Recipe | Rejected:
    soup = BeautifulSoup(html, "html.parser")
    for junk in soup.select(".mw-editsection, sup.reference, style"):
        junk.decompose()

    ing_blocks = _section(soup, "Ingredients")
    if not ing_blocks:
        return Rejected(title, "no Ingredients section")
    ingredients = _list_items(ing_blocks)
    if not ingredients:
        return Rejected(title, "Ingredients section has no list items")

    proc_blocks = _section(soup, "Procedure")
    if not proc_blocks:
        return Rejected(title, "no Procedure section")
    steps = _list_items(proc_blocks) or _paragraphs(proc_blocks)
    if not steps:
        return Rejected(title, "Procedure section has no steps")

    return Recipe(
        id=slugify(title),
        title=title.removeprefix("Cookbook:"),
        url=url,
        revid=revid,
        ingredients=ingredients,
        steps=steps,
        infobox=_infobox(soup),
    )


# --- fetching ---------------------------------------------------------------

API = "https://en.wikibooks.org/w/api.php"
USER_AGENT = "recipe-rag-takehome/0.1 (https://github.com/bigcheeseh; eugenevoronkov1@gmail.com)"
MIN_INTERVAL_S = 0.1


class Fetcher:
    """MediaWiki API client with disk cache and a >=100 ms gap between requests."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30)
        self._last = 0.0

    def _get(self, **params: str | int) -> dict:
        wait = MIN_INTERVAL_S - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        r = self.client.get(API, params={"format": "json", "formatversion": 2, **params})
        self._last = time.monotonic()
        r.raise_for_status()
        return r.json()

    def list_category(self, category: str, limit: int) -> list[str]:
        data = self._get(
            action="query", list="categorymembers", cmtitle=category, cmlimit=limit, cmnamespace=102
        )
        return [m["title"] for m in data["query"]["categorymembers"]]

    def fetch_page(self, title: str) -> dict | None:
        """Return {title, html, revid} for the page, following redirects. None if missing."""
        cached = self.cache_dir / f"{slugify(title)}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))
        data = self._get(action="parse", page=title, prop="text|revid", redirects=1)
        if "error" in data:
            return None
        p = data["parse"]
        page = {"title": p["title"], "html": p["text"], "revid": p["revid"]}
        cached.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
        return page


def page_url(title: str) -> str:
    return "https://en.wikibooks.org/wiki/" + title.replace(" ", "_")


def read_titles(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


# --- entry point ------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Fetch, parse and enrich the recipe corpus.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--titles", type=Path, help="file with one Cookbook: title per line")
    src.add_argument("--category", help="e.g. Category:Recipes")
    ap.add_argument("--limit", type=int, default=100, help="max pages when using --category")
    ap.add_argument("--out", type=Path, default=Path("data"))
    args = ap.parse_args(argv)

    fetcher = Fetcher(args.out / "html_cache")
    if args.titles:
        titles = read_titles(args.titles)
    else:
        titles = fetcher.list_category(args.category, args.limit)

    accepted: list[Recipe] = []
    rejected: list[Rejected] = []
    for t in titles:
        page = fetcher.fetch_page(t)
        if page is None:
            rejected.append(Rejected(t, "page not found"))
            continue
        r = parse_recipe(page["html"], page["title"], page_url(page["title"]), page["revid"])
        if isinstance(r, Recipe):
            accepted.append(r)
            print(f"ok      {t}")
        else:
            rejected.append(r)
            print(f"reject  {t} ({r.reason})")

    manifest = {
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source": str(args.titles or args.category),
        "accepted": [{"id": r.id, "title": r.title, "revid": r.revid} for r in accepted],
        "rejected": [{"title": r.title, "reason": r.reason} for r in rejected],
    }
    corpus = json.dumps([r.model_dump() for r in accepted], indent=1, ensure_ascii=False)
    (args.out / "corpus.json").write_text(corpus, encoding="utf-8")
    (args.out / "ingest_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"\naccepted {len(accepted)}, rejected {len(rejected)}")


if __name__ == "__main__":
    main()
