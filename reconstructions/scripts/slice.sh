#!/bin/bash -e

SLICE=${SLICE:-1.0}     # delete nodes SLICE um above root

RECS=$1
RECS=${RECS:-"../corrected"}

for f in $RECS/*.swc; do
        rep=rep$RANDOM.swc
        n=$(basename $f .swc)
        cp $f $rep

        echo -n "slicing $n ... "
        sliced=$(swc find $rep -p 3 -s $SLICE)
        swc modify $f -i $sliced -u -o $rep

        mv $rep $n-sli.swc
        swc measure $n-sli.swc -a path -p 3 -o $n-sli.json
        echo done
done
