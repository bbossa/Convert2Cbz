"""THis script convert compatibles files to CBZ format"""
import argparse
import logging
import sys
from pathlib import Path
from converter import PdfConverter, CbrConverter, EpubConverter


def prog_parser():
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

    return parser.parse_args()


def init_logging(logfile_path):
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


def convert_pdf_to_cbz(input_path, args):
    """Convert PDF document to CBZ format"""
    if args.output:
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


def convert_cbr_to_cbz(input_path, output_path):
    """Convert PDF document to CBZ format"""
    if output_path is None:
        output = input_path.with_suffix(".cbz")
    else:
        output = output_path

    # -- Create converter
    converter = CbrConverter(input_path, output)
    converter.convert()


def convert_epub_to_cbz(input_path, output_path):
    """Convert EPUB document to CBZ format"""
    if output_path is None:
        output = input_path.with_suffix(".cbz")
    else:
        output = output_path

    # -- Create converter
    converter = EpubConverter(input_path, output)
    converter.convert()


def process_path(args):
    """Scan a directory for file processing"""
    for item in args.path.glob("*"):
        if item.is_file():
            if item.suffix.lower() == ".pdf":
                convert_pdf_to_cbz(item, args)
            elif item.suffix.lower() == ".cbr":
                convert_cbr_to_cbz(item, args.output)
            elif item.suffix.lower() == ".epub":
                convert_epub_to_cbz(item, args.output)


def main():
    """Main program"""
    # -- Create parser
    args = prog_parser()
    init_logging(args.logfile)

    logging.info("Start program")

    # -- Check input

    if args.path is None:
        logging.error("No input file or directory provided. See --help for usage.")
        sys.exit(-1)

    # -- Check path error when using solo directory to scan
    if str(args.path).endswith('"') or str(args.path).endswith("'"):
        args.path = Path(str(args.path).replace('"', "").replace("'",""))

    if args.path.is_file():
        if args.path.suffix.lower() == ".pdf":
            convert_pdf_to_cbz(args.path, args)
        elif args.path.suffix.lower() == ".cbr":
            convert_cbr_to_cbz(args.path, args.output)
        elif args.path.suffix.lower() == ".epub":
            convert_epub_to_cbz(args.path, args.output)
        else:
            logging.warning("File format is not supported")
    elif args.path.is_dir():
        process_path(args)
    else:
        logging.error("Input does not exist.")


# -- Start main program
if __name__ == "__main__":
    main()
    sys.exit(0)
