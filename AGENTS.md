# Transcribing pages

Keep going for the whole session. Each scan becomes one file under `text/`. When the session ends, one pull request holds every page from that run. Do not insert into SQLite.

The format is [SPEC.md](SPEC.md). A person adding pages by hand starts at [README.md](README.md).

## What to do

- Transcribe from the Archive.org scan only. Do not consult another edition, transcription, or website.
- Write a page file for every scan you finish. Do not insert into SQLite as the contribution.
- Work forward in scan order so each continuation meets the page before it.
- Claim that range with a draft pull request before transcribing it.
- Run the page checker on every file.
- Put every finished page from the session in that same pull request.
- Do not transcribe the low-resolution `07-OP` scan or the 1933 supplement.
- Do not redo `01-AB` scans 25–132, which are already transcribed in the local database and are not page files yet.

## Scan only

Transcribe from the Archive.org scan only. Do not consult another edition, a transcription, or a website. Ignore the Internet Archive OCR text. Keep the printed spelling, including a printer's error.

The core set is the item `ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement`:

https://archive.org/details/ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement

`03-DE` in that item is about half a volume. Use the substitute scan `oed03arch`:

https://archive.org/details/oed03arch

## Take one page out of a volume

Each volume is one PDF. The scan number is that PDF's page number, counting from 1. Scan 135 of `01-AB` is page 135 of the A–B file, and the transcription is `text/01-AB/0135.md`. The printed folio is a different number. It goes in the header. Page 1 of the PDF is the first scan, even when that scan is a title page.

Download the image PDF named here. Leave files whose names end in `_text.pdf` alone. Those are OCR text. Leave `00.NEDHP.PropPub.PhilSoc.1959..pdf` alone. That pamphlet is not a dictionary volume.

| Volume | PDF |
|---|---|
| `01-AB` | `01.NEDHP.AB.Oxford.Murray.1888..pdf` |
| `02-C` | `02.NEDHP.C.Oxford.Murray.1888...pdf` |
| `03-DE` | `oed03arch.pdf` on item `oed03arch` |
| `04-FG` | `04.NEDHP.FG.Oxford.Murray.1901..pdf` |
| `05p1-H` | `05.p1.NEDHP.Oxford.Murray.1901..pdf` |
| `05p2-IJK` | `05.p2.NEDHP.IJK.Oxford.Murray.1901..pdf` |
| `06p1-L` | `06.p1.NEDHP.L.Oxford.Murray.1903..pdf` |
| `06p2-MN` | `06.p2.NEDHP.MN.Oxford.Murray.1908..pdf` |
| `07-OP` | `07.NEDHP.OP.Oxford.Murray.1909..pdf` |
| `08p1-QR` | `08.p1.NEDHP.QR.Oxford.Murray.1914..pdf` |
| `08p2-SSH` | `08.p2.NEDHP.SSH.Oxford.Murray.1914..pdf` |
| `09p1-SiSqSt` | `09.p1.NEDHP.SiSqSt.Oxford.Murray.1919..pdf` |
| `09p2-SuSzTTh` | `09.p2.NEDHP.SuSzTTh.Oxford.Murray.1919..pdf` |
| `10p1-TiTzU` | `10.p1.NEDHP.TiTzU.Oxford.Murray.1926...pdf` |
| `10p2-VWXYZ` | `10.p2.NEDHP.VWXYZ.Oxford.Murray.1928..pdf` |
| `11-sup` | `11.NEDHP.sup.Oxford.Murray.1933..pdf` |

The download URL is the item, a slash, and the file name. For `01-AB` page 135:

```bash
curl -L -o 01-AB.pdf "https://archive.org/download/ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement/01.NEDHP.AB.Oxford.Murray.1888..pdf"
qpdf 01-AB.pdf --pages . 135 -- page-0135.pdf
```

For `03-DE` the item is `oed03arch` and the file is `oed03arch.pdf`:

```bash
curl -L -o 03-DE.pdf "https://archive.org/download/oed03arch/oed03arch.pdf"
qpdf 03-DE.pdf --pages . 1 -- page-0001.pdf
```

`qpdf` writes a one-page PDF. Read that page, the whole page, left column then middle then right. Keep the downloaded volume and the one-page PDF out of git.

`07-OP` and `11-sup` are in the table so the file names are not guessed. Do not transcribe them.

## Do not transcribe these

