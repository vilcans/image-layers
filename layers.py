#!/usr/bin/env python

import json
import sys
import os.path
import argparse
from PIL import Image

parser = argparse.ArgumentParser(description='Crop and position images')
parser.add_argument(
    '--base', default='',
    help='Prefix to remove from input file names (include slash)'
)
parser.add_argument('--dir', default='images', help='Output directory')
parser.add_argument('file', nargs='+', help='Input image files')
args = parser.parse_args()

data = {}

for input_filename in args.file:
    if input_filename.startswith(args.base):
        relative_filename = input_filename[len(args.base):]
    dirname, filename = os.path.split(relative_filename)

    basename, extension = os.path.splitext(filename)
    output_filename = os.path.join(args.dir, filename)

    image = Image.open(input_filename)
    bounds = image.getbbox()
    cropped = image.crop(bounds)
    cropped.save(output_filename)

    d = data
    if dirname:
        for subdir in dirname.split('/'):
            d = d.setdefault(subdir, {})

    d[basename] = {
        'url': output_filename,
        'x': bounds[0],
        'y': bounds[1],
        'width': bounds[2] - bounds[0],
        'height': bounds[3] - bounds[1],
    }

json.dump(data, sys.stdout, indent=2)

# Recommended commands after this:
# find -name '*.png' | xargs optipng -o7
# find -name '*.png' | xargs advdef -z4
