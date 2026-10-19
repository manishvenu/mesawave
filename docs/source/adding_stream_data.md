# Adding stream data to CESM

## Required changes

1. CDEPS cime_config/config_component
    1. add %mesaclip
    2. datm_mode add mesaclip to vald_values
    3. add datm years st end align 
    4. new path variabbles like cplhist

2. CDEPS cime_config/namelist_definition_{comp}
    1. datamode (CPLHIST for mesaclip)
    2. streamslist 


3. CDEPS cime_config/stream_definiton_{comp}
    1. streamentry goes here

4. ccs_config 
    1. add mesaclip mesh 


## Possible code changes

We might need a need a new datamode for mesaclip which might need to be added in CDEPS.

It's so depressing we need to write Fortran just to do unit conversion😭