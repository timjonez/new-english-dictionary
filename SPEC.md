# NED page files

Page files are the source of the transcription. `data/ned.sqlite` is a database built from those files. A page is one scan: the unit a person can read against one image. A pull request holds every page from one session.

The scan image is the only text. Do not consult another edition, a transcription, or a website. Keep the printed spelling, including a printer's error. The reading rules below are the ones that decide what goes in a file. An agent follows [AGENTS.md](AGENTS.md).

## Rights

The volumes dated 1888–1928 were published before 1930, so that text is in the public domain in the United States. The 1933 supplement stays out of this tree until its rights are settled. The United Kingdom term is a separate question. The transcription in this repository, including `text/`, is dedicated under [CC0 1.0](LICENSE): anyone may use it for anything. The scans are not in this tree. Archive.org hosts them:

- Core set: `ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement`
- `03-DE` in this dump is about half a volume. The substitute scan is `oed03arch`.
- `07-OP` in this dump is a low-resolution JPEG. Do not transcribe it until a substitute scan is named.

## Files

```
text/<volume>/<scan>.md
```

`<volume>` is one of:

```
01-AB  02-C  03-DE  04-FG  05p1-H  05p2-IJK  06p1-L  06p2-MN
07-OP  08p1-QR  08p2-SSH  09p1-SiSqSt  09p2-SuSzTTh
10p1-TiTzU  10p2-VWXYZ
```

`<scan>` is the 1-based page number of that volume's PDF, zero-padded to four digits. [AGENTS.md](AGENTS.md) names the PDF for each volume. Scan 134 is `text/01-AB/0134.md`. The header writes that same number as `134`.

A missing file means the page is free. Do not commit empty placeholders. A skip is a real file with `status: skip` and a reason, so a title page does not look like a hole.

Leave the volume PDFs, the one-page PDFs, the rasters, and the built database out of git. A release can attach the database.

## Page file

UTF-8, LF line endings, no byte-order mark. The file ends with a newline. Front-matter keys appear in this order, one `key: value` per line, with no quotes and no blank line inside the header. `volume`, `scan`, and `status` are required.

```
---
volume: 01-AB
scan: 134
folio: 110
status: ok
---
```

| Key | Value |
|---|---|
| `volume` | The directory name. |
| `scan` | The scan number, unpadded. It must match the filename. |
| `folio` | The folio printed on the page, as text. Required for `draft`, `ok`, and `partial`. This is the book page, and it diverges from the scan number because of front matter. |
| `status` | `draft`, `ok`, `partial`, `unreadable`, or `skip`. |
| `reason` | One line. Required for `skip` and `unreadable`. Optional otherwise. |

`ok` means a second person compared the file to the scan. `partial` means the page was read and at least one glyph is still in doubt. `draft` means it has not had that second reading. `unreadable` means the scan cannot be read. `skip` means the page is not lexicon text (title, blank, preface, plate).

One blank line follows the front matter when the page has blocks. A `skip` or `unreadable` file has no blocks and ends at the closing `---`.

## Blocks

A block opens with a directive on its own line and closes with a line that is exactly `:::`. One blank line sits between blocks. A line that is exactly `:::` does not occur inside a transcription.

`:::continues` is optional, and it is first. Its body is the leftover of the previous article at the top of this page, before the first new headword. A page that opens with a new headword has no continuation block.

`:::entry` plus one space plus the headword starts an article whose headword is printed on this page. The headword is the stored form. The body is the article text printed on this page, and it usually starts with that same headword line. The body also holds an article that runs off the bottom of the page. The next page's continuation is the rest of it. This file does not mark that overflow.

The body is the normalized article, not a facsimile of the column's line breaks. Within this page, join a word divided at a line end, and join a column break into the same entry. Two spaces separate a citation from its quotation. Each quotation is its own line. Small caps are capitals. Do not use markdown italics. Keep †, ||, stress dots, macrons, breves, yogh, thorn, eth, æ, œ, ə, and the rest of the printed alphabet. An unreadable glyph is `[…]`. If any glyph on the page is unreadable, the status is `partial` and `reason` says so.

