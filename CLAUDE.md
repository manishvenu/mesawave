# CLAUDE.md

Guidance for Claude Code in this repo. Claude: keep this file current. When an
open question is answered, move it to "Decisions" with the answer.

## Project

MESAWAVE: a global ensemble of ocean wave climate projections. WAVEWATCH III
(WW3) runs standalone on a global unstructured mesh, forced one way by MESACLIP
output through CESM's data models (CDEPS). The full plan is
`docs/source/proposal.pdf`. Current thinking is in the newest file in
`docs/source/discussions/`.

- **WW3 mesh:** from a NOAA collaborator. 1.67M nodes, 25 km open ocean,
  10 km coasts, 5 km US coasts, 600 s implicit timestep.
- **MESACLIP:** CESM1.3 high-res (0.25° atmosphere, 0.1° ocean and sea ice).
  https://project.cgd.ucar.edu/projects/MESACLIP/. 10-member historical
  ensemble plus future transient runs; PI control, historical and some future
  runs are on GDEX.
- **Runs:** members 5, 9, 10 with 6-hourly forcing: historical 1950–2005, and
  RCP 2.6/4.5/6.0/8.5 for 2006–2020, 2040–2060, 2080–2100. Member 10 with
  1-hourly forcing for 2000–2020.
- **Forcing:** 6-hourly 10 m winds; daily surface currents, ice concentration
  and ice thickness; floe diameter derived from concentration and thickness.
- **Later:** possible WW3-MOM6-CICE6 coupled runs, which need full DATM
  forcing, not just winds.

## Layout

- `code/`: scripts for the user: `describe_mesaclip_variables.py` and
  `list_mesaclip_variables.py` print what MESACLIP has on GDEX. Keep these simple.
- `code/claude/`: tooling Claude runs. `generate_{datm,docn,dice}_streams.py` write CPLHIST-style
  CDEPS streams files for MESACLIP, blank where unknown and checked for
  required fields. `cdeps_streams.py` is the shared writer.
  `add_mesaclip_to_cesm.py` (data in `mesaclip.py`) regenerates the MESACLIP XML
  and cap/CMake registration on the `cdeps/` submodule, starting from
  `stream-daterange`; review and commit the result on the stack branches.
  `verify_a_case.py RUNDIR` checks the A case's coupler history against GDEX.
  `coupler_fields.py CPL_HI [CPL_HI_TEST]` lists what the mediator sends each model
  (and what a test case lacks against a reference).
  `check_ww3_forcing.py CPL_HI WW3_HI` compares WW3's history (`CUR AST WLV ICE IC1 IC5`
  in its field list) with what the mediator sent, to show which imports WW3 kept.
