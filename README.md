# New English Dictionary

Got leftover usage on an AI subscription? Spend it here. The way to contribute is to point your AI agent at this repository and let it run. It keeps transcribing scans of Murray's New English Dictionary into page files the public can keep. The 1888–1928 text is being transcribed into the public domain. The scans are [A New English Dictionary on Historical Principles, 10 volumes with supplement](https://archive.org/details/ANewEnglishDictionaryOnHistoricalPrinciples.10VolumesWithSupplement) on Archive.org. Volume `03-DE` in that item is only about half the volume, so D and E come from [oed03arch](https://archive.org/details/oed03arch).

Everything in this repository is [CC0 1.0](LICENSE). Use the transcription, the page files, and the code for anything.

## Contribute

Point your agent at <https://github.com/timjonez/new-english-dictionary> and tell it to follow [AGENTS.md](AGENTS.md). That file names each volume PDF and shows how to pull one page out of it with `qpdf`. Before it transcribes, it claims a scan range with a draft pull request, so two agents do not take the same pages. Let the agent keep going on that branch. It writes one file per scan under `text/` and checks each file with `uv run pagefile.py`. When it stops, that same pull request holds all of those pages.

The format document is [SPEC.md](SPEC.md). The checker command is `uv run pagefile.py`. The agent document is [AGENTS.md](AGENTS.md). The checker prints a flag list and still exits 0. The pull request includes that list, and each flagged token has been compared with the scan.

`01-AB` scans 25–132 are already transcribed and are reserved. Leave the low-resolution `07-OP` scan and the 1933 supplement alone.

Worked pages: `text/01-AB/0133.md` (folio 109) and `text/01-AB/0134.md` (folio 110).

`uv run build.py -o out.sqlite` builds a database from the page files. Pass a new path. The command refuses to replace an existing file.
