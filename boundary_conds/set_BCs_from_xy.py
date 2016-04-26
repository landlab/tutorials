
# Modify the boundary conditions of an interior rectangle in the grid

from landlab import RasterModelGrid, CLOSED_BOUNDARY
import numpy as np
from landlab.plot.imshow import imshow_node_grid
from matplotlib.pyplot import show

mg = RasterModelGrid((10, 10), 1.)

min_x = 2.5
max_x = 5.
min_y = 3.5
max_y = 7.5

x_condition = np.logical_and(mg.node_x < max_x, mg.node_x > min_x)
y_condition = np.logical_and(mg.node_y < max_y, mg.node_y > min_y)
my_nodes = np.logical_and(x_condition, y_condition)

mg.status_at_node[my_nodes] = CLOSED_BOUNDARY

z = mg.add_zeros('node', 'topographic__elevation')

imshow_node_grid(mg, z)
show()