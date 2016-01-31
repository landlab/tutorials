from landlab.components.diffusion import LinearDiffuser
from landlab import ModelParameterDictionary
from landlab.plot.imshow import imshow_node_grid
from landlab import RasterModelGrid
import numpy as np
import pylab

input_file = './component_tutorial_params.txt'
inputs = ModelParameterDictionary(input_file) # load the data into an MPD
nrows = inputs.read_int('nrows')
ncols = inputs.read_int('ncols')
dx = inputs.read_float('dx')
leftmost_elev = inputs.read_float('leftmost_elevation')
initial_slope = inputs.read_float('initial_slope') # this is zero
uplift_rate = inputs.read_float('uplift_rate')
runtime = inputs.read_float('total_time')
dt = inputs.read_float('dt')
nt = int(runtime // dt) # this is how many loops we'll need
uplift_per_step = uplift_rate * dt

mg = RasterModelGrid(nrows, ncols, dx) #the grid

z = mg.add_zeros('node', 'topographic__elevation')

z += leftmost_elev

z += (initial_slope * np.amax(mg.node_y)) - (initial_slope * mg.node_y)

z += np.random.rand(z.size) / 100000.

mg.set_closed_boundaries_at_grid_edges(False, True, False, True)

mg.set_fixed_value_boundaries_at_grid_edges(True, False, True, False)

lin_diffuse = LinearDiffuser(mg, input_file)

elapsed_time = 0.
keep_running = True
while keep_running:
    if elapsed_time + dt > runtime:
        dt = runtime - elapsed_time
        keep_running = False
    lin_diffuse.diffuse(dt) # do the diffusion
    mg.at_node['topographic__elevation'][mg.core_nodes] += uplift_per_step # add the uplift
    elapsed_time += dt


# Create a figure and plot the elevations
pylab.figure(1)
im = imshow_node_grid(mg, 'topographic__elevation', grid_units = ['m','m'])

pylab.figure(2)
elev_rast = mg.node_vector_to_raster(mg.at_node['topographic__elevation'])
ycoord_rast = mg.node_vector_to_raster(mg.node_y)
im = pylab.plot(ycoord_rast[:,int(ncols // 2)], elev_rast[:,int(ncols // 2)])
pylab.xlabel('horizontal distance (m)')
pylab.ylabel('vertical distance (m)')
pylab.title('topographic__elevation cross section')

# Now we're going to take a similar approach but this time combine the outputs of three distinct Landlab components: the diffuser, the monodirectional flow router, and the stream power incisor. For clarity, we're going to repeat the whole process from the start.
from landlab.components.flow_routing import FlowRouter
from landlab.components.stream_power import StreamPowerEroder
from landlab.components.diffusion import LinearDiffuser
from landlab import ModelParameterDictionary
from landlab.plot.imshow import imshow_node_grid
from landlab import RasterModelGrid
import numpy as np
import pylab

input_file = './coupled_params.txt'
inputs = ModelParameterDictionary(input_file) # load the data into an MPD
nrows = inputs.read_int('nrows')
ncols = inputs.read_int('ncols')
dx = inputs.read_float('dx')
leftmost_elev = inputs.read_float('leftmost_elevation')
initial_slope = inputs.read_float('initial_slope') # this is zero
uplift_rate = inputs.read_float('uplift_rate')
runtime = inputs.read_float('total_time')
dt = inputs.read_float('dt')
nt = int(runtime // dt) #this is how many loops we'll need
uplift_per_step = uplift_rate * dt

mg = RasterModelGrid(nrows, ncols, dx)
z = mg.add_zeros('node', 'topographic__elevation')
z += leftmost_elev
z += (initial_slope * np.amax(mg.node_y)) - (initial_slope * mg.node_y)
initial_roughness = np.random.rand(z.size)/100000.
z += initial_roughness
mg.set_closed_boundaries_at_grid_edges(False, True, False, True)
mg.set_fixed_value_boundaries_at_grid_edges(True, False, True, False)

fr = FlowRouter(mg) # note the flow router doesn't have to take an input file
sp = StreamPowerEroder(mg, input_file)
lin_diffuse = LinearDiffuser(mg, input_file)

# And now we run! We're going to run once with the diffusion and once without.
elapsed_time = 0.
keep_running = True
counter = 0 # simple incremented counter to let us see the model advance
while keep_running:
    if elapsed_time + dt > runtime:
        dt = runtime - elapsed_time
        keep_running = False
    # _ = lin_diffuse.diffuse(dt) no diffusion this time
    _ = fr.route_flow() # route_flow isn't time sensitive, so it doesn't take dt as input
    _ = sp.erode(mg, dt=dt)
    # this component is of an older style,
    # so it still needs a copy of the grid to be passed
    mg.at_node['topographic__elevation'][mg.core_nodes] += uplift_per_step # add the uplift
    elapsed_time += dt
    if counter % 50 == 0:
        print ('Completed loop %d' % counter)
    counter += 1

pylab.figure('topo without diffusion')
im = imshow_node_grid(mg, 'topographic__elevation', grid_units=['km','km'])

# And now let's reset the grid elevations and do everything again, but this time, with the diffusion turned *on*:
z = mg.add_zeros('node', 'topographic__elevation')
z += leftmost_elev
z += (initial_slope * np.amax(mg.node_y)) - (initial_slope * mg.node_y)
z += initial_roughness
elapsed_time = 0.
keep_running = True
dt = inputs.read_float('dt')
counter = 0
while keep_running:
    if elapsed_time + dt > runtime:
        dt = runtime - elapsed_time
        keep_running = False
    _ = lin_diffuse.diffuse(dt) # diffusion now on
    _ = fr.route_flow()
    _ = sp.erode(mg, dt=dt)
    mg.at_node['topographic__elevation'][mg.core_nodes] += uplift_per_step # add the uplift
    elapsed_time += dt
    if counter % 50 == 0:
        print ('Completed loop %d' % counter)
    counter += 1

pylab.figure('topo with diffusion')
im = imshow_node_grid(mg, 'topographic__elevation', grid_units=['km','km'])

# As a final step, we're going to repeat the above coupled model run, but this time we're going to plot some evolving channel profiles, and we're going to drive the simulation with a sequence of storms, not just a fixed timestep.
from landlab.plot import channel_profile as prf
from landlab.components.uniform_precip import PrecipitationDistribution

z = mg.add_zeros('node', 'topographic__elevation')
z += leftmost_elev
z += (initial_slope * np.amax(mg.node_y)) - (initial_slope * mg.node_y)
z += initial_roughness
dt = inputs.read_float('dt')

precip = PrecipitationDistribution(input_file='coupled_params_storms.txt')

out_interval = 20.
last_trunc = runtime # we use this to trigger taking an output plot
for (interval_duration, rainfall_rate) in precip.yield_storm_interstorm_duration_intensity():
    if rainfall_rate != 0.:
        # note diffusion also only happens when it's raining...
        _ = fr.route_flow()
        sp.gear_timestep(interval_duration, rainfall_intensity_in=rainfall_rate)
        _ = sp.erode(mg)
        _ = lin_diffuse.diffuse(interval_duration)
    mg.at_node['topographic__elevation'][mg.core_nodes] += uplift_rate * interval_duration
    this_trunc = precip.elapsed_time // out_interval
    if this_trunc != last_trunc: # time to plot a new profile!
        print ('made it to time %d' % (out_interval * this_trunc))
        last_trunc = this_trunc
        pylab.figure("long_profiles")
        profile_IDs = prf.channel_nodes(mg, mg.at_node['topographic__steepest_slope'],
                        mg.at_node['drainage_area'], mg.at_node['flow_receiver'])
        dists_upstr = prf.get_distances_upstream(mg, len(mg.at_node['topographic__steepest_slope']),
                        profile_IDs, mg.at_node['links_to_flow_receiver'])
        prf.plot_profiles(dists_upstr, profile_IDs, mg.at_node['topographic__elevation'])
    # no need to track elapsed time, as the generator will stop automatically
# make the figure look nicer:
pylab.figure("long_profiles")
pylab.xlabel('Distance upstream (km)')
pylab.ylabel ('Elevation (km)')
pylab.title('Long profiles evolving through time')

pylab.figure('topo with diffusion and storms')
im = imshow_node_grid(mg, 'topographic__elevation', grid_units=['km','km'])

pylab.figure('final slope-area plot')
im = pylab.loglog(mg.at_node['drainage_area'], mg.at_node['topographic__steepest_slope'],'.')
pylab.xlabel('Drainage area (km**2)')
pylab.ylabel('Local slope')
pylab.title('Slope-Area plot for whole landscape')
