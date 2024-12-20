#!/bin/bash -e

rm -rf x86_64
nrnivmodl ./mechanisms >/dev/null 2>&1

START=$(date +%s)
python3 variate.py hall_of_fame.json morphology/*.swc
END=$(date +%s)

rm -rf std.err __pycache__ x86_64

echo Time elapsed: $(($END - $START)) seconds.
