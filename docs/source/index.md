# MESAWAVE

A global ensemble of ocean wave climate projections: WAVEWATCH III forced by MESACLIP.

::::{grid} 1 1 3 3
:gutter: 3

:::{grid-item-card} {octicon}`book` Proposal
:link: proposal.pdf

The full plan (PDF).
:::

:::{grid-item-card} {octicon}`database` MESACLIP experiments
:link: mesaclip_experiments
:link-type: doc

Available datasets and the MESAWAVE run matrix.
:::

:::{grid-item-card} {octicon}`table` Variables the models can request
:link: stream_data_requirements
:link-type: doc

What WW3, MOM6 and CICE need.
:::

:::{grid-item-card} {octicon}`tools` Stream construction
:link: stream_construction
:link-type: doc

How to build CDEPS streams from MESACLIP data.
:::

:::{grid-item-card} {octicon}`plug` Adding MESACLIP to CDEPS
:link: adding_mesaclip_to_cdeps
:link-type: doc

The PR, the five scenario modes, and the datamode code.
:::
::::

## Where to start

Read the pages in this order:

1. **[Proposal](https://manishvenu.github.io/mesawave/proposal.pdf)**: why the project exists, the
   WW3 mesh, and which runs, members and time slices are planned.
2. **[MESACLIP experiments](mesaclip_experiments.md)**: what data exists. Grids, GDEX datasets,
   case names, the MESAWAVE run matrix, and every variable MESACLIP saved.
3. **[Variables the models can request](stream_data_requirements.md)**: what WW3, MOM6 and CICE
   import, and whether MESACLIP supplies each field directly, as a stand-in, computed, or not at
   all. The best single page for the science compromises.
4. **[Stream construction](stream_construction.md)**: how MESACLIP files become CDEPS streams. Time
   settings, meshes, variable mapping and the generator scripts. For changing or debugging the
   forcing.
5. **[Adding MESACLIP to CDEPS](adding_mesaclip_to_cdeps.md)**: the PR, the five scenario modes,
   `DATM_MESACLIP_CASE`, and the custom datamode code. For work on the CESM side.
6. **Discussions** (in the sidebar): dated planning notes, for how decisions were reached.

```{toctree}
:maxdepth: 1
:caption: Notes
:hidden:

mesaclip_experiments
stream_data_requirements
stream_construction
adding_mesaclip_to_cdeps
```

```{toctree}
:maxdepth: 1
:caption: Discussions
:glob:
:reversed:

discussions/*
```
