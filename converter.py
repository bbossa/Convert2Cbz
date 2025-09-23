"""Class converter"""
import io
import logging
import sys
import tempfile
from pathlib import Path
import zipfile
import rarfile
from PyPDF2 import PdfReader
import fitz
from PIL import Image
from tqdm import tqdm
from lxml import etree


def get_opf(container_path):
    """Get OPF file"""
    try:
        tree = etree.parse(container_path)
        root = tree.getroot()
        rootfile = root.find(".//{*}rootfile")
        if rootfile is not None:
            return rootfile.attrib["full-path"]
        return None
    except etree.ParseError:
        return None


def parse_opf(opf_file):
    """Parse OPF file"""
    tree = etree.parse(opf_file)
    root = tree.getroot()

    manifest = {}
    spine = []

    # -- Extract manifest
    for item in root.findall(".//{*}item"):
        item_id = item.attrib["id"]
        href = item.attrib["href"]
        manifest.update({item_id: href})

    # -- Extract spine
    for item in root.findall(".//{*}spine/{*}itemref"):
        spine.append(item.attrib["idref"])

    return manifest, spine


def resolve_image(spine_list, temp_dir):
    """Resolve image from HTML tag"""
    images = []
    temp_dir = temp_dir.resolve()

    for spine_path in spine_list:
        if not spine_path.exists():
            # -- path not resolvable -> skip
            continue
        try:
            html_parser = etree.HTMLParser()
            html = etree.parse(spine_path, html_parser)
            root = html.getroot()
            for img_tag in root.findall(".//img"):
                src = img_tag.attrib['src']
                if not src:
                    continue
                img_path = temp_dir.joinpath(src).resolve()
                if img_path.exists():
                    if img_path not in images:
                        images.append(img_path)
        except etree.ParseError:
            # -- Unable to open the HTML file
            logging.warning("Unable to open %s",str(spine_path))
            continue

    return images


class Converter:
    """Generic class to convert file to cbz format"""

    def __init__(self, input_file, output_file):
        self.input = input_file
        self.output = output_file

    def set_output_file(self, output):
        """Set Output file"""
        self.output = output

    def set_input_file(self, input_file):
        """Set input file"""
        self.input = input_file

    def is_valid_rar(self):
        """Check if the input file is a valid rar archive"""
        try:
            with rarfile.RarFile(self.input, "r") as rar_file:
                return rar_file.testrar() is None

        except (rarfile.BadRarFile, rarfile.NotRarFile):
            return False

    def is_valid_zip(self):
        """Check if the input is a valid zip archive"""
        try:
            with zipfile.ZipFile(self.input, "r") as zip_file:
                return zip_file.testzip() is None

        except zipfile.BadZipfile:
            return False


class EpubConverter(Converter):
    """Convert EPUB file to CBZ format"""

    def convert(self):
        """Convert input file to CBZ"""
        logging.info("Converting file %s", str(self.input))

        # -- Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            temp_dir = temp_dir.resolve()

            # -- Extract epub file
            with zipfile.ZipFile(self.input, "r") as zip_fid:
                zip_fid.extractall(temp_dir)

            # -- Check MIME TYPE
            mimetype_path = temp_dir.joinpath("mimetype")
            if not mimetype_path.exists() or \
                    mimetype_path.read_text(encoding="utf-8").strip() != "application/epub+zip":
                logging.error("EPUB %s is not a valid EPUB document", str(self.input.name))
                return

            # -- Check container file
            container_path = temp_dir.joinpath("META-INF/container.xml")
            if not container_path.exists():
                logging.error("Missing 'META-INF/container.xml' file in %s", str(self.input.name))
                return

            opf_path = get_opf(container_path)
            if not opf_path:
                logging.error("Container 'META-INF/container.xml' doesn't point to a valid OPF")
                return

            opf_path = temp_dir.joinpath(opf_path)
            if not opf_path.exists():
                logging.error("OPF file %s cannot be found", str(opf_path))
                return

            manifest, spine = parse_opf(opf_path)

            # -- List all images with List Comprehension
            spines_images = [temp_dir.joinpath(manifest[item]) for item in spine if
                             item in manifest]

            # -- Resolve images
            images = resolve_image(spines_images, temp_dir)

            # -- Construct CBZ
            if len(images) == 0:
                logging.error("Archive contains not file")
            else:
                with zipfile.ZipFile(self.output, "w") as zip_fid:
                    logging.info("Exporting to CBZ container")
                    for file in images:
                        cbz_name = file.relative_to(temp_dir)
                        zip_fid.write(file, cbz_name)


