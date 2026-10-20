# MESAWAVE

A global ensemble of ocean wave climate projections: WAVEWATCH III forced by MESACLIP.

::::{grid} 1 1 3 3
:gutter: 3

:::{grid-item-card} {octicon}`book` Proposal
:link: proposal.pdf

The full plan (PDF).
:::

:::{grid-item-card} {octicon}`plug` MESACLIP in CESM
:link: mesaclip_cesm_modes
:link-type: doc

The DATM and DOCN modes.
:::

:::{grid-item-card} {octicon}`table` Coupling fields
:link: stream_data_requirements
:link-type: doc

What WW3, MOM6 and CICE need.
:::

:::{grid-item-card} {octicon}`workflow` Coupling flow
:link: coupling_flow
:link-type: doc

Which MESACLIP variables connect where.
:::
::::

```{toctree}
:maxdepth: 1
:caption: Notes
:hidden:

mesaclip_cesm_modes
stream_data_requirements
coupling_flow
adding_stream_data
```

```{toctree}
:maxdepth: 1
:caption: Discussions
:glob:
:reversed:

discussions/*
```
