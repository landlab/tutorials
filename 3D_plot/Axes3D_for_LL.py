"""
 Plot a surface + points (clasts) on it

 Use matplotlib Axes3D.plot_surface and Axes3D.scatter3D

 Axes3D.plot_surface(X, Y, Z, *args, **kwargs)
 X, Y and Z are 2D arrays of similar shape.
 In our case, the plot is clearer if we don't plot boundary nodes
 (but that could bean option). So the shape is that of the LL grid
 core nodes.

 X = dx * [[1, 2, 3, ..., nb_of_columns-1]
           [1, 2, 3, ..., nb_of_columns-1]
                        ...
           [1, 2, 3, ..., nb_of_columns-1]]

 Y = dy * [[1, 1, 1, ..., 1]
           [2, 2, 2, ..., 2]
                 ...
           [nb_of_rows-1, ..., nb_of_rows-1]]

 Z = [[z_core_node1, z_core_node2, ...]
      [..., ...                      ]
                   ...
      [...,                          ]

 The rstride and cstride kwargs set the stride used to sample the input data
 to generate the graph. If 1k by 1k arrays are passed in, the default values
 for the strides will result in a 100x100 grid being plotted. Defaults to 10.

 The kwargs alpha sets the transparency factor (0 to 1).

 The LL nodes are at the crossing of the white lines that form the surface
 (the surface is made of LL patches, not cells).


 Axes3D.scatter(xs, ys, zs=0, zdir='z', s=20, c=None,
   depthshade=True, *args, **kwargs)
 xs, ys, zs are 1D arrays defining the position of the points.
 s = size (in points, so relation to the space scales of the plot itself is
 not straightforward...)
 c = color
 depthshade = Whether or not to shade the scatter markers to give the
   appearance of depth. Default is True.
"""

from landlab import RasterModelGrid
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


### Create Raster Model Grid
rows = 20
columns = 25
dx = 1
dy = 2

mg = RasterModelGrid((rows, columns), spacing=(dy, dx))

# Add elevation field
z = mg.node_y*0.1
_ = mg.add_field('topographic__elevation', z, at='node')

# Shape of core nodes:
# to be modified for more complex grids (use a mask?)
number_of_core_node_rows = mg.number_of_node_rows - 2
number_of_core_node_columns = mg.number_of_node_columns - 2

#####################################################################

### Data for 3D plot of topographic surface
xplot = mg.node_x[mg.core_nodes].reshape((
        number_of_core_node_rows, number_of_core_node_columns))
yplot = mg.node_y[mg.core_nodes].reshape((
        number_of_core_node_rows, number_of_core_node_columns))

# Elevation of core nodes, reshaped for 3D plot:
zplot = mg.at_node['topographic__elevation'][mg.core_nodes].reshape(
        (number_of_core_node_rows, number_of_core_node_columns))

#####################################################################

### 3D plot of elevation surface:
# Figure and type of projection:
fig = plt.figure(1)
ax = plt.axes(projection='3d')

# Plot surface:
ax.plot_surface(xplot, yplot, zplot, cmap='binary', rstride=1, cstride=1,
                alpha=0.5)

# Set initial view of the graph (elevation and azimuth):
ax.view_init(elev=None, azim=-130)

ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.set_zlabel('Z axis')

#####################################################################

### Data for 3D plot of topographic surface
# The Clast Set class (from Clast Tracker) provides
# clast node ID, x and y coordinates, clast elevation, etc.
# but for this example, we define them here:

clast__node = np.array([382, 386, 386, 390, 392, 392, 392, 392])
clast__number = clast__node.size

clast__x = mg.node_x[clast__node]
clast__y= mg.node_y[clast__node]

clast__elevation = np.array([3, 3, 3, 3, 3, 3, 3, 3])
clast__size = np.array([0.5, 0.5, 0.5, 1, 1, 1, 1, 1])

# For display purpose, clasts sizes are increased:
# Marker size is in "points"...
sizes = clast__size * 100

# Count the number of clast on each node (WILL PUT THIS IN THE CLAST TRACKER)
clast__number_at_node = np.zeros(mg.number_of_nodes)
for i in range(0, mg.number_of_nodes):
    clast__number_at_node[i] = list(clast__node).count(mg.nodes.reshape(
            clast__number_at_node.shape)[i])

# Assign colors to clast markers as a function of clast density on the node:
clast__color = np.zeros(clast__number)
for j in range(0, clast__number):
    clast__color[j] = clast__number_at_node[clast__node[j]]

#####################################################################

### 3D plot of points (scatter):

plot = ax.scatter(clast__x, clast__y, clast__elevation, marker='H',
                  s=sizes, c=clast__color, label=clast__color, cmap='cool')
cbar = plt.colorbar(plot, ticks=[1, 2, 3, 4], shrink=0.7)
cbar.set_label('# of clasts')
