#!/bin/bash -e

SHRINK=${SHRINK:-1.0}   # shrinkage correction in z
JUMP=${JUMP:-20}        # z-jump value 

RECS=$1
RECS=${RECS:-"../adapted"}

for f in $RECS/*.swc; do
        rep=rep$RANDOM.swc
        n=$(basename $f .swc)
        cp $f $rep

        echo -n "correcting $n ... "
        swc repair $rep -k $SHRINK -n -o $rep

        jumps=$(swc find $rep -p 3 -z $JUMP)
        if [ -n "$jumps" ]; then
                swc repair $rep -z $jumps --zjump split -o $rep
        fi

        mv $rep $n-cor.swc
        echo done
done
