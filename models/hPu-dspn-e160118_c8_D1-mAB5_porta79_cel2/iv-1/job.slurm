#!/bin/bash -l

#SBATCH --job-name=bpopt
#SBATCH --ntasks=128
#SBATCH --ntasks-per-node=128
#SBATCH --cpus-per-task=1
#SBATCH --account=naiss2023-5-205
#SBATCH --partition=main
#SBATCH --time=00:59:00
#SBATCH --error=/cfs/klemming/scratch/a/%u/%j.std.err
#SBATCH --output=std.out

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

./optimize.sh
