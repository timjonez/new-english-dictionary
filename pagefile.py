#!/usr/bin/env python3
"""Parse and check one NED page file. See SPEC.md.

  python3 pagefile.py text/01-AB/0134.md
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

STATUSES = ("draft", "ok", "partial", "unreadable", "skip")
KEY_ORDER = ("volume", "scan", "folio", "status", "reason")
FOLIO_REQUIRED = ("draft", "ok", "partial")
REASON_REQUIRED = ("skip", "unreadable")
NO_BLOCKS = ("skip", "unreadable")


class PageError(Exception):
    pass


@dataclass
class Page:
    volume: str
    scan: int
    folio: str | None
    status: str
    reason: str | None
    continues: str | None
    entries: list[tuple[str, str]]


def parse(text: str) -> Page:
    """Parse a page file. Raises PageError when the text breaks SPEC.md."""
    if text.startswith("\ufeff"):
        raise PageError("do not use a byte-order mark")
    if "\r" in text:
        raise PageError("use LF line endings")
    if not text.endswith("\n"):
        raise PageError("file must end with a newline")
    if not text.startswith("---\n"):
        raise PageError("front matter must open with ---")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise PageError("front matter must close with ---")
    header = _front_matter(text[4:end])
    rest = text[end + 5 :]
    continues, entries = _blocks(rest)
    page = Page(
        volume=header["volume"],
        scan=int(header["scan"]),
        folio=header.get("folio"),
        status=header["status"],
        reason=header.get("reason"),
        continues=continues,
        entries=entries,
    )
    _check_header(page)
    _check_blocks(page)
    return page


def render(page: Page) -> str:
    """Serialize a page in the form parse() accepts."""
    lines = ["---", f"volume: {page.volume}", f"scan: {page.scan}"]
    if page.folio is not None:
        lines.append(f"folio: {page.folio}")
    lines.append(f"status: {page.status}")
    if page.reason is not None:
        lines.append(f"reason: {page.reason}")
    lines.append("---")
    blocks: list[str] = []
    if page.continues is not None:
        blocks.append(f":::continues\n{page.continues}\n:::")
    for headword, body in page.entries:
        blocks.append(f":::entry {headword}\n{body}\n:::")
    if not blocks:
        return "\n".join(lines) + "\n"
    return "\n".join(lines) + "\n\n" + "\n\n".join(blocks) + "\n"


def check_path(page: Page, path: Path) -> None:
    """The filename is the scan and the parent directory is the volume."""
    stem = path.stem
    if len(stem) != 4 or not stem.isdigit() or f"{page.scan:04d}" != stem:
        raise PageError(f"filename {path.name} must be scan {page.scan:04d}")
    if path.parent.name != page.volume:
        raise PageError(f"directory {path.parent.name} must be volume {page.volume}")


def _front_matter(raw: str) -> dict[str, str]:
    if raw == "":
        raise PageError("front matter is empty")
    data: dict[str, str] = {}
    keys: list[str] = []
    for line in raw.split("\n"):
        if line == "":
            raise PageError("front matter has a blank line")
        if line != line.strip():
            raise PageError(f"front matter line has surrounding space: {line!r}")
        if ": " not in line:
            raise PageError(f"front matter line needs 'key: value': {line!r}")
        key, value = line.split(": ", 1)
        if key not in KEY_ORDER:
            raise PageError(f"unknown front-matter key {key}")
        if key in data:
            raise PageError(f"duplicate front-matter key {key}")
        if value == "" or value != value.strip():
            raise PageError(f"empty or padded value for {key}")
        data[key] = value
        keys.append(key)
    expected = [key for key in KEY_ORDER if key in data]
    if keys != expected:
        raise PageError("front matter keys must be in this order: volume, scan, folio, status, reason")
    for key in ("volume", "scan", "status"):
        if key not in data:
            raise PageError(f"front matter is missing {key}")
    if not data["scan"].isdigit() or int(data["scan"]) < 1:
        raise PageError("scan must be a positive integer")
    if data["status"] not in STATUSES:
        raise PageError(f"status must be one of {', '.join(STATUSES)}")
    return data


def _blocks(rest: str) -> tuple[str | None, list[tuple[str, str]]]:
    if rest == "":
        return None, []
    if rest == "\n":
        raise PageError("remove the blank line after the front matter when the page has no blocks")
    if not rest.startswith("\n"):
        raise PageError("put a blank line between the front matter and the first block")
    pos = 1
    continues: str | None = None
    entries: list[tuple[str, str]] = []
    while pos < len(rest):
        kind, body, pos = _take_block(rest, pos)
        if kind == ":::continues":
            if continues is not None or entries:
                raise PageError(":::continues must be the first block, and only one")
            continues = body
        else:
            if not kind.startswith(":::entry "):
                raise PageError(f"bad opening directive {kind!r}")
            headword = kind[len(":::entry ") :]
            if headword == "" or headword != headword.strip():
                raise PageError("headword is missing or padded")
            entries.append((headword, body))
    return continues, entries


def _take_block(text: str, pos: int) -> tuple[str, str, int]:
    if text.startswith(":::continues\n", pos):
        kind = ":::continues"
        body_start = pos + len(":::continues\n")
    elif text.startswith(":::entry ", pos):
        nl = text.find("\n", pos)
        if nl < 0:
            raise PageError("entry directive must be its own line")
        kind = text[pos:nl]
        body_start = nl + 1
    else:
        snippet = text[pos : pos + 40].replace("\n", "\\n")
        raise PageError(f"expected :::continues or :::entry, found {snippet!r}")
    if text.startswith(":::\n", body_start):
        body = ""
        fence = body_start
    else:
        search = body_start
        fence = -1
        while True:
            j = text.find("\n:::", search)
            if j < 0:
                raise PageError("block is missing its closing :::")
            if text[j + 1 : j + 4] == ":::" and (j + 4 == len(text) or text[j + 4] == "\n"):
                fence = j
                break
            search = j + 1
        body = text[body_start:fence]
        fence = fence + 1  # the start of the ::: line
    if not text.startswith(":::\n", fence) and text[fence:] != ":::":
        raise PageError("closing fence must be a line that is exactly :::")
    if text[fence:] == ":::":
        raise PageError("closing ::: must end with a newline")
    next_pos = fence + 4  # the newline after :::
    if next_pos < len(text):
        if text[next_pos] != "\n":
            raise PageError("put one blank line between blocks")
        if next_pos + 1 >= len(text):
            raise PageError("remove the blank line after the last block")
        if text[next_pos + 1] == "\n":
            raise PageError("put one blank line between blocks, not more")
        next_pos += 1
    return kind, body, next_pos


def _check_header(page: Page) -> None:
    if "/" in page.volume or page.volume in ("", ".", ".."):
        raise PageError("volume must be a single path segment")
    if page.status in FOLIO_REQUIRED and page.folio is None:
        raise PageError(f"status {page.status} requires folio")
    if page.status in REASON_REQUIRED and page.reason is None:
        raise PageError(f"status {page.status} requires reason")


def _check_blocks(page: Page) -> None:
    has_blocks = page.continues is not None or bool(page.entries)
    if page.status in NO_BLOCKS and has_blocks:
        raise PageError(f"status {page.status} has no blocks")
    if page.status not in NO_BLOCKS and not has_blocks:
        raise PageError(f"status {page.status} needs a continuation or an entry")
    if page.continues == "":
        raise PageError("continuation is empty")
    for headword, body in page.entries:
        if body == "":
            raise PageError(f"entry {headword} has an empty body")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: pagefile.py text/<volume>/<scan>.md", file=sys.stderr)
        return 2
    failed = 0
    for arg in argv:
        path = Path(arg)
        try:
            text = path.read_text(encoding="utf-8")
            page = parse(text)
            check_path(page, path)
        except PageError as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failed += 1
            continue
        folio = page.folio if page.folio is not None else "-"
        cont = "none" if page.continues is None else f"{len(page.continues)} chars"
        print(f"{page.volume}  scan {page.scan}  folio {folio}  {page.status}  continues {cont}  entries {len(page.entries)}")
        for headword, _body in page.entries:
            print(f"  {headword}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
