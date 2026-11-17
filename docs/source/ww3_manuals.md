# WW3 manuals

Two published versions of the WAVEWATCH III user manual, linked rather than copied:

| Version | Link | Notes |
|---|---|---|
| 6.07 (March 2019) | [manual.pdf](https://github.com/NOAA-EMC/WW3/wiki/files/manual.pdf) (NOAA-EMC WW3 wiki, 466 pp.) | The last released manual: NOAA/NWS/NCEP/MMAB Tech. Note 333. Cite this one. |
| 7.14 (draft, April 2022) | [manual_WW3.pdf](https://data-ww3.ifremer.fr/TRAINING/DOC/manual_WW3.pdf) (Ifremer WW3 training site, 483 pp.) | Marked "DRAFT, please do not refer to this manuscript"; it asks readers to cite 6.07. |

The LaTeX source of the manual is also in every WW3 checkout, under `WW3/manual/` (in the CESM
sandbox: `components/ww3/WW3/manual/`). It is updated with the code, so it can be newer than both
PDFs: its `IC4` section (`manual/eqs/ICE4.tex`) describes methods 1 to 10, while both PDFs stop at
7. Method 10, used by CESM's `wgx3v7` wave grid (`IC4METHOD = 10`), is only in the source.

## Where the ice physics is

| Topic | 6.07 page | 7.14 page | Source file |
|---|---|---|---|
| Wave-ice source terms, overview (`IC1`–`IC5`, `IS1`/`IS2`) | 79 (§2.4) | 84 (§2.4) | `eqs/sourceice.tex` |
| `IC4`: empirical/parametric damping by sea ice | 87 (§2.4.4) | 92 (§2.4.4) | `eqs/ICE4.tex` |
| Ice source term integration (`ICNUMERICS`) | 160 (§3.7) | 168 (§3.7) | |
| `IC0`: simple ice blocking (ice as land) | 162 (§3.8) | 169 (§3.8) | `num/ice.tex` |
| Switch list (`IC0`–`IC4`) | | in §5.9.2 (from 252) | `impl/switch.tex`, lines 118–122 |

`IC0` treats ice above a critical concentration as land; `IC1`–`IC5` damp waves inside the ice
as a source term. The manual says to use one approach or the other, not both (`num/ice.tex`,
line 61). CESM builds WW3 with `IC4`.