A sense number is not a headword. A leftover at the top of a column is not a new entry when it belongs to the article already open. The middle and right columns of the same page stay in that article. `:::continues` is only for the article that arrives from the previous scan.

This illustration is abbreviated. A line of `⋯` stands for omitted lines and is not part of the file. The complete page is `text/01-AB/0134.md`.

```
---
volume: 01-AB
scan: 134
folio: 110
status: ok
---

:::continues
3. Psych. Intimate and involuntary association of ideas and action.
⋯
1839-47 TODD Cycl. Anat. & Phys. III. 748/1  The adhesions which are formed by the consolidation of coagulable lymph.
:::

:::entry Adhesive
Adhesive (ădhī·siv), a.; also † adhæsive. [a. Fr. adhésif, -ive, as if ad. L. *adhæsīvus. See ADHESION and -IVE.]
⋯
:::

:::entry || Adiapneustia
|| Adiapneustia (æ:diăpniū·stiă). Med. [Gr.
:::
```

## How a build joins pages

The builder walks one volume in scan order and writes a fresh database. It does not patch an old row in place. Row ids are assigned on each build. The stable handle is the volume, the folio, and the headword.

For each page it writes a `pages` row: `page` is the scan, `printed_page` is the folio, and `status` and `reason` are copied through. `skip` and `unreadable` produce no `words` rows.

An article that started on an earlier page stays open until a later page settles it.

- A `:::continues` block is appended to the open article after one newline. The article's folio stays the folio where its headword was printed.
- Each `:::entry` becomes a `words` row. That closes the article the continuation just extended. The last new entry stays open, because the next scan may continue it.
- A page of only a continuation leaves that same article open.
- A page that starts with `:::entry`, or a `skip` or `unreadable` page, closes the open article with no further text.
- A missing scan is a gap. The builder does not guess across it. A continuation on the far side of a gap is kept with the page and is not appended to an invented article. Filling the gap and building again joins it.

`uv run pagefile.py` checks one file. `uv run build.py -o out.sqlite` reads `text/` and writes a fresh database. It refuses to replace `data/ned.sqlite`. The builder checks the chain across pages.

## Contributing

Claim a scan range with a draft pull request before transcribing it, as [AGENTS.md](AGENTS.md) describes. Transcribe that range for as long as the session lasts. Put every finished page in that same pull request. `draft` can merge before the second reading. The person who set `ok` is someone other than the person who wrote the file.

`uv run pagefile.py text/01-AB/0134.md` exits 0 when the file follows this spec. It also prints `flags N`, a list of tokens to compare with the scan. A pull request includes that list. A flag leaves the exit status at 0.

## Worked example

`text/01-AB/0134.md` is folio 110, scan 134, the page already stored as `ok`.

The left column opens in the middle of Adhesion, at sense 3. That article's headword is on folio 109, so this file holds senses 3–5 in `:::continues` and stops at `coagulable lymph.` Adhibit crosses onto the middle column at sense 4 and stays inside the Adhibit entry. Adiaphorist crosses onto the right column the same way. || Adiapneustia starts at the foot of the right column and runs off the page, so its entry is only the line printed here.

The file has that one continuation and the 29 articles from Adhesive through || Adiapneustia. Joining the folio 109 text of Adhesion, a newline, and this continuation reproduces the stored Adhesion article.

`text/01-AB/0133.md` is folio 109, scan 133. The left column opens with the 1878 Müller quotation that finishes Adevism, whose headword is on folio 108. Adhesion starts on this page and stops at `accustomed policy.` Building these two files appends folio 110's continuation and reproduces the stored Adhesion article and the 29 folio 110 articles. The Müller quotation stays in the folio 109 file and does not become a row, because folio 108 is not a page file yet.
