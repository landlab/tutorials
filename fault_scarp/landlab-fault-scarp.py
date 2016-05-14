# Creating a simple 2D scarp diffusion model with Landlab

# This tutorial illustrates how you can use Landlab to construct a simple
# two-dimensional numerical model on a regular (raster) grid, using a simple
# forward-time, centered-space numerical scheme. The example is the erosional 
# degradation of an earthquake fault scarp, and which evolves over time in 
# response to the gradual downhill motion of soil. Here we use a simple
# "geomorphic diffusion" model for landform evolution, in which the downhill
# flow of soil is assumed to be proportional to the (downhill) gradient of the
# land surface multiplied by a transport coefficient.

# We start by importing the NumPy library, which we'll use for some array
# calculations:
import numpy

# We will create a grid for our model using Landlab's *RasterModelGrid* class, 
# which we need to import.
from landlab import RasterModelGrid

# The syntax in the next line says: create a new RasterModelGrid object called
# mg, with 25 rows, 40 columns, and a grid spacing of 10 m.
mg = RasterModelGrid((25, 40), 10.0)

# Now we'll add a data field to the grid, to represent the elevation values at
# grid nodes. The "dot" syntax indicates that we are calling a function (or 
# method) that belongs to the RasterModelGrid class, and will act on data
# contained in mg. The arguments indicate that we want the data elements
# attached to grid nodes (rather than links, for example), and that we want to
# name this data field land_surface__elevation. The add_zeros method returns
# the newly created NumPy array.
z = mg.add_zeros('node', 'land_surface__elevation')

# Let's take a look at the grid we've created. To do so, we'll use the
# Matplotlib graphics library (imported under the name plt).
import matplotlib.pyplot as plt

# Let's plot the positions of all the grid nodes. The nodes' (x,y) positions
# are stored in the arrays mg.node_x and mg.node_y, respectively.
plt.figure(1)
plt.plot(mg.node_x, mg.node_y, '.')
plt.show()

# There are 1000 grid nodes (25 x 40). The `z` array also has 1000 entries: 
# one per grid node.
len(z)

# Add a fault trace that angles roughly east-northeast.
fault_trace_y = 50.0 + 0.25*mg.node_x

# Find the ID numbers of the nodes north of the fault trace with help from 
# NumPy's `where()` function.
upthrown_nodes = numpy.where(mg.node_y > fault_trace_y)

# Add elevation equal to 10m for all the nodes north of the fault, plus 1cm
# for every meter east (just to make it interesting).
z[upthrown_nodes] += 10.0 + 0.01*mg.node_x[upthrown_nodes]

# Show the newly created initial topography using Landlab's *imshow_node_grid*
# plotting function (which we first need to import).
from landlab.plot.imshow import imshow_node_grid
plt.figure(2)
imshow_node_grid(mg, 'land_surface__elevation')
plt.show()

# To finish getting set up, we will define two parameters: the transport
# ("diffusivity") coefficient, D, and the time-step size, dt. (The latter is
# set using the Courant condition for a forward-time, centered-space
# finite-difference solution
D = 0.01  # m2/yr transport coefficient
dt = 0.2*mg.dx*mg.dx/D

# Boundary conditions: for this example, we'll assume that the east and west
# sides are closed to flow of sediment, but that the north and south sides are
# open. (The order of the function arguments is east, north, west, south)
mg.set_closed_boundaries_at_grid_edges(False, True, False, True)

# Loop through 25 iterations representing 50,000 years
for i in range(25):
    g = mg.calculate_gradients_at_active_links(z)
    qs = -D*g
    dqsdx = mg.calculate_flux_divergence_at_nodes(qs)
    dzdt = -dqsdx
    z[mg.core_nodes] += dzdt[mg.core_nodes]*dt

# Show how our fault scarp has evolved.
plt.figure(3)
imshow_node_grid(mg, 'land_surface__elevation')
plt.show()
