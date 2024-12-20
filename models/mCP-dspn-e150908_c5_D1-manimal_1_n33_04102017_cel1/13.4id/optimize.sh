#!/bin/bash -e

export IPYTHONDIR="`pwd`/.ipython"
#export IPYTHON_PROFILE=ipyparallel.${SLURM_JOBID}
export IPYTHON_PROFILE=default
ipython profile create --profile=${IPYTHON_PROFILE}

ipcontroller --init --sqlitedb --ip='*' --profile=${IPYTHON_PROFILE} \
  --HeartMonitor.period=10000 \
  --HeartMonitor.max_heartmonitor_misses=1500 &
sleep 30
srun ipengine --profile=${IPYTHON_PROFILE} --timeout=60 &
sleep 30

rm -rf x86_64
nrnivmodl ./mechanisms >/dev/null

START=$(date +%s)
python optimize.py
END=$(date +%s)

rm -rf std.err __pycache__ .ipython x86_64

echo Time elapsed: $(($END - $START)) seconds.
