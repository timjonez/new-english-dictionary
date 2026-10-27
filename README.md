# New English Dictionary

Got leftover usage on an AI subscription? Spend it here. The way to contribute is to point your AI agent at this repository. It transcribes one scan of Murray's New English Dictionary into a page file the public can keep. The 1888–1928 text is being transcribed into the public domain. The scans stay on Archive.org.

Everything in this repository is [CC0 1.0](LICENSE). Use the transcription, the page files, and the code for anything.

## Contribute

Point your agent at <https://github.com/timjonez/oxford-english-dictionary> and tell it to follow [AGENTS.md](AGENTS.md). The agent reads one Archive.org scan, adds one file under `text/`, and checks it with `python3 pagefile.py`. Open a pull request with that file.

The format document is [SPEC.md](SPEC.md). The checker command is `python3 pagefile.py`. The agent document is [AGENTS.md](AGENTS.md).

`01-AB` scans 25–132 are already transcribed and are reserved. Leave the low-resolution `07-OP` scan and the 1933 supplement alone.

Worked pages: `text/01-AB/0133.md` (folio 109) and `text/01-AB/0134.md` (folio 110).

`python3 build.py -o out.sqlite` builds a database from the page files. Pass a new path. The command refuses to replace an existing file.
