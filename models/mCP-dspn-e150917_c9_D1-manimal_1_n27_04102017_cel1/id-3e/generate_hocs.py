#!/usr/bin/env python3

'''Example for generating hoc templates

 $ python generate_hocs.py

 Will read 'hall_of_fame.json' and save 'Cell_*.hoc' files,
 which can be loaded in neuron with:
     'load_file("path/Cell_0.hoc")'
 Then the hoc template needs to be instantiated with a morphology
     cell = Cell_0("path/")
 or
     cell = Cell_0("path/", "alternative_morphology.swc")
 if an alternative morphology reconstruction should be used (SWC, ASC or HD5).
'''
from __future__ import print_function
from collections import OrderedDict
import json
import sys

from bluepyopt.ephys.models import CellModel
import cell_model

def main():
    '''main'''
    with open('hall_of_fame.json') as fp:
        hof = json.load(fp, object_pairs_hook=OrderedDict)
    for i, param_values in enumerate(hof):
        cell_name = 'Cell_%d' % i
        cell = cell_model.create(cell_name)
        print(cell_name)
        with open(cell_name + '.hoc', 'w') as fp:
            fp.write(cell.create_hoc(param_values))

if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__)
    else:
        main()
