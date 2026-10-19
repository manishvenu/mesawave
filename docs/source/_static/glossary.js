// Hover definitions for variable names in inline code.
// Coupler fields: CMEPS fd_cesm.yaml (descriptions and units). MESACLIP fields:
// long_name and units in the GDEX files (TBOT, QBOT, SOLS, SOLL from CAM's addfld).
const GLOSSARY = {
  // CMEPS name prefixes: S = state, F = flux; a atm, o ocn, i ice, w wav, r rof, x CMEPS.
  'Sa_': 'Atmosphere state',
  'So_': 'Ocean state',
  'Si_': 'Sea-ice state',
  'Sw_': 'Wave state',
  'Sf_': 'Fraction computed by CMEPS',
  'Faxa_': 'Atmosphere flux, computed by the atmosphere',
  'Foxx_': 'Flux into the ocean, computed or merged by CMEPS',
  'Fioi_': 'Ice-to-ocean flux, computed by the ice',
  'Fioo_': 'Ice-ocean flux, computed by the ocean',
  'Forr_': 'River-to-ocean flux, computed by the river model',

  // Atmosphere
  'Sa_u': 'Lowest-level zonal (eastward) wind, m/s',
  'Sa_v': 'Lowest-level meridional (northward) wind, m/s',
  'Sa_z': 'Height of the lowest atmosphere level, m',
  'Sa_u10m': '10 m zonal (eastward) wind, m/s',
  'Sa_v10m': '10 m meridional (northward) wind, m/s',
  'Sa_tbot': 'Lowest-level air temperature, K',
  'atmImp_Sa_tbot': 'Sa_tbot as saved in coupler history: lowest-level air temperature, K',
  'Sa_ptem': 'Lowest-level potential temperature, K',
  'Sa_shum': 'Lowest-level specific humidity, kg/kg',
  'Sa_dens': 'Lowest-level air density, kg/m³',
  'Sa_pbot': 'Lowest-level pressure, Pa',
  'Sa_pslv': 'Sea-level pressure, Pa',
  'Sa_topo': 'Surface (topographic) height, m',
  'Sa_co2prog': 'Prognostic CO₂ at the lowest level, 1e-6 mol/mol',
  'Sa_co2diag': 'Diagnostic CO₂ at the lowest level, 1e-6 mol/mol',
  'Faxa_lwdn': 'Downward longwave at the surface, W/m²',
  'Faxa_swvdr': 'Downward shortwave, visible direct, W/m²',
  'Faxa_swvdf': 'Downward shortwave, visible diffuse, W/m²',
  'Faxa_swndr': 'Downward shortwave, near-infrared direct, W/m²',
  'Faxa_swndf': 'Downward shortwave, near-infrared diffuse, W/m²',
  'Faxa_rain': 'Rain, convective + large-scale, kg/m²/s',
  'Faxa_snow': 'Snow, convective + large-scale, kg/m²/s',
  'Faxa_rainc': 'Convective rain, kg/m²/s',
  'Faxa_rainl': 'Large-scale rain, kg/m²/s',
  'Faxa_snowc': 'Convective snow, kg/m²/s',
  'Faxa_snowl': 'Large-scale snow, kg/m²/s',
  'Faxa_bcph': 'Black carbon deposition (3 types), kg/m²/s',
  'Faxa_dstwet': 'Wet dust deposition (4 sizes), kg/m²/s',
  'Faxa_dstdry': 'Dry dust deposition (4 sizes), kg/m²/s',
  'Faxa_ndep': 'Nitrogen deposition (NHx, NOy), kg(N)/m²/s',

  // Ocean
  'So_t': 'Sea surface temperature, K',
  'So_s': 'Sea surface salinity, g/kg',
  'So_u': 'Surface current, eastward, m/s',
  'So_v': 'Surface current, northward, m/s',
  'So_dhdx': 'Sea-surface slope, x direction, m/m',
  'So_dhdy': 'Sea-surface slope, y direction, m/m',
  'So_bldepth': 'Ocean boundary-layer depth, m',
  'So_duu10n': '10 m neutral wind speed squared, m²/s²',
  'So_omask': 'Ocean mask, 0–1',
  'Fioo_q': 'Ocean freeze (> 0) or melt (< 0) potential, W/m²',

  // Sea ice
  'Si_ifrac': 'Ice fraction, 0–1',
  'Si_ifrac_n': 'Ice fraction per thickness category, 0–1',
  'Si_thick': 'Ice thickness, m',
  'Si_floediam': 'Ice floe diameter, m',
  'Fioi_melth': 'Heat flux from ice to ocean (melt heat), W/m²',
  'Fioi_meltw': 'Fresh water from melting ice to ocean, kg/m²/s',
  'Fioi_salt': 'Salt from melting ice to ocean, kg/m²/s',
  'Fioi_swpen': 'Shortwave through ice to ocean, W/m²',
  'Fioi_swpen_ifrac_n': 'Shortwave through ice times ice fraction, per thickness category, W/m²',
  'Fioi_taux': 'Ice–ocean stress, zonal, N/m²',
  'Fioi_tauy': 'Ice–ocean stress, meridional, N/m²',
  'Fioi_bcphi': 'Hydrophilic black carbon from ice to ocean, kg/m²/s',
  'Fioi_bcpho': 'Hydrophobic black carbon from ice to ocean, kg/m²/s',
  'Fioi_flxdst': 'Dust from ice to ocean, kg/m²/s',

  // Into the ocean, from CMEPS
  'Foxx_taux': 'Surface stress on the ocean, zonal, N/m²',
  'Foxx_tauy': 'Surface stress on the ocean, meridional, N/m²',
  'Foxx_sen': 'Sensible heat flux into the ocean, W/m²',
  'Foxx_evap': 'Evaporation, kg/m²/s',
  'Foxx_lwnet': 'Net longwave into the ocean, W/m²',
  'Foxx_swnet_vdr': 'Net shortwave into the ocean, visible direct, W/m²',
  'Foxx_swnet_vdf': 'Net shortwave into the ocean, visible diffuse, W/m²',
  'Foxx_swnet_idr': 'Net shortwave into the ocean, near-infrared direct, W/m²',
  'Foxx_swnet_idf': 'Net shortwave into the ocean, near-infrared diffuse, W/m²',
  'Foxx_swnet_afracr': 'Net shortwave times the fraction open to the atmosphere, W/m²',
  'Foxx_rofl': 'Liquid runoff, kg/m²/s',
  'Foxx_rofi': 'Frozen runoff, kg/m²/s',
  'Foxx_hrain': 'Heat content of rain, W/m²',
  'Foxx_hsnow': 'Heat content of snow, W/m²',
  'Foxx_hevap': 'Heat content of evaporation, W/m²',
  'Foxx_hcond': 'Heat content of condensation, W/m²',
  'Foxx_hrofl': 'Heat content of liquid runoff, W/m²',
  'Foxx_hrofi': 'Heat content of frozen runoff, W/m²',
  'Foxx_hrofl_glc': 'Heat content of liquid glacier runoff, W/m²',
  'Foxx_hrofi_glc': 'Heat content of frozen glacier runoff, W/m²',
  'Forr_rofl_glc': 'Liquid runoff from glaciers, kg/m²/s',
  'Forr_rofi_glc': 'Frozen runoff from glaciers, kg/m²/s',
  'Sf_afracr': 'Fraction of the ocean cell open to the atmosphere, for radiation, 0–1',

  // Waves
  'Sw_lamult': 'Langmuir enhancement factor',
  'Sw_pstokes_x': 'Stokes drift in bands, eastward, m/s',
  'Sw_pstokes_y': 'Stokes drift in bands, northward, m/s',
  'Sw_ustokes': 'Surface Stokes drift, eastward, m/s',
  'Sw_vstokes': 'Surface Stokes drift, northward, m/s',
  'Sw_hstokes': 'Stokes drift depth, m',
  'Sw_elevation_spectrum': 'Wave elevation spectrum (25 frequencies)',

  // MESACLIP CAM (6-hourly)
  'h2': 'MESACLIP CAM history stream: 6-hourly instantaneous',
  'h4': 'MESACLIP CAM history stream: 6-hourly means, stamped at the window end',
  'UBOT': 'Lowest model level zonal wind, m/s (CAM h2)',
  'VBOT': 'Lowest model level meridional wind, m/s (CAM h2)',
  'ZBOT': 'Lowest model level height, m (CAM h2)',
  'PSL': 'Sea level pressure, Pa (CAM h2)',
  'PS': 'Surface pressure, Pa (CAM h2)',
  'TREFHT': 'Reference height (2 m) temperature, K (CAM h2)',
  'QREFHT': 'Reference height (2 m) humidity, kg/kg (CAM h2)',
  'FSDS': 'Downwelling solar flux at surface, W/m² (CAM h4)',
  'FLDS': 'Downwelling longwave flux at surface, W/m² (CAM h4)',
  'SOLSD': 'Solar downward visible diffuse to surface, W/m² (CAM h4)',
  'SOLLD': 'Solar downward near infrared diffuse to surface, W/m² (CAM h4)',
  'PRECT': 'Total (convective and large-scale) precipitation rate (liq + ice), m/s (CAM h4)',
  'PRECC': 'Convective precipitation rate (liq + ice), m/s (CAM h4)',
  'PRECSC': 'Convective snow rate (water equivalent), m/s (CAM h4)',
  'PRECSL': 'Large-scale (stable) snow rate (water equivalent), m/s (CAM h4)',
  'TBOT': 'Lowest model level temperature, K (not saved 6-hourly)',
  'QBOT': 'Lowest model level water vapor mixing ratio, kg/kg (not saved 6-hourly)',
  'SOLS': 'Solar downward visible direct to surface, W/m² (not saved 6-hourly)',
  'SOLL': 'Solar downward near infrared direct to surface, W/m² (not saved 6-hourly)',

  // MESACLIP POP (daily)
  'SST': 'Surface potential temperature, °C (POP daily)',
  'SSS': 'Surface salinity, g/kg (POP daily)',
  'U1_1': 'Zonal velocity, top level, cm/s, along POP grid axes (POP daily)',
  'V1_1': 'Meridional velocity, top level, cm/s, along POP grid axes (POP daily)',
  'SSH_2': 'Sea surface height, cm (POP daily)',
  'QFLUX': 'Internal ocean heat flux due to ice formation: heat of fusion > 0 or ice-melting potential < 0, W/m² (POP daily)',
  'MELTH_F': 'Melt heat flux from coupler, W/m² (POP daily)',
  'MELT_F': 'Melt flux from coupler, kg/m²/s (POP daily)',
  'SALT_F': 'Salt flux from coupler, kg/m²/s (POP daily)',
  'HMXL': 'Mixed-layer depth, cm (POP daily)',
  'XBLT': 'Maximum boundary-layer depth, cm (POP daily)',

  // MESACLIP CICE (daily)
  'aice_d': 'Ice area (aggregate), % (CICE daily)',
  'hi_d': 'Grid cell mean ice thickness, m (CICE daily)',
  'fswthru_d': 'Shortwave through ice to ocean, W/m² (CICE daily)',

  // CESM components, grids and case settings (descriptions from CIME's config XML)
  'DATM': 'CDEPS data atmosphere',
  'DOCN': 'CDEPS data ocean',
  'DICE': 'CDEPS data sea ice',
  'CPLHIST': 'CDEPS mode that replays coupler history from an earlier run',
  'GDEX': "NCAR's Geoscience Data Exchange, where MESACLIP output is archived",
  'HIST': 'Historical scenario',
  'RCP26': 'Representative Concentration Pathway 2.6 scenario',
  'RCP45': 'Representative Concentration Pathway 4.5 scenario',
  'RCP60': 'Representative Concentration Pathway 6.0 scenario',
  'RCP85': 'Representative Concentration Pathway 8.5 scenario',
  'ne120_t12': 'CESM resolution: ne120 atmosphere (~0.25°) with t12 (0.1°) ocean',
  'ne120np4': 'CAM spectral-element grid, ~0.25°',
  'DATM_MESACLIP_CASE': 'MESACLIP case name on GDEX (picks the ensemble member) when DATM_MODE is MESACLIP_*',
  'DATM_MODE': 'Mode for the data atmosphere (which forcing it reads)',
  'DOCN_MODE': 'Mode for the data ocean',
  'DATM_TOPO': 'DATM surface topography forcing',
  'DATM_YR_': 'DATM_YR_START, DATM_YR_END, DATM_YR_ALIGN: forcing years to loop over, and the simulation year the first maps to',
  'DATM_YR_START': 'Starting year to loop forcing data over',
  'DATM_YR_ALIGN': 'Simulation year corresponding to DATM_YR_START',
  'DATM_CPLHIST_CASE': 'Case name used to find stream files when DATM_MODE is CPLHIST',
  'DATM_CPLHIST_DIR': 'Directory of coupler history data when DATM_MODE is CPLHIST',
  'DOCN_CPLHIST_DIR': 'Directory of coupler history data for DOCN CPLHIST mode',
  'DOCN_CPLHIST_YR_': 'DOCN_CPLHIST_YR_START, _END, _ALIGN: DOCN CPLHIST data years',
  'OCN_GRID': 'Ocean grid name',
  'OCN_DOMAIN_MESH': 'ESMF mesh file for the ocean domain',
  'ATM_DOMAIN_MESH': 'ESMF mesh file for the atmosphere domain',
  'WW3_GRID_INP_DIR': 'Directory with ww3_grid.inp and its associated files',
  'RUNDIR': "The case's run directory",
  'sst_constant_value': 'DOCN namelist: globally uniform SST (K) for the sst_aquap_constant mode',
};

document.addEventListener('DOMContentLoaded', () => {
  const word = /[A-Za-z][A-Za-z0-9_]*/g;
  document.querySelectorAll('code.literal').forEach((code) => {
    const walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const text = node.nodeValue;
      if (!text.match(word)?.some((w) => w in GLOSSARY)) return;
      const frag = document.createDocumentFragment();
      let last = 0;
      for (const m of text.matchAll(word)) {
        if (!(m[0] in GLOSSARY)) continue;
        frag.append(text.slice(last, m.index));
        const abbr = document.createElement('abbr');
        abbr.className = 'gloss';
        abbr.title = GLOSSARY[m[0]];
        abbr.tabIndex = 0;
        abbr.textContent = m[0];
        frag.append(abbr);
        last = m.index + m[0].length;
      }
      frag.append(text.slice(last));
      node.replaceWith(frag);
    });
  });
});
