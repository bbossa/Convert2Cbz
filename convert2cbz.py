"""THis script convert compatibles files to CBZ format"""
import argparse
import errno
import logging
import os
import shutil
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from converter import PdfConverter, CbrConverter, EpubConverter


def prog_parser(args: list) -> argparse.Namespace:
    """Program parser"""
    parser = argparse.ArgumentParser(prog="convert2cbz",
                                     description="Convert compatible files to CBZ format."
                                                 " Can be use with one file argument or"
                                                 " scan an entire directory.")
    parser.add_argument("path",
                        type=Path,
                        help="File or directory")
    parser.add_argument("-o",
                        "--output",
                        type=Path,
                        help="Output directory (default input path)")
    parser.add_argument("-d",
                        "--dpi",
                        type=int,
                        help="Specify DPI (default auto)")
    parser.add_argument("-q",
                        "--quality",
                        type=int,
                        default=85,
                        help="JPEG quality (default 85)")
    parser.add_argument("-f",
                        "--format",
                        choices=["jpeg", "png"],
                        default="png",
                        help="Image format: JPEG or PNG (default PNG)")
    parser.add_argument("-l",
                        "--logfile",
                        type=Path,
                        help="log file (default none)")
    parser.add_argument("-a",
                        "--analyze",
                        action="store_true",
                        help="Analyze input document")

    return parser.parse_args(args)


def init_logging(logfile_path: Path) -> None:
    """Initialize log file"""

    logger = logging.getLogger()
    # -- Clear log
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # -- Define format
    logger.setLevel(logging.INFO)
    log_format = logging.Formatter("%(asctime)s %(levelname)s: %(message)s",
                                   "%Y-%m-%d %H:%M:%S")

    # -- Console logger
    console_logger = logging.StreamHandler(sys.stdout)
    console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(log_format)
    logger.addHandler(console_logger)

    # -- File logger
    if logfile_path:
        file_logger = logging.FileHandler(str(logfile_path), mode="w", encoding="utf-8")
        file_logger.setLevel(logging.INFO)
        file_logger.setFormatter(log_format)
        logger.addHandler(file_logger)


def convert_pdf_to_cbz(input_path: Path, args: argparse.Namespace) -> None:
    """Convert PDF document to CBZ format"""
    if args.output:
        if args.output.is_dir():
            output = args.output.joinpath(input_path.stem).with_suffix(".cbz")
        else:
            output = args.output
    else:
        output = input_path.with_suffix(".cbz")

    # -- Create converter
    converter = PdfConverter(input_path, output)
    converter.set_dpi(args.dpi)
    converter.set_format(args.format)
    converter.set_quality(args.quality)

    if args.analyze:
        converter.analyze()
    else:
        converter.convert()


def convert_cbr_to_cbz(input_path: Path, output_path: Path) -> None:
    """Convert PDF document to CBZ format"""
    if output_path is None:
        output = input_path.with_suffix(".cbz")
    else:
        if output_path.is_dir():
            output = output_path.joinpath(input_path.stem).with_suffix(".cbz")
        else:
            output = output_path

    # -- Create converter
    converter = CbrConverter(input_path, output)
    # -- Check first if the input file is a valid rar file
    if converter.is_valid_rar():
        converter.convert()
    else:
        if converter.is_valid_zip():
            # -- Just need to copy the input file
            shutil.copy(input_path, output)
        else:
            logging.warning("File %s is not valid RAR archive nor a valid ZIP archive")


def convert_epub_to_cbz(input_path: Path, output_path: Path) -> None:
    """Convert EPUB document to CBZ format"""
    if output_path is None:
        output = input_path.with_suffix(".cbz")
    else:
        if output_path.is_dir():
            output = output_path.joinpath(input_path.stem).with_suffix(".cbz")
        else:
            output = output_path

    # -- Create converter
    converter = EpubConverter(input_path, output)
    converter.convert()


def check_unrar() -> bool:
    """Check if unrar.exe exist"""
    if Path("./UnRAR.exe").exists():
        return True

    logging.warning("Tool UnRAR.exe is missing. "
                    "Please download it at https://www.rarlab.com/rar/rarlng_unsigned.rar")
    return False


def list_files(input_path: Path) -> (list, list, list):
    """Scan PDF, CBR and EPUB file in the input directory"""
    list_pdf = []
    list_cbr = []
    list_epub = []

    for item in input_path.glob("*"):
        if item.is_file():
            if item.suffix.lower() == ".pdf":
                list_pdf.append(item)
            elif item.suffix.lower() == ".cbr":
                list_cbr.append(item)
            elif item.suffix.lower() == ".epub":
                list_epub.append(item)

    return list_pdf, list_cbr, list_epub


