#!/bin/bash -l

#SBATCH --job-name=bpopt
#SBATCH --ntasks=288
#SBATCH --cpus-per-task=1
#SBATCH --account=ich030
#SBATCH --time=23:59:00
#SBATCH --partition=normal
#SBATCH --constraint=mc
#SBATCH --error=std.err
#SBATCH --output=std.out

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

./optimize.sh
