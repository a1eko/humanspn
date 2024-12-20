#!/bin/bash -e

THRESHOLD=${THRESHOLD:-2.0}

for f in *-rep.json; do
        n=$(basename $f '-rep.json')
        if ! zrank.py $n-aim.json $f -t $THRESHOLD; then
                echo $n rejected
        fi
done