- Do not transcribe the low-resolution `07-OP` scan. It is a letter-size JPEG at about 77 ppi. Leave it until a substitute scan is named.
- Do not transcribe the 1933 supplement (`11-sup`).
- Do not redo `01-AB` scans 25–132. Those pages are already transcribed in the maintainer's local database and are not page files in this repository yet. Do not add `text/01-AB/0025.md` through `text/01-AB/0132.md`.

## Claim a range first

Do this before transcribing. Two sessions that both start at the next free scan will duplicate the work.

1. Read open pull requests:

```bash
gh pr list --repo timjonez/new-english-dictionary --state open --json number,title,updatedAt,isDraft
```

A claim is an open pull request whose title is a volume and an inclusive scan range, such as `01-AB 135-160`.

2. Also skip scans that already have a file under `text/`, the reserved `01-AB` scans 25–132, all of `07-OP`, and all of `11-sup`.

3. Pick a contiguous block you expect to finish in this session. Do not claim a whole volume. In `01-AB` the worked pages are scans 133 and 134, so the next free scan is 135 unless an open pull request already claims it.

4. A claim with no push for 48 hours has expired. `updatedAt` is the last activity. Comment on that pull request, close it, and claim the range yourself:

```bash
gh pr comment NUMBER --repo timjonez/new-english-dictionary --body "This claim expired after 48 hours without a push. Closing it."
gh pr close NUMBER --repo timjonez/new-english-dictionary
```

5. On a new branch, add `claims/<volume>-<start>-<end>.md` and open a draft pull request whose title is the range. For scans 135–160 of `01-AB` the file is `claims/01-AB-0135-0160.md`:

```markdown
---
volume: 01-AB
start: 135
end: 160
claimed: 2026-10-27T18:00:00Z
---
```

`claimed` is the current UTC time. The pull request:

```bash
gh pr create --repo timjonez/new-english-dictionary --draft --title "01-AB 135-160" --body "Claiming this range. Pages will follow on this branch."
```

6. Transcribe onto that branch, in order, and check every file. If you finish the block and still have usage, look again for a claim on the next scans, then raise `end` in the claim file and in the pull request title before you continue.

7. Remove the claim file in this pull request once the page files are in it, so the claim file is not merged. Mark the pull request ready. The page files are the record after merge.

The filename for a page is `text/<volume>/<scan>.md`. The scan number is zero-padded to four digits. Scan 135 of volume `01-AB` is `text/01-AB/0135.md`. Leave scans 133 and 134 unless you are correcting a reading.

## Write the file

Follow [SPEC.md](SPEC.md). Read the scan left column, then middle, then right.

- A leftover at the top of the page, from the article that started on an earlier scan, is a `:::continues` block and nothing else. It is the first block.
- Each headword that starts on this page is a `:::entry`, including an article that runs off the bottom.
- A column break on this same page stays inside that entry. `:::continues` is only for text that arrived from the previous scan.
- Set `status` to `draft` until a second person has compared the file to the scan. `ok` means that second reading.
- Join a word split with a hyphen at a line end. Put two spaces before each quotation. Write small caps as capitals. Do not use markdown italics. An unreadable glyph is `[…]`, and then `status` is `partial` with a `reason`.

## Check

Run the page checker on every file you added. It must exit 0. Pass them all in one command:

```bash
uv run pagefile.py text/01-AB/0135.md text/01-AB/0136.md
```

Use your own paths. `uv run pagefile.py text/01-AB/0134.md` is the same command on a worked page.

The checker prints `flags N` after the headwords. A valid file still exits 0. The next section says what to do with that list.

Do not insert into SQLite as the contribution. `build.py` turns page files into a database later. It is not the way to record a page.

## Read the page again

When the file is written, read that scan once more before you call the page finished. Then run the checker. The flag list is part of the pull request.

Each flag is a token to compare with the scan:

- a rare word one letter away from a very common word, such as `mast` beside `most`
- a token that is not an English word and is one confusable letter away from a word that is, such as `coberent` beside `coherent` or `Papat` beside `papal`
- a one- or two-digit number between two ordinary words, such as `there 10 multiplied`

For each flag, look at that spot on the scan. Keep the letters the scan prints, including a printer's error and an old spelling. Where the scan shows different letters, change the file to those letters. Where a glyph is still unreadable, write `[…]`, set `status` to `partial`, and give a `reason`. The word after the arrow is a hint about what a misreading would look like. `ok` waits for a second person. Leave your own pages at `draft`.