class CbrConverter(Converter):
    """Convert CBR file to CBZ format"""

    def convert(self):
        """Convert input file to CBZ"""
        logging.info("Converting file %s",str(self.input))

        # -- Check first if the CBR is valid
        if not self.is_valid_rar():
            if self.is_valid_zip():
                # -- CBR archive is in fact a CBZ archive --> rename
                self.input.rename(self.output)
                return

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            with rarfile.RarFile(self.input, "r") as rar_file:
                # -- Extract CBR as rarfile into temp directory
                rar_file.extractall(temp_dir)

                # -- Collect all files with List Comprehension
                files = sorted([item for item in temp_dir.rglob("*") if item.is_file()])

            if len(files) == 0:
                logging.error("Archive contains not file")
            else:
                with zipfile.ZipFile(self.output, "w") as zip_fid:
                    logging.info("Exporting to CBZ container")
                    for file in files:
                        cbz_name = file.relative_to(temp_dir)
                        zip_fid.write(file, cbz_name)


class PdfConverter(Converter):
    """Convert PDF file to CBZ format"""

    def __init__(self, input_file, output_file):
        super().__init__(input_file, output_file)
        self.dpi = 72
        self.format = "png"
        self.quality = 85

    def set_dpi(self, dpi):
        """Set DPI value"""
        self.dpi = dpi

    def set_format(self, file_format):
        """Set file format"""
        self.format = file_format

    def set_quality(self, quality):
        """Set JPEG quality"""
        self.quality = quality

    def analyze(self):
        """Analyze PDF file to determine MIN, MAX and AVERAGE DPI"""
        logging.info("Analysing file %s", str(self.input))
        pdf = PdfReader(str(self.input))
        # -- Get pages width as list with List Comprehension
        page_widths = [float(p.mediabox.width) for p in pdf.pages]
        # -- Compute DPI values list with List Comprehension
        dpi_values = [int(2000 / width * 72) for width in page_widths]
        print("Min DPI: ", str(min(dpi_values)))
        print("Max DPI: ", str(max(dpi_values)))
        print("Average DPI: ", str(round(sum(dpi_values) / len(dpi_values))))

    def _compute_dpi(self):
        """Compute Auto dpi based on the average DPI of input document"""
        pdf = PdfReader(str(self.input))
        # -- Get pages width as list with List Comprehension
        page_widths = [float(p.mediabox.width) for p in pdf.pages]
        # -- Compute DPI values list with List Comprehension
        dpi_values = [int(2000 / width * 72) for width in page_widths]

        dpi = round(sum(dpi_values) / len(dpi_values))
        dpi = max(dpi, 100)

        self.dpi = dpi

    def _process_pdf(self):
        # -- Set output dict
        data_img = {}
        with fitz.open(str(self.input)) as pdf:
            # -- Get number of page
            num_pages = len(pdf)
            padding_width = len(str(num_pages))
            # -- Set output file extension
            if self.format == "png":
                ext = "png"
            else:
                ext = "jpg"

            # -- Create progress bar with TQDM
            progress = tqdm(total=num_pages, desc=f"Rendering {self.input.name}", unit="pages",
                            file=sys.stdout)

            for i in range(1, num_pages + 1):
                # -- Get page
                page = pdf.load_page(i - 1)
                scale = self.dpi / 72
                # - Create maxtrix scaling
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                # -- generate image
                if self.format == "png":
                    # -- Export directly in PNG databyte
                    data = pix.tobytes("png")
                else:
                    # -- Export via PIL for quality control
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.sample)
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=self.quality)
                    data = buffer.getvalue()

                data_img.update({f"{self.input.stem}_{str(i).zfill(padding_width)}.{ext}": data})
                progress.update(1)

        progress.close()
        return data_img

    def convert(self):
        """Convert PDF to CBZ"""
        logging.info("Converting file %s", str(self.input))

        # -- Get DPI
        if not self.dpi:
            self._compute_dpi()

        # -- Start conversion

        # -- Process pages
        data_img = self._process_pdf()

        if len(data_img) == 0:
            logging.error("No image processed during conversion")
        else:
            # -- Export to zip file
            with zipfile.ZipFile(self.output, "w") as zip_fid:
                logging.info("Exporting to CBZ container")
                for img_name, img_data in data_img.items():
                    zip_fid.writestr(img_name, img_data)

        logging.info("CBZ created: %s", str(self.output))
