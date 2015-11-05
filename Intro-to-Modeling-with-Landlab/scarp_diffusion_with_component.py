#Import statements so that you will have access to the necessary functions
import numpy
from landlab import RasterModelGrid
from landlab.components.diffusion.diffusion import LinearDiffuser
from landlab.plot.imshow import imshow_node_grid
from pylab import show, figure


#Create a raster grid with 25 rows, 40 columns, and cell spacing of 10 m
mg = RasterModelGrid(25, 40, 10.0)

#Create a field of node data (an array) on the grid called elevation.
#Initially populate this array with zero values.
#The component wants the elevation field to be called 'topographic__elevation'
z = mg.add_zeros('node', 'topographic__elevation')

#Check the size of the array
len(z)

#Create a diagonal fault across the grid
fault_y = 50.0 + 0.25*mg.node_x
upthrown_nodes = numpy.where(mg.node_y>fault_y)
z[upthrown_nodes] += 10.0 + 0.01*mg.node_x[upthrown_nodes]

#Illustrate the grid
imshow_node_grid(mg, 'topographic__elevation', cmap='jet', grid_units=['m','m'])
show()

#Instantiate the diffusion component:
linear_diffuse = LinearDiffuser(grid=mg, input_stream='./diffusion_input_file.txt')

#Set boundary conditions
mg.set_closed_boundaries_at_grid_edges(False, True, False, True)

#set a model timestep
#(the component will subdivide this as needed to keep things stable)
dt = 2000.

#Evolve landscape
for i in range(25):
    linear_diffuse.diffuse(dt)

#Plot new landscape
figure()
imshow_node_grid(mg, 'topographic__elevation', cmap='jet', grid_units=['m','m'])
show()
