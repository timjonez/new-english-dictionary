#!/usr/bin/env python3
"""Build a SQLite database from text/ page files. See SPEC.md.

  uv run build.py -o out.sqlite

The file written is a fresh database. This refuses to replace data/ned.sqlite.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import pagefile

# Scan order for the core volumes, then the supplement. The supplement stays
# out of the public tree until its rights are settled; the order is here so a
# checkout can build without the local session tools.
VOLUMES = (
    "01-AB",
    "02-C",
    "03-DE",
    "04-FG",
    "05p1-H",
    "05p2-IJK",
    "06p1-L",
    "06p2-MN",
    "07-OP",
    "08p1-QR",
    "08p2-SSH",
    "09p1-SiSqSt",
    "09p2-SuSzTTh",
    "10p1-TiTzU",
    "10p2-VWXYZ",
    "11-sup",
)

ROOT = Path(__file__).resolve().parent
SOURCE_DB = ROOT / "data" / "ned.sqlite"

SCHEMA = """
CREATE TABLE words (
    id INTEGER PRIMARY KEY,
    volume TEXT NOT NULL,
    printed_page TEXT,
    headword TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE INDEX words_headword ON words (headword);
CREATE TABLE pages (
    volume TEXT NOT NULL,
    page INTEGER NOT NULL,
    printed_page TEXT,
    status TEXT NOT NULL,
    reason TEXT,
    PRIMARY KEY (volume, page)
);
"""


class BuildError(Exception):
    pass


@dataclass
class Article:
    volume: str
    folio: str | None
    headword: str
    text: str


def load_pages(text_root: Path) -> list[tuple[Path, pagefile.Page]]:
    if not text_root.is_dir():
        raise BuildError(f"no page directory {text_root}")
    found: list[tuple[Path, pagefile.Page]] = []
    for path in text_root.glob("*/*.md"):
        try:
            page = pagefile.parse(path.read_text(encoding="utf-8"))
            pagefile.check_path(page, path)
        except pagefile.PageError as exc:
            raise BuildError(f"{path}: {exc}") from exc
        found.append((path, page))
    rank = {name: index for index, name in enumerate(VOLUMES)}
    found.sort(key=lambda item: (rank.get(item[1].volume, len(rank)), item[1].volume, item[1].scan))
    return found


def assemble(pages: list[pagefile.Page]) -> tuple[list[tuple], list[Article], list[str]]:
    """Join pages in scan order. Returns pages rows, articles, and warnings."""
    page_rows: list[tuple] = []
    articles: list[Article] = []
    warnings: list[str] = []
    open_article: Article | None = None
    prev: pagefile.Page | None = None

    for page in pages:
        if prev is not None and prev.volume != page.volume:
            prev = None
            open_article = None
        if prev is not None and page.scan == prev.scan:
            raise BuildError(f"{page.volume} scan {page.scan} is duplicated")
        if prev is not None and page.scan != prev.scan + 1:
            if open_article is not None:
                warnings.append(
                    f"{page.volume}: gap after scan {prev.scan} closed {open_article.headword}"
                )
            else:
                warnings.append(f"{page.volume}: gap after scan {prev.scan}")
            open_article = None

        if page.continues is not None:
            if open_article is None:
                if prev is not None and page.scan == prev.scan + 1 and prev.status in pagefile.NO_BLOCKS:
                    raise BuildError(
                        f"{page.volume} scan {page.scan}: continuation follows status {prev.status}"
                    )
                warnings.append(f"{page.volume} scan {page.scan}: continuation has no open article")
            else:
                open_article.text += "\n" + page.continues
        else:
            open_article = None

        page_rows.append((page.volume, page.scan, page.folio, page.status, page.reason))
        if page.status not in pagefile.NO_BLOCKS:
            for headword, body in page.entries:
                article = Article(page.volume, page.folio, headword, body)
                articles.append(article)
                open_article = article
        prev = page

    return page_rows, articles, warnings


def write_db(path: Path, page_rows: list[tuple], articles: list[Article]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        con.executescript(SCHEMA)
        con.executemany(
            "INSERT INTO pages (volume, page, printed_page, status, reason) VALUES (?, ?, ?, ?, ?)",
            page_rows,
        )
        con.executemany(
            "INSERT INTO words (volume, printed_page, headword, text) VALUES (?, ?, ?, ?)",
            [(article.volume, article.folio, article.headword, article.text) for article in articles],
        )
        con.commit()
    except Exception:
        con.close()
        path.unlink(missing_ok=True)
        raise
    else:
        con.close()


def build(text_root: Path, output: Path) -> list[str]:
    loaded = load_pages(text_root)
    page_rows, articles, warnings = assemble([page for _path, page in loaded])
    write_db(output, page_rows, articles)
    counts: dict[str, list[int]] = {}
    for volume, _scan, _folio, _status, _reason in page_rows:
        counts.setdefault(volume, [0, 0])
        counts[volume][0] += 1
    for article in articles:
        counts.setdefault(article.volume, [0, 0])
        counts[article.volume][1] += 1
    for volume, (pages, words) in counts.items():
        print(f"{volume}  {pages} pages  {words} words")
    if not counts:
        print("0 pages  0 words")
    print(f"wrote {output}")
    return warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build a SQLite database from text/ page files.")
    parser.add_argument("-o", "--output", required=True, help="database to create")
    parser.add_argument("--text", default=str(ROOT / "text"), help="page-file tree (default: text/)")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if not output.is_absolute():
        output = Path.cwd() / output
    output = output.resolve()
    if output == SOURCE_DB.resolve():
        print("refusing to overwrite data/ned.sqlite", file=sys.stderr)
        return 1
    if output.exists():
        print(f"refusing to overwrite {output}", file=sys.stderr)
        return 1
    try:
        warnings = build(Path(args.text), output)
    except BuildError as exc:
        print(exc, file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
