#!/bin/bash -e

NREP=${NREP:-99}        # number of repair candidates to generate
DMIN=${DMIN:-0.50}      # min diameter of terminal sections without outliers (2 STD)
DMAX=${DMAX:-1.00}      # max diameter of terminal sections without outliers (2 STD)
CUT=${CUT:-20}          # cut plane thickness

f=$1
n=$(basename $f .swc)
rep=rep$RANDOM.swc

POOL=${POOL:-"../sanitized"}

OPT=${OPT:-0}
case $OPT in
        0) OPTS="--pool $POOL/*.swc" ;;
        1) OPTS="--force-repair" ;;
        2) OPTS="--force-repair --pool $POOL/*.swc" ;;
esac

echo -n "repairing $n ($NREP) ... "
mkdir -p $n-rep
rm -f $n-rep/*
for i in $(seq $NREP); do
        cp $f $rep
        thin=$(swc find $rep -p 3 -d $DMIN --comp lt)
        if [ -n "$thin" ]; then
                swc repair $rep -d $thin --diam value --diam-value $DMIN -o $rep
        fi

        thick=$(swc find $rep -p 3 -b 1 -d $DMAX --comp gt)
        if [ -n "$thick" ]; then
                swc repair $rep -d $thick --diam value --diam-value $DMAX -o $rep
        fi

        cuts=$(swc find $rep -p 3 -c $CUT)
        swc repair $rep -c $cuts $OPTS --seed $i -o $rep || true

        thin=$(swc find $rep -p 3 -d $DMIN --comp lt --sec)
        if [ -n "$thin" ]; then
                swc modify $rep -i $thin -u -o $rep
        fi
        thin=$(swc find $rep -p 3 -d $DMIN --comp lt)
        if [ -n "$thin" ]; then
                swc repair $rep -d $thin --diam value --diam-value $DMIN -o $rep
        fi

        thick=$(swc find $rep -p 3 -b 1 -d $DMAX --comp gt)
        if [ -n "$thick" ]; then
                swc repair $rep -d $thick --diam value --diam-value $DMAX -o $rep
        fi

        mv $rep $n-rep/$n-rep$i.swc
done

swc measure $n-rep/*swc -p 3 -a path -o $n-rep.json
echo done
