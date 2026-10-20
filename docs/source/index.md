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

:::{grid-item-card} {octicon}`table` Coupling fields
:link: stream_data_requirements
:link-type: doc

What WW3, MOM6 and CICE need.
:::
::::

```{toctree}
:maxdepth: 1
:caption: Notes
:hidden:

mesaclip_experiments
stream_construction
adding_mesaclip_to_cdeps
stream_data_requirements
```

```{toctree}
:maxdepth: 1
:caption: Discussions
:glob:
:reversed:

discussions/*
```
