# Transcribing a page

Add one missing page file. The contribution is that file. Do not insert into SQLite.

The format is [SPEC.md](SPEC.md). A person adding a page by hand starts at [README.md](README.md).

## What to do

- Transcribe from the Archive.org scan only. Do not consult another edition, transcription, or website.
- Write one page file, and do not insert into SQLite as the contribution.
- Run the page checker.
- Claim a page by adding its missing file.
- Do not transcribe the low-resolution `07-OP` scan or the 1933 supplement.
- Do not redo `01-AB` scans 25–132, which are already transcribed in the local database and are not page files yet.

## Scan only

Transcribe from the Archive.org scan only. Do not consult another edition, a transcription, or a website. Ignore the Internet Archive OCR text. Keep the printed spelling, including a printer's error.

The core set is the item `ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement`:

https://archive.org/details/ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement

`03-DE` in that item is about half a volume. Use the substitute scan `oed03arch`:

https://archive.org/details/oed03arch

## Do not transcribe these

- Do not transcribe the low-resolution `07-OP` scan. It is a letter-size JPEG at about 77 ppi. Leave it until a substitute scan is named.
- Do not transcribe the 1933 supplement (`11-sup`).
- Do not redo `01-AB` scans 25–132. Those pages are already transcribed in the maintainer's local database and are not page files in this repository yet. Do not add `text/01-AB/0025.md` through `text/01-AB/0132.md`.

## Claim a page

A file that is not in `text/` is free, except the reserved scans above. Claim it by adding that file. Do not add an empty placeholder. One page per contribution.

The filename is `text/<volume>/<scan>.md`. The scan number is zero-padded to four digits. Scan 135 of volume `01-AB` is `text/01-AB/0135.md`. The worked pages already in the tree are `text/01-AB/0133.md` (folio 109) and `text/01-AB/0134.md` (folio 110). Leave them unless you are correcting a reading.

## Write the file

Follow [SPEC.md](SPEC.md). Read the scan left column, then middle, then right.

- A leftover at the top of the page, from the article that started on an earlier scan, is a `:::continues` block and nothing else. It is the first block.
- Each headword that starts on this page is a `:::entry`, including an article that runs off the bottom.
- A column break on this same page stays inside that entry. `:::continues` is only for text that arrived from the previous scan.
- Set `status` to `draft` until a second person has compared the file to the scan. `ok` means that second reading.
- Join a word split with a hyphen at a line end. Put two spaces before each quotation. Write small caps as capitals. Do not use markdown italics. An unreadable glyph is `[…]`, and then `status` is `partial` with a `reason`.

## Check

Run the page checker on the file you added. It must exit 0.

```bash
python3 pagefile.py text/01-AB/0135.md
```

Use your own path. `python3 pagefile.py text/01-AB/0134.md` is the same command on a worked page.

Do not insert into SQLite as the contribution. `build.py` turns page files into a database later. It is not the way to record a page.