def process_path(args: argparse.Namespace) -> None:
    """Scan a directory for file processing"""
    list_pdf, list_cbr, list_epub = list_files(args.path)

    # -- Check if output is a directory
    if args.output is not None:
        if args.output.is_dir():
            # -- Output is a file -> set parent directory
            args.output = args.output.parent

    # -- Run PDF export
    for item in list_pdf:
        convert_pdf_to_cbz(item, args)

    # -- Run CBR export
    flag_unrar = check_unrar()
    if len(list_cbr) > 0 and flag_unrar:
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            # -- Create threads execution
            future_cbz = [executor.submit(convert_cbr_to_cbz, item, args.output) for item in
                          list_cbr]
            progress = tqdm(total=len(list_cbr), desc="Convert", unit="files", file=sys.stdout)
            # -- Wait to each thread to stop and try to get execution
            for future in as_completed(future_cbz):
                try:
                    future.result()
                    progress.update(1)
                except Exception as e:  # pylint: disable=broad-except
                    logging.error("Error during file conversion: %s", e)
            progress.close()

    # -- Run EPUB export
    if len(list_epub) > 0:
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            # -- Create threads execution
            future_epub = [executor.submit(convert_cbr_to_cbz, item, args.output) for item in
                           list_epub]
            progress = tqdm(total=len(list_epub), desc="Convert", unit="files", file=sys.stdout)
            # -- Wait to each thread to stop and try to get execution
            for future in as_completed(future_epub):
                try:
                    future.result()
                    progress.update(1)
                except Exception as e:  # pylint: disable=broad-except
                    logging.error("Error during file conversion: %s", e)
            progress.close()


def validate_output(output: Path) -> Path | None:
    """Create output directory or file if necessary"""
    # -- Protect output path name
    if str(output).endswith('"') or str(output).endswith("'"):
        if str(output).endswith('"'):
            output = Path(str(output).strip('"'))
        elif str(output).endswith("'"):
            output = Path(str(output).strip("'"))

    # -- Check if the output path / file exists
    if output is None:
        # -- Nothing to do
        return output

    # -- Trim
    output = Path(str(output).strip())
    print(output)

    if output.exists():
        check_file_permission(output)
    try:
        if len(output.suffixes) > 0:
            # -- File
            output.parent.mkdir(parents=True, exist_ok=True)
        else:
            # -- Directory
            output.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logging.error("Unable to create the output path - Permission error.")
        sys.exit(-2)

    return output


def check_file_permission(test_file: Path) -> None:
    """Check if a file is writable"""
    try:
        with open(test_file, "w", encoding="utf-8") as fid:
            fid.close()
    except PermissionError:
        logging.error("Output is not accessible with WRITE mode")
        sys.exit(-2)
    except IOError as e:
        if e.errno == errno.EACCES:
            logging.error("Output is not accessible with WRITE mode")
            sys.exit(-2)
        raise


def protect_path(parser: argparse.Namespace) -> argparse.Namespace:
    """Protect path"""
    # -- Check path error when using solo directory to scan
    if str(parser.path).endswith('"') or str(parser.path).endswith("'"):
        if str(parser.path).endswith('"'):
            parser.path = Path(str(parser.path).strip('"'))
        elif str(parser.path).endswith("'"):
            parser.path = Path(str(parser.path).strip("'"))

    return parser


def process_input(parser: argparse.Namespace):
    """Process input path"""
    parser.output = validate_output(parser.output)
    if parser.path.is_file():
        if parser.path.suffix.lower() == ".pdf":
            convert_pdf_to_cbz(parser.path, parser)
        elif parser.path.suffix.lower() == ".cbr":
            convert_cbr_to_cbz(parser.path, parser.output)
        elif parser.path.suffix.lower() == ".epub":
            convert_epub_to_cbz(parser.path, parser.output)
        else:
            logging.warning("File format is not supported")
    elif parser.path.is_dir():
        process_path(parser)
    else:
        logging.error("Input does not exist.")


def main() -> None:
    """Main program"""
    # -- Create parser
    parser = prog_parser(sys.argv[1:])
    init_logging(parser.logfile)

    logging.info("Start program")

    # -- Check input

    if parser.path is None:
        logging.error("No input file or directory provided. See --help for usage.")
        sys.exit(-1)

    # -- Check path error when using solo directory to scan
    parser = protect_path(parser)

    # -- Process input path / file
    process_input(parser)


# -- Start main program
if __name__ == "__main__":
    main()
    sys.exit(0)
