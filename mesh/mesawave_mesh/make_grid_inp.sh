#!/bin/bash
# usage (inside a job): make_grid_inp.sh STAGEDIR GRIDNAME
# STAGEDIR holds mesh.msh, ww3_grid.nml, namelists.nml and ww3_grid; writes mod_def.ww3 and GRIDNAME_ESMFmesh.nc
set -eo pipefail
G=$1; name=$2
tools=$(cd "$(dirname "$0")/../tools" && pwd)   # copies of Alper's sandbox tools + wu025r004 case env
T=$tools/ww3_msh_to_esmf.py
cd "$G" && source $tools/derecho_ww3_env.sh >/dev/null 2>&1   # ww3_grid was built in this env; it has MKL
./ww3_grid > ww3_grid.log 2>&1; echo "ww3_grid exit $?"
grep -A2 "WARNING" ww3_grid.log | head -20
/glade/u/apps/opt/conda/envs/npl/bin/python -I $T mesh.msh ${name}_ESMFmesh.nc
