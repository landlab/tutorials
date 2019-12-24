# -*- coding: utf-8 -*-
"""

"""

# Authors: Sai Nudurupati & Erkan Istanbulluoglu, 21May15
# Edited: 15Jul16 - to conform to Landlab version 1.
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from landlab.plot import imshow_grid
from landlab import RasterModelGrid as rmg
from landlab.components import (PrecipitationDistribution, Radiation,
                                PotentialEvapotranspiration)
from soil_moisture_dynamics_lb_pap import SoilMoisture
from vegetation_dynamics_lb_pap import Vegetation
from plant_competition_ca_lb_pap import VegCA
from landlab import load_params

GRASS = 0
SHRUB = 1
TREE = 2
BARE = 3
SHRUBSEEDLING = 4
TREESEEDLING = 5


# Function to compose spatially distribute PFT
def compose_veg_grid(grid, percent_bare=0.4, percent_grass=0.2,
                     percent_shrub=0.2, percent_tree=0.2):
    number_cells = grid.number_of_cells
    V = 3 * np.ones(grid.number_of_cells, dtype=int)
    shrub_point = int(percent_bare * number_cells)
    tree_point = int((percent_bare + percent_shrub) * number_cells)
    grass_point = int((1 - percent_grass) * number_cells)
    V[shrub_point:tree_point] = 1
    V[tree_point:grass_point] = 2
    V[grass_point:] = 0
    np.random.shuffle(V)
    return V


def initialize_components(data, grid_veg=None, grid=None, pet_method='Cosine'):
    # Plant types are defined as following:
    # GRASS = 0; SHRUB = 1; TREE = 2; BARE = 3;
    # SHRUBSEEDLING = 4; TREESEEDLING = 5
    # Initialize random plant type field
    grid.at_cell['vegetation__plant_functional_type'] = compose_veg_grid(
                grid, percent_bare=data['percent_bare_initial'],
                percent_grass=data['percent_grass_initial'],
                percent_shrub=data['percent_shrub_initial'],
                percent_tree=data['percent_tree_initial'])
    # Assign plant type for representative ecohydrologic simulations
    grid_veg.at_cell['vegetation__plant_functional_type'] = np.arange(0, 6)
    grid.at_node['topographic__elevation'] = np.full(grid.number_of_nodes,
                                                      1700.)
    grid_veg.at_node['topographic__elevation'] = np.full(
                        grid_veg.number_of_nodes, 1700.)
    precip_dry = PrecipitationDistribution(
                        mean_storm_duration=data['mean_storm_dry'],
                        mean_interstorm_duration=data['mean_interstorm_dry'],
                        mean_storm_depth=data['mean_storm_depth_dry'],
                        random_seed=None)
    precip_wet = PrecipitationDistribution(
                        mean_storm_duration=data['mean_storm_wet'],
                        mean_interstorm_duration=data['mean_interstorm_wet'],
                        mean_storm_depth=data['mean_storm_depth_wet'],
                        random_seed=None)
    radiation = Radiation(grid_veg)
    if pet_method=='Cosine':
        pet_tree = PotentialEvapotranspiration(
                        grid_veg, method=data['PET_method'],
                        MeanTmaxF=data['MeanTmaxF_tree'],
                        delta_d=data['DeltaD'])
        pet_shrub = PotentialEvapotranspiration(
                        grid_veg, method=data['PET_method'],
                        MeanTmaxF=data['MeanTmaxF_shrub'],
                        delta_d=data['DeltaD'])
        pet_grass = PotentialEvapotranspiration(
                        grid_veg, method=data['PET_method'],
                        MeanTmaxF=data['MeanTmaxF_grass'],
                        delta_d=data['DeltaD'])
    elif pet_method=='PriestleyTaylor':
        pet_met = PotentialEvapotranspiration(grid_veg,
                                              method='PriestleyTaylor')
        
    soil_moisture = SoilMoisture(grid_veg, **data)   # Soil Moisture object
    vegetation = Vegetation(grid_veg, **data)    # Vegetation object
    vegca = VegCA(grid, **data)      # Cellular automaton object

    # # Initializing inputs for Soil Moisture object
    grid_veg.at_cell['vegetation__live_leaf_area_index'] = (
                                    1.6 * np.ones(grid_veg.number_of_cells))
    grid_veg.at_cell['soil_moisture__initial_saturation_fraction'] = (
                                    0.59 * np.ones(grid_veg.number_of_cells))
    # Initializing Soil Moisture
    if pet_method=='Cosine':
        return (precip_dry, precip_wet, radiation, pet_tree, pet_shrub,
                pet_grass, soil_moisture, vegetation, vegca)
    elif pet_method=='PriestleyTaylor':
        return (precip_dry, precip_wet, radiation, pet_met, soil_moisture,
                vegetation, vegca)


