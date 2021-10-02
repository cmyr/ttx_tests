import argparse
import os
import sys
import difflib
from afdko import makeotf

from fontTools.ttLib import TTFont

from fontTools.feaLib.builder import addOpenTypeFeatures

FONT_PATH = "./resources/Compagnon-Roman.otf"
OUTPUT_DIR = "./output"

def read_ttx(path):
    lines = []
    if not os.path.exists(path):
        return lines
    with open(path, "r", encoding="utf-8") as ttx:
        for line in ttx.readlines():
            # Elide ttFont attributes because ttLibVersion may change.
            if line.startswith("<ttFont "):
                lines.append("<ttFont>\n")
            else:
                lines.append(line.rstrip() + "\n")
    return lines


def fileNameWithExtension(path, extension):
    fileName = os.path.split(path)[1]
    return os.path.splitext(fileName)[0] + extension

def run_fonttools(path):
    """fonttools.py"""
    font = TTFont(FONT_PATH)
    addOpenTypeFeatures(font, path)

    outFile = fileNameWithExtension(path, ".fonttools.ttx")
    outPath = os.path.join(OUTPUT_DIR, outFile)

    return write_xml(font, outPath)


def write_xml(tt_font, to_path):
    prev = read_ttx(to_path)
    # tt_font.saveXML(outPath, tables=['head', 'name', 'BASE', 'GDEF', 'GSUB',
                                     # 'GPOS', 'OS/2', 'STAT', 'hhea', 'vhea'])
    tt_font.saveXML(to_path, tables=[ 'GDEF', 'GSUB', 'GPOS'])
    return (prev, read_ttx(to_path))


def run_afdko(path):
    """afdko"""
    out_path = os.path.join(OUTPUT_DIR, "afdko-out.otf")
    if os.path.exists(out_path):
        os.remove(out_path)
    args = ['-f', FONT_PATH, '-ff', path, '-o', out_path]
    params = makeotf.MakeOTFParams()
    makeotf.getOptions(params, args)
    makeotf.setMissingParams(params)
    makeotf.setOptionsFromFontInfo(params)
    makeotf.runMakeOTF(params)

    font = TTFont(out_path)
    os.remove(out_path)
    ttxPath = fileNameWithExtension(path, ".afdko.ttx")
    ttxPath = os.path.join(OUTPUT_DIR, ttxPath)
    return write_xml(font, ttxPath)


def compare_results(impl, path):
    (old, new) = impl(path)
    print("running", impl.__doc__)
    if old and old != new:
        for line in difflib.unified_diff(
                old, new, fromfile="previous", tofile="new"):
            sys.stderr.write(line)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="compile a ttx from an example file"
    )
    parser.add_argument(
        "input_fea", metavar="FEATURES", help="Path to the feature file"
    )
    options = parser.parse_args()
    if os.path.splitext(options.input_fea)[1] != ".fea":
        print("expected input .fea file")
        return 1

    if not os.path.exists("output"):
        os.mkdir("output")

    compare_results(run_fonttools, options.input_fea)
    compare_results(run_afdko, options.input_fea)


if __name__ == "__main__":
    sys.exit(main())
