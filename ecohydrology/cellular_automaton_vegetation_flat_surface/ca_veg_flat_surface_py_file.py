# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 2016

This tutorial is on:
landlab/tutorials/ecohydrology/cellular_automaton_vegetation_flat_surface.ipynb

Creating a (.py) version of the same.

@author: Sai Nudurupati & Erkan Istanbulluoglu
"""

import time
import numpy as np
from landlab import RasterModelGrid as rmg
from Ecohyd_functions_flat import (txt_data_dict, Initialize_, Empty_arrays,
                                   Create_PET_lookup, Save_, Plot_)

grid1 = rmg((100, 100), spacing=(5., 5.))
grid = rmg((5, 4), spacing=(5., 5.))

InputFile = 'Inputs_Vegetation_CA.txt'
data = txt_data_dict(InputFile)  # Create dictionary that holds the inputs

PD_D, PD_W, Rad, PET_Tree, PET_Shrub, PET_Grass, SM, VEG, vegca = Initialize_(
            data, grid, grid1)

n_years = 1200      # Approx number of years for model to run
# Calculate approximate number of storms per year
fraction_wet = (data['doy__end_of_monsoon']-data['doy__start_of_monsoon'])/365.
fraction_dry = 1 - fraction_wet
no_of_storms_wet = (8760 * (fraction_wet)/(data['mean_interstorm_wet'] +
                    data['mean_storm_wet']))
no_of_storms_dry = (8760 * (fraction_dry)/(data['mean_interstorm_dry'] +
                    data['mean_storm_dry']))
n = int(n_years * (no_of_storms_wet + no_of_storms_dry))

P, Tb, Tr, Time, VegType, PET_, Rad_Factor, EP30, PET_threshold = Empty_arrays(
                n, grid, grid1)

Create_PET_lookup(Rad, PET_Tree, PET_Shrub, PET_Grass,  PET_, Rad_Factor,
                  EP30, grid)

# # Represent current time in years
current_time = 0            # Start from first day of Jan

# Keep track of run time for simulation - optional
Start_time = time.clock()     # Recording time taken for simulation

# declaring few variables that will be used in the storm loop
time_check = 0.     # Buffer to store current_time at previous storm
yrs = 0             # Keep track of number of years passed
WS = 0.             # Buffer for Water Stress
Tg = 270        # Growing season in days

# # Run storm Loop
for i in range(0, n):
    # Update objects

    # Calculate Day of Year (DOY)
    Julian = np.int(np.floor((current_time - np.floor(current_time)) * 365.))

    # Generate seasonal storms
    # for Dry season
    if Julian < data['doy__start_of_monsoon'] or Julian > data[
                        'doy__end_of_monsoon']:
        PD_D.update()
        P[i] = PD_D.storm_depth
        Tr[i] = PD_D.storm_duration
        Tb[i] = PD_D.interstorm_duration
    # Wet Season - Jul to Sep - NA Monsoon
    else:
        PD_W.update()
        P[i] = PD_W.storm_depth
        Tr[i] = PD_W.storm_duration
        Tb[i] = PD_W.interstorm_duration

    # Spatially distribute PET and its 30-day-mean (analogous to degree day)
    grid['cell']['surface__potential_evapotranspiration_rate'] = PET_[Julian]
    grid['cell']['surface__potential_evapotranspiration_30day_mean'] = EP30[
                Julian]

    # Assign spatial rainfall data
    grid['cell']['rainfall__daily_depth'] = P[i] * np.ones(grid.number_of_cells)

    # Update soil moisture component
    current_time = SM.update(current_time, Tr=Tr[i], Tb=Tb[i])

    # Decide whether its growing season or not
    if Julian != 364:
        if EP30[Julian+1, 0] > EP30[Julian, 0]:
            PET_threshold = 1
            # 1 corresponds to ETThresholdup (begin growing season)
        else:
            PET_threshold = 0
            # 0 corresponds to ETThresholddown (end growing season)

    # Update vegetation component
    VEG.update(PETThreshold_switch=PET_threshold, Tb=Tb[i], Tr=Tr[i])

    # Update yearly cumulative water stress data
    WS += (grid['cell']['vegetation__water_stress'])*Tb[i]/24.

    # Record time (optional)
    Time[i] = current_time

    # Update spatial PFTs with Cellular Automata rules
    if (current_time - time_check) >= 1.:
        if yrs % 100 == 0:
            print 'Elapsed time = ', yrs, ' years'
        VegType[yrs] = grid1['cell']['vegetation__plant_functional_type']
        WS_ = np.choose(VegType[yrs], WS)
        grid1['cell']['vegetation__cumulative_water_stress'] = WS_/Tg
        vegca.update()
        time_check = current_time
        WS = 0
        yrs += 1

VegType[yrs] = grid1['cell']['vegetation__plant_functional_type']

Final_time = time.clock()
Time_Consumed = (Final_time - Start_time)/60.    # in minutes
print 'Time_consumed = ', Time_Consumed, ' minutes'

# # Saving
# sim = 'Sim_26Jul16_'
# Save_(sim, Tb, Tr, P, VegType, yrs, Time_Consumed, Time)

Plot_(grid1, VegType, yrs, yr_step=100)