def create_empty_arrays(number_of_storms, grid_veg, grid, pet_method='Cosine'):
    P = np.empty(number_of_storms)    # Record precipitation
    Tb = np.empty(number_of_storms)    # Record inter storm duration
    Tr = np.empty(number_of_storms)    # Record storm duration
    Time = np.empty(number_of_storms)  # To record time elapsed from the start of simulation
#    CumWaterStress = np.empty([n/55, grid.number_of_cells])
    # Cum Water Stress
    VegType = np.empty([int(number_of_storms/55), grid.number_of_cells], dtype=int)
    if pet_method=='Cosine':
        pet_arr = np.zeros([365, grid_veg.number_of_cells])
    elif pet_method=='PriestleyTaylor':
        pet_arr = np.zeros([number_of_storms, grid_veg.number_of_cells])
    Rad_Factor = np.empty([365, grid_veg.number_of_cells])
    EP30 = np.empty([365, grid_veg.number_of_cells])
    Rad_Factor_met = np.empty([number_of_storms, grid_veg.number_of_cells])
    EP30_met = np.empty([number_of_storms, grid_veg.number_of_cells])
    # 30 day average PET to determine season
    pet_threshold = 0  # Initializing PET_threshold to ETThresholddown
    return (P, Tb, Tr, Time, VegType, pet_arr, Rad_Factor,
            Rad_Factor_met, EP30, EP30_met, pet_threshold)


def create_pet_lookup(grid_veg, radiation=None, Rad_Factor=None,
                      EP30=None, pet_tree=None, pet_shrub=None,
                      pet_grass=None, pet_arr=None,
                      Rad_Factor_met=None, number_of_storms=None,
                      pet_met=None, Tmax_met=None, Tmin_met=None,
                      EP30_met=None, first_day=0, pet_method='Cosine'):
    if pet_method=='Cosine':
        for i in range(0, 365):
            pet_tree.update(float(i)/365.25)
            pet_shrub.update(float(i)/365.25)
            pet_grass.update(float(i)/365.25)
            pet_arr[i] = [pet_grass._PET_value, pet_shrub._PET_value,
                       pet_tree._PET_value, 0., pet_shrub._PET_value,
                       pet_tree._PET_value]
            radiation.update(float(i)/365.25)
            Rad_Factor[i] = (
                    grid_veg.at_cell['radiation__ratio_to_flat_surface'])
            if i < 30:
                if i == 0:
                    EP30[0] = pet_arr[0]
                else:
                    EP30[i] = np.mean(pet_arr[:i], axis=0)
            else:
                EP30[i] = np.mean(pet_arr[i-30:i], axis=0)
        return (pet_arr, EP30)

    elif pet_method=='PriestleyTaylor':
        for i in range(0, number_of_storms):
            pet_met.update(float(first_day+i)/365.25, Tmax = Tmax_met[i],
                               Tmin = Tmin_met[i],
                               Tavg = (Tmax_met[i]+Tmin_met[i])/2.)
            pet_arr[i] = [pet_met._PET_value, pet_met._PET_value,
                          pet_met._PET_value, 0., pet_met._PET_value,
                          pet_met._PET_value]
            radiation.update(float(i)/365.25)
            Rad_Factor_met[i] = (
                    grid_veg.at_cell['radiation__ratio_to_flat_surface'])
            if i < 30:
                if i == 0:
                    EP30_met[0] = pet_arr[0]
                else:
                    EP30_met[i] = np.mean(pet_arr[:i], axis=0)
            else:
                EP30_met[i] = np.mean(pet_arr[i-30:i], axis=0)
        return(pet_arr, EP30_met)


