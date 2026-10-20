# Coupling flow diagrams

MESACLIP variables (left) flowing to coupler import fields (right) for each model component.
Generated from verified source: `code/list_mesaclip_variables.py` lists all available variables;
`wav_import_export.F90`, `esmFldsExchange_cesm_mod.F90`, and the MESACLIP datamodes confirm what
gets connected and how.

**Node colours:** green = correct variable (unit conversion only) · amber = stand-in or extra
computation · red = not supplied · purple = available in MESACLIP but not yet wired · grey = in
the file but not relevant to this model · dashed arrow = potential future connection.

## WW3

```{mermaid}
flowchart LR
    classDef yes    fill:#f0fdf4,stroke:#4ade80,color:#14532d
    classDef si     fill:#fffbeb,stroke:#fbbf24,color:#78350f
    classDef ns     fill:#fff1f2,stroke:#fca5a5,color:#7f1d1d
    classDef could  fill:#f5f3ff,stroke:#c4b5fd,color:#4c1d95
    classDef unused fill:#f8fafc,stroke:#e2e8f0,color:#94a3b8

    subgraph h2 ["cam.h2 · 6-hourly instantaneous (31 vars)"]
        UBOT["UBOT · ~60 m u-wind"]:::si
        VBOT["VBOT · ~60 m v-wind"]:::si
        U10w["U10 · real 10 m wind ⚠"]:::could
        TREFHTw["TREFHT · 2 m temperature"]:::si
        other_h2w["PS, PSL, ZBOT, QREFHT\n+ 27 others · not used by WW3"]:::unused
    end

    subgraph ocn ["pop.h.nday1 · daily (26 vars)"]
        SSTw["SST · °C"]:::yes
        U1_1w["U1_1 · surf u cm/s"]:::yes
        V1_1w["V1_1 · surf v cm/s"]:::yes
        SSSw["SSS · salinity ⚠"]:::could
        other_ocnw["HMXL, SSH_2, TAUX…\n+ 21 others · not used by WW3"]:::unused
    end

    subgraph ice ["cice.h1 · daily (10 vars)"]
        aice_dw["aice_d · ice conc. %"]:::yes
        hi_dw["hi_d · ice thickness ⚠"]:::could
        other_icew["uvel_d, vvel_d, Tsfc_d…\n+ 7 others"]:::unused
    end

    UBOT   -- "stand-in · bottom level ~60 m" --> Sa_u10m["Sa_u10m · 10 m wind u"]:::si
    VBOT   -- "stand-in · bottom level ~60 m" --> Sa_v10m["Sa_v10m · 10 m wind v"]:::si
    TREFHTw -- "stand-in · 2 m not lowest level" --> Sa_tbot["Sa_tbot · air temperature"]:::si
    SSTw   -- "°C → K via DOCN" --> So_t["So_t · SST"]:::yes
    U1_1w  -- "cm/s → m/s ×0.01 via DOCN" --> So_u["So_u · current u"]:::yes
    V1_1w  -- "cm/s → m/s ×0.01 via DOCN" --> So_v["So_v · current v"]:::yes
    aice_dw -- "% → fraction ÷100 via DICE" --> Si_ifrac["Si_ifrac · ice fraction"]:::yes
    hi_dw  -. "could derive ÷aice_d" .-> Si_thick["Si_thick · not supplied"]:::ns
    SSSw   -. "not wired" .-> So_bldepth
    So_bldepth["So_bldepth REQ · fill value sent"]:::ns
    Si_floediam["Si_floediam · not supplied"]:::ns
```

## MOM6

MOM6 imports few fields directly — most atmosphere–ocean coupling goes through CMEPS bulk formulae
(wind stress, sensible/latent heat, net SW/LW) computed automatically from the DATM fields.

```{mermaid}
flowchart LR
    classDef yes    fill:#f0fdf4,stroke:#4ade80,color:#14532d
    classDef si     fill:#fffbeb,stroke:#fbbf24,color:#78350f
    classDef ns     fill:#fff1f2,stroke:#fca5a5,color:#7f1d1d
    classDef could  fill:#f5f3ff,stroke:#c4b5fd,color:#4c1d95
    classDef unused fill:#f8fafc,stroke:#e2e8f0,color:#94a3b8

    subgraph h2m ["cam.h2 · 6-hourly instantaneous"]
        PSLm["PSL · sea-level pressure"]:::yes
        cmeps_h2["UBOT, VBOT, TREFHT, ZBOT…\n→ CMEPS bulk formulae,\nnot direct MOM6 imports"]:::unused
    end

    subgraph h4m ["cam.h4 · 6-hourly means"]
        PRECTm["PRECT · total precip m/s"]:::si
        PRECCm["PRECC · conv. precip m/s"]:::si
        PRECSCm["PRECSC · conv. snow m/s"]:::si
        PRECSLm["PRECSL · ls snow m/s"]:::si
        cmeps_h4["FLDS, FSDS, SOLSD, SOLLD\n→ CMEPS bulk formulae"]:::unused
    end

    subgraph icem ["cice.h1 · daily"]
        aice_dm["aice_d · ice conc. %"]:::yes
        other_icem["hi_d, uvel_d… · not used"]:::unused
    end

    PRECTm  -- "conv+ls rain/snow split\nm/s → kg m⁻² s⁻¹" --> Faxa_precip["Faxa_rain, Faxa_snow"]:::si
    PRECCm  --> Faxa_precip
    PRECSCm --> Faxa_precip
    PRECSLm --> Faxa_precip
    PSLm    -- "direct" --> Sa_pslv["Sa_pslv · sea-level pressure"]:::yes
    aice_dm -- "÷100 via DICE" --> Si_ifrac_m["Si_ifrac · ice fraction"]:::yes
```

