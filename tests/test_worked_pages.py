"""Drive the published checker and builder on the worked pages."""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pagefile  # noqa: E402

PAGE_109 = ROOT / "text" / "01-AB" / "0133.md"
PAGE_110 = ROOT / "text" / "01-AB" / "0134.md"


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", *args],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class WorkedPagesTest(unittest.TestCase):
    def test_checker_accepts_both_pages(self) -> None:
        result = run(["pagefile.py", str(PAGE_109), str(PAGE_110)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("scan 133", result.stdout)
        self.assertIn("folio 109", result.stdout)
        self.assertIn("entries 22", result.stdout)
        self.assertIn("scan 134", result.stdout)
        self.assertIn("folio 110", result.stdout)
        self.assertIn("entries 29", result.stdout)
        self.assertIn("mast → most", result.stdout)
        self.assertIn("coberent → coherent", result.stdout)
        self.assertIn("papat → papal", result.stdout)
        self.assertIn("\n  10\n", result.stdout)
        self.assertIn("flags 10\n", result.stdout)
        self.assertIn("flags 6\n", result.stdout)
        self.assertNotIn("hare →", result.stdout)

    def test_builder_joins_adhesion_and_refuses_bad_outputs(self) -> None:
        folio_109 = pagefile.parse(PAGE_109.read_text(encoding="utf-8"))
        folio_110 = pagefile.parse(PAGE_110.read_text(encoding="utf-8"))
        adhesion = next(body for headword, body in folio_109.entries if headword == "Adhesion")
        joined = adhesion + "\n" + folio_110.continues

        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "checkout"
            checkout.mkdir()
            # A published tree has build.py and pagefile.py, not next_page.py.
            # Only the two worked pages, so later scans do not change this join.
            for name in ("build.py", "pagefile.py"):
                shutil.copy(ROOT / name, checkout / name)
            worked = checkout / "text" / "01-AB"
            worked.mkdir(parents=True)
            shutil.copy(PAGE_109, worked / PAGE_109.name)
            shutil.copy(PAGE_110, worked / PAGE_110.name)
            self.assertFalse((checkout / "next_page.py").exists())
            out = Path(tmp) / "built.sqlite"
            result = run(["build.py", "-o", str(out)], cwd=checkout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("ModuleNotFoundError", result.stderr)
            self.assertIn("2 pages", result.stdout)
            self.assertIn("51 words", result.stdout)
            self.assertTrue(out.is_file())

            again = run(["build.py", "-o", str(out)], cwd=checkout)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("refusing to overwrite", again.stderr)

            con = sqlite3.connect(out)
            con.row_factory = sqlite3.Row
            words = list(con.execute("SELECT printed_page, headword, text FROM words ORDER BY id"))
            pages = list(con.execute("SELECT volume, page, printed_page, status FROM pages ORDER BY page"))
            con.close()

        self.assertEqual([(row["volume"], row["page"], row["printed_page"], row["status"]) for row in pages], [
            ("01-AB", 133, "109", "ok"),
            ("01-AB", 134, "110", "ok"),
        ])
        self.assertEqual(len(words), 51)
        on_109 = [row for row in words if row["printed_page"] == "109"]
        on_110 = [row for row in words if row["printed_page"] == "110"]
        self.assertEqual(len(on_109), 22)
        self.assertEqual(len(on_110), 29)
        self.assertEqual([row["headword"] for row in on_109], [headword for headword, _body in folio_109.entries])
        self.assertEqual([row["headword"] for row in on_110], [headword for headword, _body in folio_110.entries])
        stored = next(row for row in words if row["headword"] == "Adhesion")
        self.assertEqual(stored["printed_page"], "109")
        self.assertEqual(stored["text"], joined)
        self.assertIn("accustomed policy.\n3. Psych.", stored["text"])
        self.assertTrue(stored["text"].endswith("coagulable lymph."))
        self.assertNotIn(folio_109.continues, [row["text"] for row in words])
        self.assertFalse(any(folio_109.continues in row["text"] for row in words))

        refused = run(["build.py", "-o", "data/ned.sqlite"])
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("refusing to overwrite data/ned.sqlite", refused.stderr)

    def test_recovered_folios_join_adevism(self) -> None:
        recovered = ROOT / "text" / "01-AB"
        for scan in range(25, 133):
            path = recovered / f"{scan:04d}.md"
            page = pagefile.parse(path.read_text(encoding="utf-8"))
            pagefile.check_path(page, path)
            self.assertEqual(page.scan, scan)
            self.assertEqual(page.folio, str(scan - 24))
            if scan in (47, 48, 49):
                self.assertEqual(page.status, "partial")
            else:
                self.assertEqual(page.status, "draft")
        first = pagefile.parse((recovered / "0025.md").read_text(encoding="utf-8"))
        self.assertIsNone(first.continues)
        folio_108 = pagefile.parse((recovered / "0132.md").read_text(encoding="utf-8"))
        folio_109 = pagefile.parse(PAGE_109.read_text(encoding="utf-8"))
        adevism = next(body for headword, body in folio_108.entries if headword == "Adevism")
        self.assertNotIn("MAX MÜLLER", adevism)
        self.assertTrue(folio_109.continues.startswith("1878 MAX MÜLLER"))
        account = pagefile.parse((recovered / "0087.md").read_text(encoding="utf-8"))
        account_next = pagefile.parse((recovered / "0088.md").read_text(encoding="utf-8"))
        self.assertTrue(account.entries[-1][1].endswith("like-"))
        self.assertTrue(account_next.continues.startswith("wise Accompt"))

        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "checkout"
            checkout.mkdir()
            for name in ("build.py", "pagefile.py"):
                shutil.copy(ROOT / name, checkout / name)
            worked = checkout / "text" / "01-AB"
            worked.mkdir(parents=True)
            for name in ("0132.md", "0133.md", "0134.md"):
                shutil.copy(recovered / name, worked / name)
            out = Path(tmp) / "built.sqlite"
            result = run(["build.py", "-o", str(out)], cwd=checkout)
            self.assertEqual(result.returncode, 0, result.stderr)
            con = sqlite3.connect(out)
            stored = con.execute("SELECT text FROM words WHERE headword = 'Adevism'").fetchone()
            adhesion = con.execute("SELECT text FROM words WHERE headword = 'Adhesion'").fetchone()
            con.close()
        self.assertEqual(stored[0], adevism + "\n" + folio_109.continues)
        self.assertIn("accustomed policy.\n3. Psych.", adhesion[0])


if __name__ == "__main__":
    unittest.main()