def save_data(sim, Tb, Tr, P, VegType, yrs, Time_Consumed, Time):
    np.save(sim+'Tb', Tb)
    np.save(sim+'Tr', Tr)
    np.save(sim+'P', P)
    np.save(sim+'VegType', VegType)
#    np.save(sim+'CumWaterStress', CumWaterStress)
    np.save(sim+'Years', yrs)
    np.save(sim+'Time_Consumed_minutes', Time_Consumed)
    np.save(sim+'CurrentTime', Time)


def plot_results(grid, VegType, yrs, yr_step=10):
    # # Plotting
    pic = 0
    years = range(0, yrs)
    cmap = mpl.colors.ListedColormap(
                        ['green', 'red', 'black', 'white', 'red', 'black'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    print('Plotting cellular field of Plant Functional Type')
    print('Green - Grass; Red - Shrubs; Black - Trees; White - Bare')
    # # Plot images to make gif.
    for year in range(0, yrs, yr_step):
        filename = 'Year = ' + "%05d" % year
        pic += 1
        plt.figure(pic)
        imshow_grid(grid, VegType[year], values_at='cell', cmap=cmap,
                    grid_units=('m', 'm'), norm=norm, limits=[0, 5],
                    allow_colorbar=False)
        plt.title(filename)
        plt.savefig(filename)
    grass_cov = np.empty(yrs)
    shrub_cov = np.empty(yrs)
    tree_cov = np.empty(yrs)
    grid_size = float(VegType.shape[1])
    for x in range(0, yrs):
        grass_cov[x] = (VegType[x][VegType[x] == GRASS].size/grid_size) * 100
        shrub_cov[x] = ((VegType[x][VegType[x] == SHRUB].size/grid_size) *
                        100 + (VegType[x][VegType[x] == SHRUBSEEDLING].size /
                        grid_size) * 100)
        tree_cov[x] = ((VegType[x][VegType[x] == TREE].size/grid_size) *
                       100 + (VegType[x][VegType[x] == TREESEEDLING].size /
                       grid_size) * 100)
    pic += 1
    plt.figure(pic)
    plt.plot(years, grass_cov, '-g', label='Grass')
    plt.hold(True)
    plt.plot(years, shrub_cov, '-r', label='Shrub')
    plt.hold(True)
    plt.plot(years, tree_cov, '-k', label='Tree')
    plt.xlim(xmin=0, xmax=years[-1])
    plt.ylim(ymin=0, ymax=(max(np.max(grass_cov),
                               np.max(shrub_cov),
                               np.max(tree_cov))+10))
    plt.ylabel(' % Coverage ')
    plt.xlabel('Time in years')
    plt.legend(loc=0)
    plt.savefig('PercentageCover_PFTs')
    # plt.show()

def run_ecohydrology_model(grid, input_data, input_file,
                           synthetic_storms=True, number_of_storms=None,
                           number_of_years=None,
                           first_julian_day_of_observations=0,
                           pet_method='Cosine',
                           save_files=False, sim_name='Trial'):
    # Create data object by reading in the input_file
    data = load_params(input_file)
    # Create a grid that can hold enough cells to represent all individual
    # vegetation types 
    grid_veg = rmg((5, 4), spacing=(5., 5.))
    if pet_method == 'Cosine':
        (precip_dry, precip_wet, radiation, pet_tree, pet_shrub, pet_grass,
         soil_moisture, vegetation, vegca) = initialize_components(data,
                                         grid_veg, grid, pet_method='Cosine')
    elif pet_method == 'PriestleyTaylor':
        (precip_dry, precip_wet, radiation, pet_met,
         soil_moisture, vegetation, vegca) = initialize_components(data,
                                grid_veg, grid, pet_method='PriestleyTaylor')        

    if number_of_years!=None:
        # Calculate approximate number of storms per year
        fraction_wet = ((data['doy__end_of_monsoon']-
                         data['doy__start_of_monsoon'])/365.)
        fraction_dry = (1 - fraction_wet)
        number_of_storms_wet = (8760 * (fraction_wet)/
                                (data['mean_interstorm_wet'] +
                                 data['mean_storm_wet']))
        number_of_storms_dry = (8760 * (fraction_dry)/
                                (data['mean_interstorm_dry'] +
                                 data['mean_storm_dry']))
        number_of_storms = int(number_of_years *
                               (number_of_storms_wet + number_of_storms_dry))

    (precip, inter_storm_dt, storm_dt, Time, VegType, pet_arr, Rad_Factor,
     Rad_Factor_met, EP30, EP30_met, pet_threshold) = create_empty_arrays(
                                                     number_of_storms,
                                                     grid_veg, grid,
                                                     pet_method=pet_method)
    
    if pet_method == 'Cosine':
        (pet_arr, EP30) = create_pet_lookup(grid_veg, radiation=radiation, Rad_Factor=Rad_Factor,
                              EP30=EP30, pet_tree=pet_tree, pet_shrub=pet_shrub,
                              pet_grass=pet_grass, pet_arr=pet_arr)
    if pet_method == 'PriestleyTaylor':
        (pet_arr, EP30_met) = create_pet_lookup(grid_veg, radiation=radiation,
                              Rad_Factor_met=Rad_Factor_met,
                              number_of_storms=number_of_storms,
                              pet_met=pet_met, Tmax_met=input_data['Tmax_met'],
                              Tmin_met=input_data['Tmin_met'], EP30_met=EP30_met,
                              first_day=first_julian_day_of_observations,
                              pet_method=pet_method, pet_arr=pet_arr)

    # declaring few variables that will be used in the storm loop
    current_time = first_julian_day_of_observations/365.25  # Initial time
    time_check = 0.     # Buffer to store current_time at previous storm
    yrs = 0             # Keep track of number of years passed
    water_stress = 0.             # Buffer for Water Stress
    Tg = 0            # Growing season in days
    
    # # Run storm Loop
    for i in range(0, number_of_storms):
        # Update objects
    
        # Calculate Day of Year (DOY)
        julian = np.int(np.floor((current_time - np.floor(current_time)) *
                                 365.))
        if synthetic_storms:
            # Generate seasonal storms
            # for Dry season
            if julian < data['doy__start_of_monsoon'] or julian > data[
                                'doy__end_of_monsoon']:
                precip_dry.update()
                precip[i] = precip_dry.storm_depth
                storm_dt[i] = precip_dry.storm_duration
                inter_storm_dt[i] = precip_dry.interstorm_duration
            # Wet Season - Jul to Sep - NA Monsoon
            else:
                precip_wet.update()
                precip[i] = precip_wet.storm_depth
                storm_dt[i] = precip_wet.storm_duration
                inter_storm_dt[i] = precip_wet.interstorm_duration
        else:
            precip[i] = input_data['precip_met'][i]
            storm_dt[i] = 0.
            inter_storm_dt[i] = 24.
    
        # Spatially distribute PET and its 30-day-mean (analogous to degree day)
        if pet_method == 'Cosine':
            grid_veg.at_cell['surface__potential_evapotranspiration_rate'] = (
                    pet_arr[julian])
            grid_veg.at_cell['surface__potential_evapotranspiration_30day_mean'] = (
                    EP30[julian])
            grid_veg.at_cell['surface__potential_evapotranspiration_rate__grass'] = (
                    np.full(grid_veg.number_of_cells, pet_arr[julian, 0]))
        elif pet_method=='PriestleyTaylor':
            grid_veg.at_cell['surface__potential_evapotranspiration_rate'] = (
                    pet_arr[i])
            grid_veg.at_cell['surface__potential_evapotranspiration_30day_mean'] = (
                    EP30_met[i])
            grid_veg.at_cell['surface__potential_evapotranspiration_rate__grass'] = (
                    np.full(grid_veg.number_of_cells, pet_arr[i, 0]))
    
        # Assign spatial rainfall data
        grid_veg.at_cell['rainfall__daily_depth'] = (
                np.full(grid_veg.number_of_cells, precip[i]))
    
        # Update soil moisture component
        current_time = soil_moisture.update(current_time, Tr=storm_dt[i],
                                            Tb=inter_storm_dt[i])
    
        # Decide whether its growing season or not
        if pet_method == 'Cosine':
            if julian != 364:
                if EP30[julian+1, 0] > EP30[julian, 0]:
                    pet_threshold = 1
                    # 1 corresponds to ETThresholdup (begin growing season)
                    if EP30[julian, 0] > vegetation._ETthresholdup:
                        growing_season = True
                    else:
                        growing_season = False
                else:
                    pet_threshold = 0
                    # 0 corresponds to ETThresholddown (end growing season)
                    if EP30[julian, 0] > vegetation._ETthresholddown:
                        growing_season = True
                    else:
                        growing_season = False
        elif pet_method=='PriestleyTaylor':
            if i != number_of_storms-1:
                if EP30_met[i+1, 0] > EP30_met[i, 0]:
                    pet_threshold = 1
                    # 1 corresponds to ETThresholdup (begin growing season)
                    if EP30_met[i, 0] > vegetation._ETthresholdup:
                        growing_season = True
                    else:
                        growing_season = False
                else:
                    pet_threshold = 0
                    # 0 corresponds to ETThresholddown (end growing season)
                    if EP30_met[i, 0] > vegetation._ETthresholddown:
                        growing_season = True
                    else:
                        growing_season = False                            

        # Update vegetation component
        vegetation.update(PETThreshold_switch=pet_threshold,
                          Tb=inter_storm_dt[i], Tr=storm_dt[i])

        if growing_season:
            # Update yearly cumulative water stress data
            Tg += (storm_dt[i]+inter_storm_dt[i])/24.    # Incrementing growing season storm count
            water_stress += ((grid_veg.at_cell['vegetation__water_stress']) *
                             inter_storm_dt[i]/24.)

        # Record time (optional)
        Time[i] = current_time
    
        # Update spatial PFTs with Cellular Automata rules
        if (current_time - time_check) >= 1.:
            if yrs % 100 == 0:
                print('Elapsed time = ', yrs, ' years')
            VegType[yrs] = grid.at_cell['vegetation__plant_functional_type']
            WS_ = np.choose(VegType[yrs], water_stress)
            grid.at_cell['vegetation__cumulative_water_stress'] = WS_/Tg
            vegca.update()
            time_check = np.floor(current_time)
            water_stress = 0
            yrs += 1
            Tg = 0
    
    VegType[yrs] = grid.at_cell['vegetation__plant_functional_type']
    if save_files:
        save_data(sim_name, inter_storm_dt, storm_dt, precip,
                  VegType, yrs, 0, Time)
    if pet_method == 'Cosine':
        returns_debug = [grid_veg, precip_dry, precip_wet,
                         radiation, pet_tree, pet_shrub,
                         pet_grass, soil_moisture, vegetation,
                         vegca]

    elif pet_method == 'PriestleyTaylor':
        returns_debug = [grid_veg, precip_dry, precip_wet,
                         radiation, pet_met, soil_moisture,
                         vegetation, vegca]
    return (VegType, yrs-1, returns_debug)
        
