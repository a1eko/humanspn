#!/bin/bash -e

CUT=${CUT:-5}           # cut plane thickness

RECS=$1
RECS=${RECS:-"../corrected"}

for f in $RECS/*.swc; do
        rep=rep$RANDOM.swc
        n=$(basename $f .swc)
        cp $f $rep

        echo -n "sanitizing $n ... "
        cuts=$(swc find $rep -p 3 -c $CUT)
        stems=$(swc find $rep -n $cuts --stem)
        swc modify $rep -i $stems -u -o $rep

        if grep -q ' 3 ' $rep; then
                mv $rep $n-san.swc
                echo done
        else
                rm $rep
                echo FAIL
        fi
done
