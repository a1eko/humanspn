#!/bin/bash -e

rm -rf x86_64
nrnivmodl ./mechanisms >/dev/null 2>&1

SECONDS=0
python3 variate.py hall_of_fame.json morphology/*.swc
#python3 variate.py one_par.json morphology/*.swc
echo Elapsed time: $(($SECONDS / 3600))h $((($SECONDS / 60) % 60))m $(($SECONDS % 60))s

rm -rf std.err __pycache__ x86_64
