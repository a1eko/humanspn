#!/bin/bash -l

#SBATCH --job-name=bpopt
#SBATCH --nodes=8
#SBATCH --cpus-per-task=1
#SBATCH --account=ich030
#SBATCH --time=01:59:00
#SBATCH --partition=normal
#SBATCH --constraint=mc
#SBATCH --error=/scratch/snx3000/%u/%j.std.err
#SBATCH --output=std.out

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

./optimize.sh
