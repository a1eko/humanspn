#!/bin/bash -e

OPT=${OPT:-0}           # repair mode (0, 1 or 2)
NREP=${NREP:-99}        # number of repair candidates to generate
DMIN=${DMIN:-0.50}      # min diameter of terminal sections without outliers (2 STD)
DMAX=${DMAX:-1.00}      # max diameter of terminal sections without outliers (2 STD)
CUT=${CUT:-20}          # cut plane thickness

RECS=$1
RECS=${RECS:-"../corrected"}

POOL=$2
POOL=${POOL:-"../sanitized"}

START=$(date +%s)
parallel OPT=$OPT NREP=$NREP DMIN=$DMIN DMAX=$DMAX CUT=$CUT POOL=$POOL repair_one.sh ::: $RECS/*.swc
END=$(date +%s)

echo Time elapsed: $(($END - $START)) seconds.