## CICE

```{mermaid}
flowchart LR
    classDef yes    fill:#f0fdf4,stroke:#4ade80,color:#14532d
    classDef si     fill:#fffbeb,stroke:#fbbf24,color:#78350f
    classDef ns     fill:#fff1f2,stroke:#fca5a5,color:#7f1d1d
    classDef could  fill:#f5f3ff,stroke:#c4b5fd,color:#4c1d95
    classDef unused fill:#f8fafc,stroke:#e2e8f0,color:#94a3b8

    subgraph h2c ["cam.h2 · 6-hourly instantaneous"]
        UBOTc["UBOT · ~60 m u-wind"]:::yes
        VBOTc["VBOT · ~60 m v-wind"]:::yes
        ZBOTc["ZBOT · level height"]:::yes
        PSc["PS · surface pressure"]:::si
        PSLc["PSL · sea-level P ⚠"]:::could
        TREFHTc["TREFHT · 2 m temperature"]:::si
        QREFHTc["QREFHT · 2 m humidity"]:::si
        U10c["U10 · real 10 m wind ⚠"]:::could
    end

    subgraph h4c ["cam.h4 · 6-hourly means"]
        FLDSc["FLDS · downward LW"]:::yes
        SOLSDc["SOLSD · diffuse vis SW"]:::yes
        SOLLDc["SOLLD · diffuse nIR SW"]:::yes
        FSDSc["FSDS · total SW"]:::si
        PRECTc["PRECT · total precip"]:::si
        PRECCc["PRECC · conv. precip"]:::si
        PRECSCc["PRECSC · conv. snow"]:::si
        PRECSLc["PRECSL · ls snow"]:::si
    end

    subgraph ocnc ["pop.h.nday1 · daily"]
        SSTc["SST · °C"]:::yes
        U1_1c["U1_1 · surf u cm/s"]:::yes
        V1_1c["V1_1 · surf v cm/s"]:::yes
        SSSc["SSS · salinity ⚠"]:::could
    end

    subgraph icec ["cice.h1 · daily"]
        aice_dc["aice_d · ice conc. %"]:::yes
        hi_dc["hi_d · ice thickness ⚠"]:::could
    end

    %% Required fields
    PSc     -- "stand-in · surface not lowest-level" --> Sa_pbot["Sa_pbot REQ · lowest-level P"]:::si
    TREFHTc -- "compute ptem = T·(p₀/PS)^(Rd/cp)" --> Sa_ptem["Sa_ptem REQ · potential temp"]:::si
    PSc     --> Sa_ptem
    QREFHTc --> Sa_ptem
    TREFHTc -- "compute dens = p/(Rd·T·(1+0.608q))" --> Sa_dens["Sa_dens REQ · air density"]:::si
    PSc     --> Sa_dens
    QREFHTc --> Sa_dens

    %% Optional atmosphere fields
    ZBOTc   -- "direct" --> Sa_z["Sa_z · level height"]:::yes
    UBOTc   -- "direct" --> Sa_u["Sa_u · u-wind"]:::yes
    VBOTc   -- "direct" --> Sa_v["Sa_v · v-wind"]:::yes
    TREFHTc -- "stand-in · 2 m not lowest level" --> Sa_tbot_c["Sa_tbot · air temperature"]:::si
    QREFHTc -- "stand-in · 2 m not lowest level" --> Sa_shum["Sa_shum · specific humidity"]:::si
    FLDSc   -- "direct" --> Faxa_lwdn["Faxa_lwdn · downward LW"]:::yes
    SOLSDc  -- "direct" --> Faxa_swvdf["Faxa_swvdf · diffuse vis SW"]:::yes
    SOLLDc  -- "direct" --> Faxa_swndf["Faxa_swndf · diffuse nIR SW"]:::yes
    FSDSc   -- "FSDS−SOLSD × 0.28/0.59" --> Faxa_swvdr["Faxa_swvdr · direct vis SW"]:::si
    SOLSDc  --> Faxa_swvdr
    FSDSc   -- "FSDS−SOLLD × 0.31/0.59" --> Faxa_swndr["Faxa_swndr · direct nIR SW"]:::si
    SOLLDc  --> Faxa_swndr
    PRECTc  -- "rain/snow split\nm/s → kg m⁻² s⁻¹" --> Faxa_rain["Faxa_rain · rain flux"]:::si
    PRECCc  --> Faxa_rain
    PRECSCc -- "snow split" --> Faxa_snow["Faxa_snow · snow flux"]:::si
    PRECSLc --> Faxa_snow

    %% Ocean/ice fields
    SSTc   -- "°C → K via DOCN" --> So_t_c["So_t · SST"]:::yes
    SSSc   -. "not wired → could supply So_s" .-> So_s["So_s · not supplied"]:::ns
    U1_1c  -- "×0.01 via DOCN" --> So_u_c["So_u · current u"]:::yes
    V1_1c  -- "×0.01 via DOCN" --> So_v_c["So_v · current v"]:::yes
    aice_dc -- "÷100 via DICE" --> Si_ifrac_c["Si_ifrac · ice fraction"]:::yes
    hi_dc  -. "could derive Si_thick" .-> So_dhdx["So_dhdx, So_dhdy · not supplied"]:::ns
    PSLc   -. "available but PS used instead" .-> Sa_pbot
```
