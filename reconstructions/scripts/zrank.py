#!/usr/bin/python3

"""
Sort morphology reconstructions with z-score to the target values:
    zrank.py aim.json rep.json

    aim.json - morphometrics of the predicted reconstruction
    rep.json - morphometrics of the repaired reconstructions

Morphometric feature extraction must be done using `treem` command:
    swc measure rec.swc -a dist path -o rec.json
"""

import argparse
import json
import sys

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', type=str, nargs=2, help='input file (json)')
    parser.add_argument('-n', dest='number', metavar='<int>', type=int, default=1,
            help='list number of acceptable reconstructions [1]')
    parser.add_argument('-t', dest='thresh', metavar='<float>', type=float, default=3.0,
            help='Z-score threshold [3.0]')
    parser.add_argument('-v', dest='verbose', action='store_true',
            help='verbose print')
    return parser.parse_args()


def zscore(rec, ref, verbose=False):
    scores =list()
    for feature in ref:
        if feature in rec:
            score = abs(rec[feature] - ref[feature]['mean']) / ref[feature]['std']
            scores.append(score)
        if verbose:
            print(f'{feature=}, {score=}, {rec[feature]}, {ref[feature]["mean"]}')
    if verbose:
        print(f'mean z-score: {np.mean(scores)}')
    return np.mean(scores)


def main(args):
    predicted = json.load(open(args.file[0]))
    repaired = json.load(open(args.file[1]))

    for rec in repaired:
        if args.verbose:
            print()
            print(rec)
        score = zscore(repaired[rec]['dend'], predicted['dend'], verbose=args.verbose)
        repaired[rec]['zscore'] = score
    ranked = sorted(repaired, key=lambda x: repaired[x]['zscore'])

    err = 0
    for i, rec in enumerate(ranked):
        if i == args.number:
            break
        score = repaired[rec]['zscore']
        if score < args.thresh:
            print(rec)
        else:
            err = 1

    return err


if __name__ == '__main__':
    sys.exit(main(parse_args()))
