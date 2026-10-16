# Adding stream data to CESM

## Required changes

1. CDEPS cime_config/config_component
    a. add %mesaclip
    b. datm_mode add mesaclip to vald_values
    c. add datm years st end align 
    d. new path variabbles like cplhist

2. CDEPS cime_config/namelist_definition_{comp}
    a. datamode (CPLHIST for mesaclip)
    b. streamslist 


3. CDEPS cime_config/stream_definiton_{comp}
    a. streamentry goes here

4. ccs_config 
    a. add mesaclip mesh 


## Possible Code changes

We might need a need a new datamode for mesaclip which might need to be added in CDEPS.

It's so depressing we need to write Fortran just to do unit conversion😭