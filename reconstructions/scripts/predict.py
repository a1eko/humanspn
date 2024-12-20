#!/usr/bin/python3

"""
Generate morphometric predictions from sliced half-reconstructions.

Morphometric feature extraction must be done using `treem` command:
    swc measure <rec>-sli.swc -a path -o <rec>-sli.json
"""

import argparse
import json
import os

import numpy as np


factors = {
        'breadth': 1.0,
        'diam': 1.0,
        'dist': 1.0,
        'length': 2.0,
        'nbranch': 2.0,
        'nterm': 2.0,
        'order': 1.0,
        'path': 1.0,
        'seclen': 1.0,
        'xdim': 1.0,
        'ydim': 1.0,
        'zdim': 2.0
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', type=str, nargs='+',
            help='morphometrics of sliced reconstructions (json)')
    return parser.parse_args()


def main(args):
    values = dict()
    predict = dict()
    for rec in args.file:
        mmdat = json.load(open(rec))
        mmnam = os.path.basename(rec)
        mmnam = os.path.splitext(mmnam)[0]
        name = mmnam.replace('-sli', '')
        name += '-aim'
        predict[name] = {'dend': dict()}
        for feature in factors:
            dend = predict[name]['dend']
            value = mmdat[mmnam]['dend'][feature] * factors[feature]
            dend[feature] = {'mean': value}
            if feature not in values:
                values[feature] = list()
            values[feature].append(value * factors[feature])
    for name in predict:
        dend = predict[name]['dend']
        for feature in dend:
            dend[feature]['std'] = np.std(values[feature])

    for name in predict:
        with open(name + '.json', 'w') as fp:
            json.dump(predict[name], fp, indent=4)


if __name__ == '__main__':
    main(parse_args())
