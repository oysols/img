#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Iterator, Union, BinaryIO
import contextlib
import sys

from PIL import Image  # type: ignore


def get_palette() -> List[Tuple[str, str]]:
    # Basic colors 0 - 7
    # Bright basic colors 8 - 15
    palette = [
        ("00",  "000000"),
        ("01",  "800000"),
        ("02",  "008000"),
        ("03",  "808000"),
        ("04",  "000080"),
        ("05",  "800080"),
        ("06",  "008080"),
        ("07",  "c0c0c0"),
        ("08",  "808080"),
        ("09",  "ff0000"),
        ("10",  "00ff00"),
        ("11",  "ffff00"),
        ("12",  "0000ff"),
        ("13",  "ff00ff"),
        ("14",  "00ffff"),
        ("15",  "ffffff"),
        ]

    # Extended colors 16 - 231 (000000, ffffff)
    # Almost evenly spread
    # values = [0] + [95 + 40 * i for i in range(5)]
    # All RGB values with any combination of "values" are valid
    color_code = 16
    values = ["00", "5f", "87", "af", "d7", "ff"]
    for r in values:
        for g in values:
            for b in values:
                palette.append((str(color_code), "".join([r, g, b])))
                color_code += 1

    # Gray scale 232 - 255 (080808 - eeeeee)
    # Almost evenly spread
    gray_values = [8 + 10 * i for i in range(24)]
    for i in gray_values:
        palette.append((str(color_code), "{:02x}{:02x}{:02x}".format(i, i, i)))
        color_code += 1
    return palette

def create_closest_valid_color_dict() -> Dict[int, str]:
    # All RGB values with any combination of  `values` are valid
    values = ["00", "5f", "87", "af", "d7", "ff"]
    closest_hex_lookup = {}
    for i in range(256):
        distances = [abs(i - int(value, 16)) for value in values]
        index_of_minimum = distances.index(min(distances))
        closest_hex_lookup[i] = values[index_of_minimum]
    return closest_hex_lookup


# Pregenerate lookup table for finding the closest valid color value
CLOSEST_VALID_COLORS = create_closest_valid_color_dict()

# Pregenerate lookup table for converting a valid hexcolor to colorcode
HEX_2_COLORCODE = {hexcolor: colorcode for colorcode, hexcolor in get_palette()}


def get_colorcode_from_rgb(rgb_tuple: Tuple[int, int, int]) -> str:
    hexcolor = "".join([CLOSEST_VALID_COLORS[color] for color in rgb_tuple])
    return HEX_2_COLORCODE[hexcolor]


def is_valid_image(path: Path) -> bool:
    try:
        im = Image.open(path)
    except:
        return False
    return True


def process_image(image: Union[Path, BinaryIO], cols: Optional[int] = None, rows: Optional[int] = None) -> List[str]:
    term_cols, term_rows = os.get_terminal_size(1)
    if not cols:
        cols = term_cols
    if not rows:
        rows = term_rows
    size = (cols, rows*2)
    im = Image.open(image)
    im.thumbnail(size, Image.ANTIALIAS)
    output = []
    for y in range(1, im.size[1], 2):  # Use y and y -1 every loop
        line = ""
        for x in range(0, im.size[0], 1):
            # Build image using utf-8 half block symbol
            char = "▄"

            # Background (top)
            p = im.getpixel((x, y - 1))
            colorcode = get_colorcode_from_rgb(p[:3])
            background_color = "\033[48;5;{}m".format(colorcode)

            # Foreground (bottom)
            p = im.getpixel((x, y))
            colorcode = get_colorcode_from_rgb(p[:3])
            foreground_color = "\033[38;5;{}m".format(colorcode)
            line += background_color + foreground_color + char
        line += "\033[0m"  # Clear formatting
        output.append(line)
    return output


@contextlib.contextmanager
def safe_print() -> Iterator[None]:
    try:
        yield
    finally:
        print("\033[0m", end="")  # Make sure to not break terminal


def main() -> None:
    parser = argparse.ArgumentParser(description="Print image to terminal")
    parser.add_argument("image_paths", help="Path to image(s)", nargs="*")
    parser.add_argument("-c", "--cols", type=int, help="Columns of image")
    parser.add_argument("-r", "--rows", type=int, help="Rows of image")
    args = parser.parse_args()

    if len(args.image_paths) == 1:
        # Fill terminal by default
        if args.image_paths == ["-"]:
            # Read directly from stdin
            image = process_image(sys.stdin.buffer, args.cols, args.rows)
            with safe_print():
                for text_row in image:
                    print(text_row)
        path = Path(args.image_paths[0])
        if is_valid_image(path):
            image = process_image(path, args.cols, args.rows)
            with safe_print():
                for text_row in image:
                    print(text_row)
    else:
        # Show thumbs and filenames
        if not args.image_paths:
            image_paths = Path().iterdir()
        else:
            image_paths = (Path(path) for path in args.image_paths)
        sorted_image_paths = sorted([path for path in image_paths if is_valid_image(path)])

        cols = args.cols
        if not cols:
            cols = 40

        blank_line = " " * cols
        column_separator = "  "
        row_separator = "\n"

        term_cols, term_rows = os.get_terminal_size(1)
        images_per_row = term_cols // (cols + len(column_separator))

        current_row_images = []
        current_row_paths = []
        for path in sorted_image_paths:
            current_row_images.append(process_image(path, cols, args.rows))
            current_row_paths.append(path)
            if len(current_row_images) == images_per_row or path == sorted_image_paths[-1]:
                max_rows = max([len(im) for im in current_row_images])
                print(column_separator.join(["{:{}}".format(str(path), cols) for path in current_row_paths]))
                for line in range(max_rows):
                    image_lines = [im[line] if len(im) > line else blank_line for im in current_row_images]
                    output = column_separator.join(image_lines)
                    with safe_print():
                        print(output)
                print(row_separator, end="")
                current_row_images = []
                current_row_paths = []


if __name__ == "__main__":
    main()
