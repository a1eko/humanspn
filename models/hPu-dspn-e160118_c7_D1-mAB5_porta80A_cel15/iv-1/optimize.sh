#!/bin/bash -e

export IPYTHONDIR=${SCRATCH}/${SLURM_JOB_ID}
export IPYTHON_PROFILE=default

#ipython profile create --profile=${IPYTHON_PROFILE}
#ipcontroller --init --sqlitedb --ip='*' \
#  --profile=${IPYTHON_PROFILE} \
#  --HeartMonitor.period=10000 \
#  --HeartMonitor.max_heartmonitor_misses=1500 &

ipython profile create --profile=${IPYTHON_PROFILE}
ipcontroller --init --sqlitedb --ip='*' \
  --profile=${IPYTHON_PROFILE} \
  --HeartMonitor.max_heartmonitor_misses=0 &

sleep 30
srun ipengine --profile=${IPYTHON_PROFILE} --timeout=60 &
sleep 30

rm -rf x86_64
nrnivmodl ./mechanisms >/dev/null

SECONDS=0
python optimize.py
echo "Elapsed time: $SECONDS seconds ($((SECONDS / 3600))h $(((SECONDS / 60) % 60))m $((SECONDS % 60))s)"

rm -rf __pycache__ x86_64 "${SCRATCH}"/"${SLURM_JOB_ID}"{,.std.err}