- `cdeps/`: submodule on `manishvenu/CDEPS` `mesaclip-dice`, the top of a GitHub
  stack of PRs in the fork, on `cdeps1.0.101`: #5 `stream-daterange` → `main`
  (`%daterange`), #1 `mesaclip-datm` → `stream-daterange`, #2 `mesaclip-docn` →
  `mesaclip-datm`, #3 `mesaclip-dice` → `mesaclip-docn`. All CESM changes live
  here. Change a component on its branch, then restack the branches above it
  (force-pushes need the user's OK). Don't run `gh stack sync`: it rebases onto
  the fork's `main`, 133 commits past `cdeps1.0.101`.
- `docs/source/`: Sphinx source, Markdown via MyST. `index.md` links the
  proposal and auto-lists `discussions/*` newest first.
- `docs/source/discussions/YYYY-MM-DD.md`: dated planning notes, one per discussion.

## Docs

- Build: `pip install -r docs/requirements.txt`, then
  `sphinx-build -b html docs/source docs/build/html`.
- `.github/workflows/docs.yml` builds on every push and PR, and deploys to
  https://manishvenu.github.io/mesawave/ from `main` only.
- Theme: Shibuya with the `cyan` accent (`docs/source/conf.py`), sphinx-design
  cards on the index, small overrides in `docs/source/_static/custom.css`.
- `docs/build/` is git-ignored. Never commit build output.
- Non-Markdown files (e.g. PDFs) only reach the site if a page links them with
  `{download}` or they are in `html_extra_path` (the proposal, at `/proposal.pdf`).

## CDEPS stream files

- Format: `<file id="stream" version="2.0">` with one `<stream_info name="...">`
  per stream. Tags: `taxmode`, `tintalgo`, `readmode`, `mapalgo`, `dtlimit`,
  `year_first`, `year_last`, `year_align`, `vectors`, `meshfile`,
  `lev_dimname`, `datafiles/file`, `datavars/var`, `offset`.
- `<var>` is `name_in_file  name_in_model`.
- Leave anything unknown blank rather than guessing. CDEPS rejects blank or
  invalid `taxmode`, `mapalgo`, `tintalgo`, `readmode`, so fill these before a run.
- CDEPS does not convert units or rotate grid-relative vectors.
- `%daterange` (stack PR #5) in a `<file>` stands for the `<start>-<end>` of CESM
  time-series names; buildnml expands it to the files covering the stream years,
  checks gaps and overlaps, and marks the stream `check_dates`, so the model checks
  each file's times against its name (only for those streams). It is expanded after
  `user_nl_*_streams` changes, with their `year_first`/`year_last` and `datafiles`.

## Reference CESM source (GLADE)

`~/work/installs/CESM_crocodash/components/`:
- `cdeps/streams/dshr_stream_mod.F90`: stream XML parser.
- `ww3/WW3/model/src/wav_import_export.F90`: WW3 imports `Sa_u10m`, `Sa_v10m`,
  `Sa_tbot`, `So_u`, `So_v`, `So_t`, `Si_ifrac`, `Si_thick`; also `So_bldepth`
  (CESM-coupled) and `Si_floediam` (when coupled to CICE).
- `cmeps/mediator/esmFldsExchange_cesm_mod.F90`: which component supplies each field.

## CrocoDash (regional tests)

CrocoDash builds regional MOM6 cases in CESM, optionally with active WW3 and
CICE. Use it to test MESACLIP forcings on a small regional domain before
global runs.

- Code: `~/documents/croc/regional_mom_workflows/CrocoDash`
  (`CROCODILE-CESM/CrocoDash`), part of the `croc` monorepo, whose `CLAUDE.md`
  has the minimal case-setup pattern. Don't switch that checkout's branch or
  edit it; use a worktree.
- Env: `dev_cd` (`/glade/work/manishrv/conda-envs/dev_cd`) with
  `ESMFMKFILE=/glade/work/manishrv/conda-envs/dev_cd/lib/esmf.mk`. Don't install
  into the shared workshop `CrocoDash` env.
- CESM: `~/work/installs/CESM_crocodash` (`CROCODILE-CESM/CESM`, branch
  `crocodash`). Cases go in `~/croc_cases/`, inputs in `~/scratch/croc_input/`.
- Every case needs `configure_forcings` then `process_forcings`.
  `override=True` wipes the inputdir, so recreate cases against a fresh one.
- Only MOM6 compsets are allowed (`case.py` asserts `"MOM6"` in the compset).
  WW3 reuses the regional ocean grid.
- Regional wave compsets, defined in
  `components/mom/cime_config/config_compsets.xml`:
  - `GWR_JRA`: DATM + CICE + MOM6 + WW3 (wave-ice-ocean).
  - `CWR_JRA`: DATM + DICE%SSMI + MOM6 + WW3 (wave-ocean, data ice).
  - Variants add MARBL BGC (`*1850MARBL*`), GLOFAS runoff (`*_GLOFAS`), or
    repeat-year JRA (`CWR_JRA_RYF`).
- DATM stream changes go in the case's `user_nl_datm_streams` as
  `streamname:field = value`. Only streams the compset already defines can be
  changed (`components/cdeps/cime_config/stream_cdeps.py`).

## MCP servers

`.mcp.json` connects the three croc MCP servers. They run from `dev_cd`, and
their code is in `~/documents/croc/dev/`.
- `crocodash`: create cases, configure and process forcings.
- `cesm-runner`: case setup/build/submit, xmlquery/xmlchange, logs, crocontainer.
- `ocean-debugger`: log triage, MOM_input inspection, CFL/timestep checks,
  expert domain knowledge.

Say so before slow calls (`create_case`, `process_forcings`, `case_build`),
and flag any that run past ~4 minutes.

## Status (2026-10-27)

- MESACLIP DATM/DOCN/DICE modes are done. `docs/source/adding_mesaclip_to_cdeps.md`
  has the PRs, the five scenario modes, `%daterange`, `DATM_MESACLIP_CASE` and the
  datamode code.
- PRs: the stack manishvenu/CDEPS#5, #1, #2, #3. The older combined draft
  CROCODILE-CESM/CDEPS#2 (fork branch `mesaclip`) is untouched; the org's `main`
  now tracks ESCOMP main, so merging there needs a rebase and a retest. The user
  moves org refs.
- Tests in the stack: #5 has `cime_config/test_stream_cdeps.py` (one plain-assert test
  of `%daterange`; `CIMEROOT=... python3 cime_config/test_stream_cdeps.py`). #3 adds two
  `aux_cdeps` tests to `testlist_dice.xml`, DATM/DOCN/DICE in MESACLIP modes forcing WW3
  on `T62_t232_wg37` with testmod `dice/mesaclip` (starts on the scenario's first year):
  `SMS_D_Ld3_P12` (HIST) and `ERS_Ld4_P12` (RCP45). Both passed on 2026-10-27 (31 and
  14 min, 56 GB). WW3 on `wt232` took 98% of the run time; one task ran out of memory.
- The CESM_crocodash install's `components/cdeps` is on `mesaclip-dice` (ddf810a, as pushed);
  the earlier manual copies are in its `stash@{0}`. Its `ccs_config/modelgrid_aliases_nuopc.xml`
  has an uncommitted `mesaclip_ne120np4` alias (atm `ne120np4` only; a tester's, minus lnd).
- CrocoDash + MESACLIP: `~/croc_cases/mesaclip_crocodash_alaska` (DATM/DICE MESACLIP-HIST,
  regional MOM6, Casper, `replay.sh`). Needs an `ne120np4` alias without `not_compset="_MOM"`:
  visualCaseGen keeps a grid's `not_compset` only if every alias using it has it
  (`cime_interface.py` `_process_domain_constraints`), and all CESM `ne120` aliases are `_MOM`-excluded.
  CrocoDash's `StreamYears` rewrites every DATM stream's years/`datafiles`, which works only
  with the 2026-10-28 `%daterange` fix. CrocoDash picked 62 tasks; 162×66 MOM6 needs ≤ ~16.
  Ran 3 days (job 6431558, 16 tasks, 23 sim yr/day) with CrocoDash's own overrides.
- The A case needs ~136 GB, more than Derecho's develop queue gives (CIME asks 10 GB
  per task up to 12 tasks, then that share of a node's 235 GB, so ≤ 120 GB; 63 tasks
  max): run it on Casper or a full `main` node.
  `~/croc_cases/mesaclip_dice_a_hist_derecho` (main, 128 tasks, 2 days, stream
  years 2000–2000, ocean history `So_t:So_s:So_u:So_v`) verified the stack: run
  starts on Jan 1 of the stream year (`extend`), currents match `ANGLE`-rotated
  GDEX to 5e-8 (compare coupler `So_u/So_v` with 0.01 × rotated `U1_1/V1_1`).
  The Casper `mesaclip_dice_a_hist` is left at STOP_N=2, stream years 1999–2000.
- Verified test cases: `~/croc_cases/mesaclip_a_hist` (A case, `ne120_t12`, SICE),
  `~/croc_cases/mesaclip_ww3_alaska` (regional WW3 on a 162×66 Bering Sea grid,
  SICE), `mesaclip_dice_a_hist` and `mesaclip_dice_ww3_alaska` (16 tasks; WW3 gets
  9 of its 10 imports, all but `Si_floediam`). On 2026-10-22, rebuilt on the stack (1 day,
  job 6340575), WW3's history matched the coupler for winds, currents, ice fraction and
  `Sa_tbot − So_t` (≤ 1e-5); ice thickness stayed at WW3's 0.5 m default, floe diameter
  1000 m, water level 0. `user_nl_ww3` keeps the longer field list. Each has `replay.sh`; `user_nl_*`
  edits are in the case dirs. WW3 writes `ww3.hi` only when `HIST_OPTION` is set: the cap takes
  the driver's `history_option`, not `wav_in`'s, and the same setting writes the mediator's `cpl.hi`.
- Global unstructured WW3: `~/croc_cases/mesaclip_ww3_wu2r05` (Derecho, 1 node/128 tasks on
  `main`, 10 days from 2000-01-01, member 010) tests ESMCI/ccs_config_cesm#310 + ESCOMP/WW3_interface#23
  in the sandbox `/glade/work/manishrv/installs/CESM_wu2r05` (CESM 16dd396; `ww3` branch
  `wu2r05-pr23` = e64dc4d + the PR's commits, two conflicts resolved by hand; `cdeps` on
  `mesaclip-dice`). Grid `a%ne120np4_l%null_oi%wu2r05_r%null_g%null_w%wu2r05_z%null_m%wu2r05`, so
  DOCN/DICE sit on the WW3 mesh. Job 7911442 (2026-10-22): 186 s init, 58.7 s/day (WAV 41 s), 98 GB;
  `check_ww3_forcing.py` matches winds, currents, ice fraction. Job 7911888 reran it with `U10`
  winds (55.8 s/day). `UBOT`/`VBOT` and `U10` `ww3.hi` from both cases are in
  `~/scratch/mesawave_u10_compare/{ubot,u10,ubot_wu2r05,u10_wu2r05}/`.
- Reference for what each model receives: `~/croc_cases/gwr_jra_cplhist`
  (GWR_JRA clone of `so1deg_wav_wavfix`, cpayne's `crocodile2026` CESM), 1 day
  with `HIST_OPTION=ndays`; its `cpl.hi` is the input to `coupler_fields.py`.
- Claude runs on Casper. Build, submit and `xmlquery` need Derecho:
  `ssh -o BatchMode=yes derecho '<command>'`. Keep jobs under 60 cores so they
  go through the develop queue fast.

## Open questions

1. **POP currents on U points.** The datamode rotates them to east/north, but
   they are read on the T-point mesh (about half a cell off).
3. **Wave-only regional tests through CrocoDash.** Done with plain CIME instead
   (`mesaclip_ww3_alaska`). No new WW3 rule is needed: DOCN satisfies the
   existing "WW3 needs an active or data ocean" rule. What still blocks CrocoDash
   (paths in CrocoDash's embedded `CrocoDash/visualCaseGen/`, which `dev_cd` uses):
   - `visualCaseGen/specs/relational_constraints.py`: "Custom grids can only be
     generated when MOM6 and/or CLM are selected" and "Custom OCN grids can
     only be generated for MOM6". These need relaxing for DOCN.
   - CrocoDash `case.py` also asserts `"MOM6"` in the compset.
   - Injection point: `visualCaseGen/initialize.py` passes
     `get_relational_constraints(cvars)`, a `{constraint: message}` dict, to
     `csp.initialize`. CrocoDash calls it from `Case.__init__` via
     `initialize_visualCaseGen(cesmroot)`.

## Decisions

- **WW3's winds: `UBOT`/`VBOT` × (10/`ZBOT`)^0.11** (2026-10-28, from Julio Bacmeister; was
  `U10` speed along `UBOT`/`VBOT` from 10-22, `UBOT`/`VBOT` before). A power law from the lowest
  CAM level (~64 m over ocean, `ZBOT`) to 10 m, about 0.82 at 60 m; no `U10` stream. For comparison,
  MESACLIP's `U10`/|`UBOT`| has an open-ocean median of 0.92 (0.84 above 20 m/s, 0.79 stable),
  and the `U10` winds cut Hs by 25% on wu2r05 (19% in Alaska) over 10 days. `BETAMAX`, if tuned,
  is tuned once on historical and held fixed. `Sa_u`/`Sa_v` stay `UBOT`/`VBOT`; `ZBOT` is `Sa_z`.
  Checked 2026-10-28 (Alaska, 1 day): DATM's `Sa_u10m` equals the formula to 4e-15; WW3's
  wind is 0.821 × the `UBOT` run's and 0.93–0.96 × the `U10` run's.
- **No runs span historical and future MESACLIP** (2026-10-16). Each run
  uses one MESACLIP scenario and member; combining them is out of scope.
- **MESACLIP enters CESM as CDEPS modes** (2026-10-16/19): `DATM%MESACLIP-<scenario>`,
  `DOCN%MESACLIP-<scenario>`, and `DICE%MESACLIP-<scenario>` with one case variable,
  `DATM_MESACLIP_CASE`, read by `mesaclip` datamodes copied from CPLHIST/SSMI, which
  also do unit conversions. DICE reads daily `aice_d` (%) from CICE history and divides
  by 100. `Si_floediam` is not provided (DICE%SSMI also doesn't provide it).
- **Stand-ins for fields MESACLIP lacks** (2026-10-16): 2 m `TREFHT`/`QREFHT` and
  `PS` (`h2`) for lowest-level T, q and p; potential temperature and density
  computed; direct shortwave = `FSDS` minus diffuse, split with JRA's fractions;
  topography from DATM's observed stream; WW3's 10 m winds as above.
- **6-hourly MESACLIP fields** (2026-10-16): `h2` is instantaneous (`UBOT`, `VBOT`,
  `ZBOT`, `PSL`, `PS`, `TREFHT`, `QREFHT`); `h4` holds 6 h means stamped at the
  window's end (`FSDS`, `FLDS`, `SOLSD`, `SOLLD`, `PRECT`, `PRECC`, `PRECSC`,
  `PRECSL`). With the stand-ins above that is enough for full DATM. Ocean
  fields are daily. HIST member 001 has no 6-hourly data, so it is ignored.
- **`So_t` and `Sa_tbot` are included** (2026-10-16): `SST` and `TREFHT` are in
  the streams.
- **`So_s` from MESACLIP `SSS`** (2026-10-21): daily POP `SSS`, × 1000 because the files hold kg/kg despite a g/kg label,
  in the DOCN streams; CICE and DICE (freezing point, `tfreeze_option = mushy`) import
  it. Without the stream, DOCN falls back to 34.7 psu as DOCN%SST does.

- **`Si_thick` = `hi_d` / `aice_d`** (2026-10-21): DICE computes it as CICE does
  (`vice/aice` where aice > puny, else 0). Before, WW3 got 0 everywhere.
- **`So_bldepth` = 0** (2026-10-21): WW3 wants a boundary-layer depth, not POP's
  mixed-layer depth `HMXL`; MESACLIP only has the daily maximum (`XBLT`). DOCN
  sends 0 (was 1e30). WW3 reads it into `HSL` but uses it only with `&LMPN`
  `LMPENABLED` and `HSLMODE = 1`. Both are off by default, but CESM's `wgx3v7`, `ww3a` and
  `wu2r05` grid inputs turn them on; then it changes only the Langmuir/Stokes fields WW3
  sends an ocean, not the waves. Check the NOAA mesh's input.
- **What standalone WW3 uses** (2026-10-22, corrected 2026-10-29): only winds and currents
  change the waves; ice fraction does not. `Sa_tbot − So_t` feeds only `STAB3` (build has
  `STAB0`). Without CICE the cap sets `inflags2(:) = .false.` (`wav_comp_nuopc.F90:1714`),
  which turns off all ice source terms (`w3srcemd.F90:2122`, and ice scaling at 1444);
  the other `IC4` call needs `IC_NUMERICS` (`w3srcemd.F90:1363`), default false
  (`w3gridmd.F90:2784`); `FICEN` blocking is `IC0` only and ice transparency needs
  `TRFLAG ≥ 3`. WW3 still reads the ice into `ICE` (history) and returns it as
  `Sw_ifrac_avg` (demand page has the links). `So_h` isn't advertised. Offset tests (3 days, Alaska, 10-day stream offsets; cases
  `~/croc_cases/mesaclip_ww3_offset_{control,irrelevant,relevant,icefrac}`, power-law winds):
  shifting everything but wind (`UBOT VBOT ZBOT`), currents and `aice_d` left waves and all
  600 restart spectral bins bit-for-bit identical (only `AS` changed); shifting those six
  changed the waves; shifting only `aice_d` changed `ICE` by up to 0.99 at ~1,100 of 6,996
  sea points and left the waves bit-for-bit identical. Earlier 10-28 test (`U10` winds) in
  `~/scratch/mesawave_offset_test/`.
- **`%daterange` in CDEPS for time-series files** (2026-10-22): one stream entry
  per variable, expanded at buildnml to the member's files for the stream years
  (all RCPs to 2100), with gap/overlap checks and a file-time-vs-name check in
  `dshr_stream_mod.F90`. Replaces explicit file lists and the per-case script.
  Mesh/weight sharing across streams and multi-file streams were considered and
  not wanted.
- **Currents rotated in the DOCN datamode, no preprocessing** (2026-10-22): `ANGLE`
  read from the current files at init, cos/sin regridded with the current
  stream's weights and renormalized, rotated as POP's coupler does. Verified on
  tx0.1 to 5e-8. Where the regridded cos/sin is shorter than 0.5 (stencil across
  POP's Arctic fold) the current is set to 0.
- **`taxmode = extend` for all MESACLIP streams** (2026-10-22, from review):
  averaged fields' edge records sit up to 12 h inside the year and scenario edges
  have no file beyond, so `limit` stopped runs on Jan 1 / Dec 31. Cost: a run past
  `DATM_YR_END` silently holds the last record.
- **Shortwave `coszen`** (2026-10-22): `FSDS`, `SOLSD`, `SOLLD` use `coszen` with
  offset −21600 (window start), like JRA; other h4 means stay `nearest`/−10800.
- **`Si_thick` from the final ice fraction** (2026-10-22): computed after DICE's
  SSMI code adjusts the fraction.

## Working rules

- Keep changes small and simple. Do only what's asked.
- Ask before committing or pushing. No `Co-Authored-By` lines in commits, and
  no @-mentions on GitHub.
- Run `module load gh` before using the `gh` CLI.
- Don't recursively scan GDEX/GLADE data collections. Look up specific paths.
- Never move, copy or delete anything in CESM inputdata.
