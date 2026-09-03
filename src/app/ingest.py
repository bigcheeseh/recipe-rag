"""Corpus ingestion. Run manually, never at request time."""

import re
from dataclasses import dataclass

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
