#!/bin/bash -e

SAMPLE=${SAMPLE:-3.0}      # resample with fixed resolution
SCALEX=${SCALEX:-1.01}     # recover dend length loss due to resampling
SCALEY=${SCALEY:-1.01}     #
SCALEZ=${SCALEZ:-1.01}     #
STRETCH=${STRETCH:-0.0}    # stretching strength
SMOOTH=${SMOOTH:-0}        # smoothing iterations

RECS=$1
RECS=${RECS:-"../repaired/selected"}

for f in $RECS/*.swc; do
        rep=rep$RANDOM.swc
        n=$(basename $f .swc)
        cp $f $rep

        echo -n "postprocessing $n ... "
        swc modify $rep -m $SMOOTH -t $STRETCH -s $SCALEX $SCALEY $SCALEZ -o $rep
        swc repair $rep -r $SAMPLE -o $rep

        rsoma=$(grep "^1 1 " $rep | cut -d' ' -f6)
        inside=$(swc find $rep -p 2 3 -i $rsoma --comp lt)
        swc repair $rep -l $inside -o $rep

        mv $rep $n-post.swc
        echo done
done
