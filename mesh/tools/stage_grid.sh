#!/bin/bash -l
# usage (inside a job): stage_grid.sh BUILD [CASEROOT]
# Stages the mesh build $SCRATCH/mesawave_mesh/build/BUILD/BUILD.ww3 as CESM's wu025r005 WW3 grid.
# Writes /glade/work/manishrv/ww3_mesh/grid_inp/BUILD/ (mesh.msh, ww3_grid.nml, namelists.nml,
# wu025r005_ESMFmesh.nc, mod_def.ww3), then points grid_inp/wu025r005, the path CESM reads, at it.
# mod_def.ww3 is made by CASEROOT's own ww3_grid when given (it must match the case's WW3 build),
# else by the ww3_grid in tools/grid_inp_template.
set -eo pipefail
build=$1; caseroot=$2
here=$(cd "$(dirname "$0")" && pwd)
W=/glade/work/manishrv/ww3_mesh/grid_inp
G=$W/$build
mkdir -p "$G" && cd "$G"
cp -L "$SCRATCH/mesawave_mesh/build/$build/$build.ww3" mesh.msh
cp "$here/grid_inp_template/ww3_grid.nml" "$here/grid_inp_template/namelists.nml" .

if [ -n "$caseroot" ]; then
  exe=$(cd "$caseroot" && ./xmlquery --value EXEROOT)/wav/obj/ww3_grid; env=$caseroot/.env_mach_specific.sh
else
  exe=$here/grid_inp_template/ww3_grid; env=$here/derecho_ww3_env.sh
fi
rm -f mod_def.ww3
(source "$env" >/dev/null 2>&1 && "$exe" > ww3_grid.log 2>&1) || { tail -20 ww3_grid.log; exit 1; }
[ -s mod_def.ww3 ] || { echo "no mod_def.ww3"; tail -20 ww3_grid.log; exit 1; }
echo "mod_def.ww3 from $exe"

PY="/glade/u/apps/opt/conda/envs/npl/bin/python -I"
$PY "$here/ww3_msh_to_esmf.py" mesh.msh wu025r005_ESMFmesh.nc
ln -sfn "$build" "$W/wu025r005"
$PY -c "import netCDF4; print('wu025r005 ->', '$build', 'elementCount', netCDF4.Dataset('wu025r005_ESMFmesh.nc').dimensions['elementCount'].size)"
