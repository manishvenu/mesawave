#!/bin/bash -l
# usage (inside a job): run_mesh.sh PREFIX SCALE [SIZEFILE] [rows|icos] [ITMAX]; outputs and log go to $out/PREFIX/
set -eo pipefail
here=$(cd "$(dirname "$0")" && pwd)
module load ncarenv/25.10 && module load matlab/R2024b   # R2024b needs ncarenv >= 24.12
out=${SCRATCH:-/glade/derecho/scratch/$USER}/mesawave_mesh/build/$1   # per-run dir: OM2D writes fixed-name temp files
sizefile=${3:-sizefx_na1000_ot500_hull.nc}
layout=${4:-rows}
itmax=${5:-100}
mkdir -p "$out" && cd "$out"
matlab -nodisplay -batch "addpath('$here'); make_mesh('$1', $2, '$sizefile', '$layout', $itmax)" 2>&1 | tee "$out/$1.log"
