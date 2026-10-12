
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from polycode_cli.cli import VERSION, main


class TestPolyCodeCLI(unittest.TestCase):

    def test_version(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as result:
                main(["--version"])

        self.assertEqual(result.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"PolyCode {VERSION}")

    def test_missing_file(self):
        errors = io.StringIO()

        with contextlib.redirect_stderr(errors):
            result = main(["run", "definitely_missing.poly"])

        self.assertEqual(result, 1)
        self.assertIn("File not found", errors.getvalue())

    def test_wrong_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            file_path = Path(folder) / "program.txt"
            file_path.write_text("print('hello')", encoding="utf-8")

            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                result = main(["run", str(file_path)])

        self.assertEqual(result, 1)
        self.assertIn(".poly extension", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
