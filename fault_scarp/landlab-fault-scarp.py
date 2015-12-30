# Creating a simple 2D scarp diffusion model with Landlab

# Import the Numpy library, which we'll use for some array calculations
import numpy

# We will create a grid for our model using Landlab's *RasterModelGrid* class, which we need to import.
from landlab import RasterModelGrid

# Create a new *RasterModelGrid* object called **mg**, with 25 rows, 40 columns, and a grid spacing of 10 m.
mg = RasterModelGrid(25, 40, 10.0)

# Now add a *land_surface__elevation* field to the grid, to represent the elevation values at grid nodes.
z = mg.add_zeros('node', 'land_surface__elevation')

# Let's take a look at the grid we've created using the Pylab graphics library (imported under the name `plt`).
import pylab as plt

# Plot the positions of all the grid nodes.
plt.plot(mg.node_x, mg.node_y, '.')

# There are 1000 grid nodes (25 x 40). The `z` array also has 1000 entries: one per grid cell.
len(z)

# Add a fault trace that angles roughly east-northeast.
fault_trace_y = 50.0 + 0.25*mg.node_x

# Find the ID numbers of the nodes north of the fault trace with help from Numpy's `where()` function.
upthrown_nodes = numpy.where(mg.node_y > fault_trace_y)

# Add elevation equal to 10m for all the nodes north of the fault, plus 1cm for every meter east (just to make it interesting).
z[upthrown_nodes] += 10.0 + 0.01*mg.node_x[upthrown_nodes]

# Show the newly created initial topography using Landlab's *imshow_node_grid* plotting function (which we first need to import).
from landlab.plot.imshow import imshow_node_grid

imshow_node_grid(mg, 'land_surface__elevation')

# Define transport ("diffusivity") coefficient, `D`, and the time-step size, `dt`.
D = 0.01  # m2/yr transport coefficient
dt = 0.2*mg.dx*mg.dx/D
dt

# Set boundary conditions (ENWS)
mg.set_closed_boundaries_at_grid_edges(False, True, False, True)

# Calculate changes in elevation for nodes that are not boundaries
core_nodes = mg.core_nodes

len(core_nodes)

# Loop through 25 iterations representing 50,000 years
for i in range(25):
    g = mg.calculate_gradients_at_active_links(z)
    qs = -D*g
    dqsdx = mg.calculate_flux_divergence_at_nodes(qs)
    dzdt = -dqsdx
    z[core_nodes] += dzdt[core_nodes]*dt

# Show how our fault scarp has evolved.
imshow_node_grid(mg, 'land_surface__elevation')
