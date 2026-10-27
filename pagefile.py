#!/usr/bin/env python3
"""Parse and check one NED page file. See SPEC.md.

  uv run pagefile.py text/01-AB/0134.md
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from functools import lru_cache
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


WORD_LIST = Path(__file__).resolve().parent / "words.txt"
# words.txt is most-frequent first. A token rarer than RARE_RANK, one letter
# away from a word in the top COMMON_RANK, is the mast/most shape. A token
# that is not a word at all, one confusable letter from a word that is, is
# the coberent/coherent and Papat/papal shape. u/v and i/y are old spelling.
RARE_RANK = 15000
COMMON_RANK = 400
RARE_RATIO = 50
UNKNOWN_MIN = 5
CONFUSABLE = {frozenset(pair) for pair in ("bh", "tl", "ce", "mn", "un", "rn", "ao", "cl", "fi")}
TOKEN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+")
LETTERS = "abcdefghijklmnopqrstuvwxyz"
HISTORICAL = {("u", "v"), ("v", "u"), ("i", "y"), ("y", "i")}
# A stress dot splits Adia·phory into two tokens. A hyphen does not: spore-cases is a word.
JOINERS = set("·•‧∙")


@dataclass(frozen=True)
class Flag:
    token: str
    suggestion: str | None
    line: str


def _word_list() -> dict[str, int]:
    ranked: dict[str, int] = {}
    for line in WORD_LIST.read_text(encoding="utf-8").splitlines():
        word = line.strip().lower()
        if not word or word.startswith("#") or not word.isalpha():
            continue
        if word not in ranked:
            ranked[word] = len(ranked)
    return ranked


def _substitutions(word: str) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for index, old in enumerate(word):
        for letter in LETTERS:
            if letter != old:
                found.append((word[:index] + letter + word[index + 1 :], old, letter))
    return found


def _historical(old: str, new: str) -> bool:
    diffs = [(a, b) for a, b in zip(old, new) if a != b]
    return len(diffs) == 1 and diffs[0] in HISTORICAL


def _prefer(source: str, candidates: list[str], ranked: dict[str, int]) -> str | None:
    if not candidates:
        return None
    # Keep the first letter when a neighbor does. mast is nearer most than last.
    return min(candidates, key=lambda word: (word[:1] != source[:1], ranked[word]))


def _bounded(line: str, start: int, end: int) -> bool:
    if start and line[start - 1].isalpha():
        return False
    if end < len(line) and line[end].isalpha():
        return False
    return True


@lru_cache(maxsize=1)
def _loaded_words() -> dict[str, int]:
    return _word_list()


def flags_for_text(text: str) -> list[Flag]:
    """Tokens to read again on the scan. This does not change the text."""
    ranked = _loaded_words()
    found: list[Flag] = []
    seen: set[tuple[str, str | None]] = set()
    for raw_line in text.splitlines():
        matches = list(TOKEN.finditer(raw_line))
        for index, match in enumerate(matches):
            token = match.group()
            if not _bounded(raw_line, match.start(), match.end()):
                continue
            if token.isdigit():
                if len(token) > 2 or index == 0 or index + 1 == len(matches):
                    continue
                previous = matches[index - 1].group()
                following = matches[index + 1].group()
                # "also 7" is a century label. A capital after the number is a quotation.
                if previous.lower() == "also":
                    continue
                if not (previous.isalpha() and following.isalpha() and len(previous) >= 3 and len(following) >= 3):
                    continue
                if not (previous[:1].islower() and following[:1].islower()):
                    continue
                key = (token, None)
                if key in seen:
                    continue
                seen.add(key)
                found.append(Flag(token, None, raw_line.strip()))
                continue
            # Small caps are stored as capitals. "Tong." is a title abbreviation.
            # A lowercase word before a period is the end of a sentence.
            followed_by_period = match.end() < len(raw_line) and raw_line[match.end()] == "."
            if token.isupper() or (followed_by_period and token[:1].isupper()):
                continue
            if match.start() and raw_line[match.start() - 1] in JOINERS:
                continue
            if match.end() < len(raw_line) and raw_line[match.end()] in JOINERS:
                continue
            word = token.lower()
            if not word.isascii() or not word.isalpha() or len(word) > 18:
                continue
            suggestion: str | None = None
            if word in ranked:
                if ranked[word] < RARE_RANK or len(word) < 4:
                    continue
                candidates = [
                    new
                    for new, _old, _letter in _substitutions(word)
                    if new in ranked and ranked[new] < COMMON_RANK and not _historical(word, new)
                ]
                suggestion = _prefer(word, candidates, ranked)
                if suggestion is not None and ranked[word] / (ranked[suggestion] + 1) < RARE_RATIO:
                    suggestion = None
            elif len(word) >= UNKNOWN_MIN:
                candidates = [
                    new
                    for new, old, letter in _substitutions(word)
                    if frozenset((old, letter)) in CONFUSABLE and new in ranked and not _historical(word, new)
                ]
                suggestion = _prefer(word, candidates, ranked)
            if suggestion is None:
                continue
            key = (word, suggestion)
            if key in seen:
                continue
            seen.add(key)
            found.append(Flag(word, suggestion, raw_line.strip()))
    return found


def flags_for_page(page: Page) -> list[Flag]:
    parts: list[str] = []
    if page.continues:
        parts.append(page.continues)
    parts.extend(body for _headword, body in page.entries)
    return flags_for_text("\n".join(parts))


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
        page_flags = flags_for_page(page)
        print(f"flags {len(page_flags)}")
        for flag in page_flags:
            if flag.suggestion is None:
                print(f"  {flag.token}")
            else:
                print(f"  {flag.token} → {flag.suggestion}")
            print(f"    {flag.line}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
