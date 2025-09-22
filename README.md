# Convert2Cbz
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![pylint](https://img.shields.io/badge/PyLint-10.00-brightgreen?logo=python&logoColor=white)
[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Convert PDF, CBR and EPUB comics / manga / BD to CBZ format.

## Description
The tool can take a PDF, a CBR or an EPUB file and convert it as a CBZ file.

## Usages
<pre>
usage: convert2cbz [-h] [-o OUTPUT] [-d DPI] [-q QUALITY] [-f {jpeg,png}] [-l LOGFILE] [-a] path

Convert compatible files to CBZ format. Can be use with one file argument or scan an entire directory.

positional arguments:
  path                  File or directory

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory (default input path)
  -d DPI, --dpi DPI     Specify DPI (default auto)
  -q QUALITY, --quality QUALITY
                        JPEG quality (default 85)
  -f {jpeg,png}, --format {jpeg,png}
                        Image format: JPEG or PNG (default PNG)
  -l LOGFILE, --logfile LOGFILE
                        log file (default none)
  -a, --analyze         Analyze input document
</pre>

option `-d` or `--dpi` is only used for PDF conversion.\
option `-f` or `--format` is only used for PDF conversion.\
option `-q` or `--quality` is only used for PDF conversion.

## Restrictions
Script currently uses `Unrar.exe` which is free to use but have some restriction. Check licence file for more information.


