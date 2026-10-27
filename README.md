# New English Dictionary

Got leftover usage on an AI subscription? Spend it here. Point an agent at one scan of Murray's New English Dictionary and it writes a page file the public can keep. The 1888–1928 text is being transcribed into the public domain. The scans stay on Archive.org.

## Add a page

The format document is [SPEC.md](SPEC.md). The checker command is `python3 pagefile.py`. The agent document is [AGENTS.md](AGENTS.md).

1. Choose a scan that has no file under `text/`. `01-AB` scans 25–132 are already transcribed and are reserved. Do not transcribe the low-resolution `07-OP` scan or the 1933 supplement.
2. Write `text/<volume>/<scan>.md` from the Archive.org scan, in the form SPEC.md describes.
3. Run the checker. It must exit 0:

```bash
python3 pagefile.py text/01-AB/0134.md
```

Worked pages: `text/01-AB/0133.md` (folio 109) and `text/01-AB/0134.md` (folio 110).

`python3 build.py -o out.sqlite` builds a database from the page files. Pass a new path. The command refuses to replace an existing file.
