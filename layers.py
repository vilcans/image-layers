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
parser.add_argument(
    '--jsonp', help='Output JSONP, using the specified function name'
)
parser.add_argument('file', nargs='+', help='Input image files')
args = parser.parse_args()

image_list = []
image_by_id = {}


def process_file(input_filename):
    if not input_filename.startswith(args.base):
        sys.stderr.write(
            '%s does not start with %s\n' % (input_filename, args.base)
        )
        sys.exit(1)

    relative_filename = input_filename[len(args.base):].lstrip('/')
    dirname, filename = os.path.split(relative_filename)

    basename, extension = os.path.splitext(filename)
    output_filename = os.path.join(args.dir, relative_filename)
    config_filename = os.path.splitext(input_filename)[0] + '.json'
    if os.path.exists(config_filename):
        config = json.load(open(config_filename))
    else:
        config = {}

    image = Image.open(input_filename)
    bands = image.getbands()
    if bands[-1] != 'A':
        sys.stderr.write(
            'Warning: Image without alpha channel: %s %s\n' %
            (input_filename, bands)
        )
        alpha_channel = image.convert('RGBA').split()[-1]
    else:
        alpha_channel = image.split()[-1]

    if config.get('autocrop', True):
        bounds = alpha_channel.getbbox()
        image = image.crop(bounds)
    else:
        bounds = (0, 0) + image.size
    target_dir = os.path.join(args.dir, dirname)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    image.save(output_filename)

    id = os.path.splitext(relative_filename)[0]
    data = {
        'id': id,
        'src': output_filename,
        'x': bounds[0] + config.get('x', 0),
        'y': bounds[1] + config.get('y', 0),
        'width': bounds[2] - bounds[0],
        'height': bounds[3] - bounds[1],
    }
    if id in image_by_id:
        sys.stderr.write(
            'Duplicate ID: %s (%s and %s)' %
            (id, image_by_id[id]['src'], data['src'])
        )
        sys.exit(1)

    image_list.append(data)
    image_by_id[id] = data


for input_filename in args.file:
    process_file(input_filename)

if args.jsonp:
    sys.stdout.write(args.jsonp)
    sys.stdout.write('(')
    json.dump(image_list, sys.stdout, indent=2)
    sys.stdout.write(');')
else:
    json.dump(image_list, sys.stdout, indent=2)
# Recommended commands after this:
# find -name '*.png' | xargs optipng -o7
# find -name '*.png' | xargs advdef -z4
