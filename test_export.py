"""Tests of the convertion script"""
import unittest
import zipfile
from pathlib import Path

from convert2cbz import prog_parser, protect_path, process_input


# -- Function
def is_valid_zip(input_file):
    """Check if the input is a valid zip archive"""
    try:
        with zipfile.ZipFile(input_file, "r") as zip_file:
            return zip_file.testzip() is None

    except zipfile.BadZipfile:
        return False


def remove_cbz():
    """Remove all CBZ"""
    for item in Path(".").rglob("*.cbz"):
        item.unlink()


# -- Initialize tests
class TestConvertion(unittest.TestCase):
    """Unitest class for test cases"""
    # -- Test 1 : Convert one PDF file
    def test_convert_one_pdf(self):
        """Test convert one PDF file"""
        remove_cbz()
        input_obj = 'tests/one_file/pdf/bd-gratuite-zoo-dingo-t-4-safari-party.pdf'
        expected_obj = Path("tests/one_file/pdf/bd-gratuite-zoo-dingo-t-4-safari-party.cbz")
        parser = prog_parser([input_obj])
        parser = protect_path(parser)
        process_input(parser)
        self.assertTrue(expected_obj.is_file())
        self.assertTrue(is_valid_zip(expected_obj))

    def test_convert_one_pdf_with_name(self):
        """Test convert one PDF file with specific output"""
        remove_cbz()
        input_obj = 'tests/one_file/pdf/bd-gratuite-zoo-dingo-t-4-safari-party.pdf'
        expected_obj = Path("Out/converted.cbz")
        parser = prog_parser([input_obj, '-o Out/converted.cbz'])
        parser = protect_path(parser)
        process_input(parser)
        self.assertTrue(expected_obj.is_file())
        self.assertTrue(is_valid_zip(expected_obj))

    def test_convert_one_cbr(self):
        """Test convert one CBR file"""
        remove_cbz()
        input_obj = 'tests/one_file/cbr/bd-gratuite-zoo-dingo-t-4-safari-party.cbr'
        expected_obj = Path("tests/one_file/cbr/bd-gratuite-zoo-dingo-t-4-safari-party.cbz")
        parser = prog_parser([input_obj])
        parser = protect_path(parser)
        process_input(parser)
        self.assertTrue(expected_obj.is_file())
        self.assertTrue(is_valid_zip(expected_obj))

    def test_convert_one_cbr_with_name(self):
        """Test convert one CBR file with specific output"""
        remove_cbz()
        input_obj = 'tests/one_file/cbr/bd-gratuite-zoo-dingo-t-4-safari-party.cbr'
        expected_obj = Path("Out/converted.cbz")
        parser = prog_parser([input_obj, '-o Out/converted.cbz'])
        parser = protect_path(parser)
        process_input(parser)
        self.assertTrue(expected_obj.is_file())
        self.assertTrue(is_valid_zip(expected_obj))

    def test_convert_one_epub(self):
        """Test convert one EPUB file"""
        remove_cbz()
        input_obj = 'tests/one_file/epub/bd-gratuite-zoo-dingo-t-4-safari-party.epub'
        expected_obj = Path("tests/one_file/epub/bd-gratuite-zoo-dingo-t-4-safari-party.cbz")
        parser = prog_parser([input_obj])
        parser = protect_path(parser)
        process_input(parser)
        self.assertTrue(expected_obj.is_file())
        self.assertTrue(is_valid_zip(expected_obj))

    def test_convert_one_epub_with_name(self):
        """Test convert one EPUB file with specific output"""
        remove_cbz()
        input_obj = 'tests/one_file/epub/bd-gratuite-zoo-dingo-t-4-safari-party.epub'
        expected_obj = Path("Out/converted.cbz")
        parser = prog_parser([input_obj, '-o Out/converted.cbz'])
        parser = protect_path(parser)
        process_input(parser)
        self.assertTrue(expected_obj.is_file())
        self.assertTrue(is_valid_zip(expected_obj))

    def test_convert_multiple_pdf(self):
        """Test convert multiple PDF files | directory scanning"""
        remove_cbz()
        input_obj = 'tests/dir/pdf'
        expected_obj = [Path('tests/dir/pdf/bd-gratuite-vick-et-vicky-t-8-les-sorcieres-de'
                             '-broceliande-t-1-le-grimoire.cbz'),
                        Path('tests/dir/pdf/bd-gratuite-zoo-dingo-t-4-safari-party.cbz')]
        parser = prog_parser([input_obj])
        parser = protect_path(parser)
        process_input(parser)
        for cbz_item_path in  expected_obj:
            self.assertTrue(cbz_item_path.is_file())

    def test_convert_multiple_cbr(self):
        """Test convert multiple CBR files | directory scanning"""
        remove_cbz()
        input_obj = 'tests/dir/cbr'
        expected_obj = [Path('tests/dir/cbr/bd-gratuite-vick-et-vicky-t-8-les-sorcieres-de'
                             '-broceliande-t-1-le-grimoire.cbz'),
                        Path('tests/dir/cbr/bd-gratuite-zoo-dingo-t-4-safari-party.cbz')]
        parser = prog_parser([input_obj])
        parser = protect_path(parser)
        process_input(parser)
        for cbz_item_path in  expected_obj:
            self.assertTrue(cbz_item_path.is_file())

    def test_convert_multiple_epub(self):
        """Test convert multiple EPUB files | directory scanning"""
        remove_cbz()
        input_obj = 'tests/dir/epub'
        expected_obj = [Path('tests/dir/epub/bd-gratuite-vick-et-vicky-t-8-les-sorcieres-de'
                             '-broceliande-t-1-le-grimoire.cbz'),
                        Path('tests/dir/epub/bd-gratuite-zoo-dingo-t-4-safari-party.cbz')]
        parser = prog_parser([input_obj])
        parser = protect_path(parser)
        process_input(parser)
        for cbz_item_path in  expected_obj:
            self.assertTrue(cbz_item_path.is_file())


if __name__ == '__main__':
    # -- Remove all cbz files
    remove_cbz()

    # -- Call test
    unittest.main()
