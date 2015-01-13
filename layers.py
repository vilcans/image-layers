#!/usr/bin/env python

import json
import sys
import os.path
import argparse
from PIL import Image, ImageChops

parser = argparse.ArgumentParser(description='Crop and position images')
parser.add_argument(
    '--base', default='',
    help='Prefix to remove from input file names (include slash)'
)
parser.add_argument('--dir', default='images', help='Output directory')
parser.add_argument(
    '--crop-top', type=int, default=0,
    help='Remove this many pixels from the top of all images'
)
parser.add_argument(
    '--crop-bottom', type=int, default=0,
    help='Remove this many pixels from the bottom of all images'
)
parser.add_argument(
    '--crop-left', type=int, default=0,
    help='Remove this many pixels from the left side of all images'
)
parser.add_argument(
    '--crop-right', type=int, default=0,
    help='Remove this many pixels from the right side of all images'
)
parser.add_argument(
    '--scale', type=float, default=1,
    help='Scaling factor, e.g. 0.5'
)
parser.add_argument(
    '--jsonp', help='Output JSONP, using the specified function name'
)
parser.add_argument('file', nargs='+', help='Input image files')
args = parser.parse_args()

image_list = []
image_by_id = {}

cropping = any(
    (args.crop_top, args.crop_bottom, args.crop_left, args.crop_right)
)


def scale(value):
    if args.scale is None:
        return value
    return int(value * args.scale + .5)


def images_are_equal(image1, image2):
    # From http://effbot.org/zone/pil-comparing-images.htm#exact
    if image1.size != image2.size:
        return False
    image1 = image1.convert('RGBA')
    image2 = image2.convert('RGBA')
    return ImageChops.difference(image1, image2).getbbox() is None


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
    if cropping:
        image = image.crop((
            args.crop_left, args.crop_top,
            image.size[0] - args.crop_left, image.size[1] - args.crop_bottom
        ))
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
    if args.scale is not None:
        image = image.convert('RGBA').resize(
            tuple(scale(s) for s in image.size),
            Image.ANTIALIAS
        )

    if (
        os.path.exists(output_filename) and
        images_are_equal(image, Image.open(output_filename))
    ):
        sys.stderr.write(
            'Not overwriting pixel-identical image %s\n' %
            output_filename
        )
    else:
        sys.stderr.write(
            'Writing image %s\n' %
            output_filename
        )
        image.save(output_filename)

    id = os.path.splitext(relative_filename)[0]
    data = {
        'id': id,
        'src': output_filename,
        'x': scale(bounds[0] + config.get('x', 0)),
        'y': scale(bounds[1] + config.get('y', 0)),
        'width': scale(bounds[2] - bounds[0]),
        'height': scale(bounds[3] - bounds[1]),
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
