# # What happens when you create a grid object?

# Landlab supports a range of grid types. These include both rasters (with both
# square and rectangular cells), and a range of structured and unstructured
# grids based around the interlocking polygons and triangles of a
# Voronoi-Delaunay tesselation (radial, hexagonal, and irregular grids).
#
# Here, we look at some of the features of both of these types.
#
# We can create **grid** objects with the following lines of code.

# In[ ]:

import numpy as np
from landlab import RasterModelGrid, VoronoiDelaunayGrid, HexModelGrid
# a square-cell raster, 3 rows x 4 columns, unit spacing
smg = RasterModelGrid((3, 4), 1.)
rmg = RasterModelGrid((3, 4), (1., 2.))  # a rectangular-cell raster
hmg = HexModelGrid(3, 4, 1.)
# ^a hexagonal grid with 3 rows, 4 columns from the base row, & node spacing of
# 1.
x = np.random.rand(100) * 100.
y = np.random.rand(100) * 100.
vmg = VoronoiDelaunayGrid(x, y)
# ^a Voronoi-cell grid with 100 randomly positioned nodes within a 100.x100.
# square


# All these various `ModelGrid` objects contains various data items (known as
# *attributes*). These include, for example: * number nodes and links in the
# grid * *x* and *y* coordinates of each each node * starting ("tail") and
# ending ("head") node IDs of each link * IDs of links that are active * IDs of
# core nodes * etc.
#
# From here on we'll focus on the square raster grid as its geometry is a bit
# easier to think through, but all of the following applies to all grid types.
#
# ## Understanding the topology of Landlab grids
#
# All grids consist of two interlocked sets of *points* joined by *lines*
# outlining *areas*. If we define data on the points we call **nodes**, then
# they are joined by **links** which outline **patches**. Each node within the
# interior of the grid lies at the geometric center of the area of a **cell**.
# The cell's edges are **faces**, and the point at the edge of each face is a
# **corner**.
#
# Note that this kind of scheme requires one set of features to be "dominant"
# over the other; i.e., either not every node has a cell, *or* not every link is
# crossed by a face. Both cannot be true, because one or other set of features
# has to define the edge of the grid. Landlab assumes that the node set is
# primary, so there are always more nodes than corners; more links than faces;
# and more patches than cells.
#
# Each of these sets of *"elements"* has its own set of IDs. These IDs are what
# allow us to index the various Landlab fields which store spatial data. Each
# feature is ordered by **x, then y**. The origin is always at the bottom left
# node, unless you choose to move it (`grid.move_origin`)... except in the
# specific case of a radial grid, where logic and symmetry dictates it must be
# the central node.
#
# Whenever Landlab needs to order something rotationally (angles; elements
# around a different element type), it does so following the standard
# mathematical convention of **counterclockwise from east**. We'll see this in
# practical terms a bit later in this tutorial.
#
# The final thing to know is that **lines have direction**. This lets us record
# fluxes on the grid by associating them with, and mapping them onto, the links
# (or, much less commonly, the faces). All lines point into the **upper right
# quadrant**. So, on our raster, this means the horizontal links point east an
# the vertical links point north.
#
# So, for reference, our raster grid looks like this:
#
#
#     NODES:                       LINKS:                       PATCHES:
#     8 ----- 9 ---- 10 ---- 11    * -14-->* -15-->* -16-->*    * ----- * ----- * ----- *
#     |       |       |       |    ^       ^       ^       ^    |       |       |       |
#     |       |       |       |   10      11      12      13    |   3   |   4   |   5   |
#     |       |       |       |    |       |       |       |    |       |       |       |
#     4 ----- 5 ----- 6 ----- 7    * --7-- * --8-- * --9-- *    * ----- * ----- * ----- *
#     |       |       |       |    ^       ^       ^       ^    |       |       |       |
#     |       |       |       |    3       4       5       6    |   0   |   1   |   2   |
#     |       |       |       |    |       |       |       |    |       |       |       |
#     0 ----- 1 ----- 2 ----- 3    * --0-->* --1-->* --2-->*    * ----- * ----- * ----- *
#
#     CELLS:                       FACES:                       CORNERS:
#     * ----- * ----- * ----- *    * ----- * ----- * ----- *    * ----- * ----- * ----- *
#     |       |       |       |    |       |       |       |    |       |       |       |
#     |   . ----- . ----- .   |    |   . --5-->. --6-->.   |    |   3 ----- 4 ----- 5   |
#     |   |       |       |   |    |   ^       ^       ^   |    |   |       |       |   |
#     * --|   0   |   1   |-- *    * --2       3       4-- *    * --|       |       |-- *
#     |   |       |       |   |    |   |       |       |   |    |   |       |       |   |
#     |   . ----- . ----- .   |    |   . --0-->. --1-->.   |    |   0 ----- 1 ----- 2   |
#     |       |       |       |    |       |       |       |    |       |       |       |
#     * ----- * ----- * ----- *    * ----- * ----- * ----- *    * ----- * ----- * ----- *
#
#
# ## Recording and indexing the values at elements
#
# Landlab lets you record values at any element you want. In practice, the most
# useful places to store data is on the primary elements of nodes, links, and
# patches, the the nodes being most useful for scalar values (e.g, elevations)
# and the links for fluxes with direction to them (e.g., discharges).
#
# In order to maintain compatibility across data types, *all* landlab data is
# stored in *number-of-elements*-long arrays. This includes both user-defined
# data and the properties of the nodes within the grid. This means that these
# arrays can be immediately indexed by their element ID. In other words:

# In[ ]:

# what's the y-coordinates of the pair of nodes in the middle of our 3-by-4
# grid? the IDs of these nodes are 5 and 6, so:
smg.y_of_node[[5, 6]]


# If you're working with a raster, you can always reshape the value arrays back
# into two dimensions so you can take Numpy-style slices through it:

# In[ ]:

# what's the x-coordinates of the middle row?
smg.x_of_node.reshape(smg.shape)[1, :]


# This same data storage pattern is what underlies the Landlab **data fields**,
# which are simply one dimensional, number-of-elements-long arrays which store
# user defined spatial data across the grid, attached to the grid itself.

# In[ ]:

smg.add_zeros('node', 'elevation', noclobber=False)
# ^Creates a new field of zero data associated with nodes
smg.at_node['elevation']  # Note the use of dictionary syntax


# Or, equivalently, at links:

# In[ ]:

smg.add_ones('link', 'slope', noclobber=False)
# ^Creates a new array of data associated with links
smg.at_link['slope']


# The Landlab **components** use fields to share spatial information between
# themselves. See the *fields* and *components* tutorials for more information.
#
#
# ## Getting this information from the grid object
#
# All of this topological information is recorded within our grid objects, and
# can be used to work with data that is defined over the grid. The grids record
# the numbers of each element, their positions, and their interrelationships to
# each other. Let's take a look at some of this information for the raster:

# In[ ]:

smg.number_of_nodes


# In[ ]:

smg.number_of_links


# The grid contains its geometric information too. Let's look at the *(x,y)*
# coordinates of the nodes:

# In[ ]:

for i in range(smg.number_of_nodes):
    print(i, smg.x_of_node[i], smg.y_of_node[i])


# Link connectivity and direction is described by specifying the starting
# ("tail") and ending ("head") node IDs for each link (to remember this, think
# of an arrow: TAIL ===> HEAD).

# In[ ]:

for i in range(smg.number_of_links):
    print('Link',i,':  node',smg.node_at_link_tail[i],'===> node',smg.node_at_link_head[i])


# Boundary conditions are likewise defined on these elements (see also the full
# boundary conditions tutorial). Landlab is clever enough to ensure that the
# boundary conditions recorded on, say, the links get updated when you redefine
# the conditions on, say, the nodes.
#
# Nodes can be *core*, *fixed value*, *fixed gradient*, or *closed* (flux into
# or out of node is forbidden). Links can be *active* (can carry flux), *fixed*
# (always  carries the same flux; joined to a fixed gradient node) or *inactive*
# (forbidden from carrying flux). This information is likewise available from
# the grid:

# In[ ]:

smg.core_nodes


# In[ ]:

smg.active_links


# In[ ]:

# let's demonstrate the auto-updating of boundary conditions:
from landlab import CLOSED_BOUNDARY
smg.status_at_node[smg.nodes_at_bottom_edge] = CLOSED_BOUNDARY
smg.active_links  # the links connected to the bottom edge nodes are now inactive


# ### Element connectivity
#
# Importantly, we can also find out which elements are connected to which other
# elements. This allows us to do computationally vital operations involving
# mapping values defined at one element onto another, e.g., the net flux at a
# node; the mean slope at a patch; the node value at a cell.
#
# In cases where these relationships are one-to-many (e.g., `links_at_node`,
# `nodes_at_patch`), the shape of the resulting arrays is always
# (number_of_elements, max-number-of-connected-elements-across-grid). i.e., on a
# raster, `links_at_node` is (nnodes, 4), because the cells are always square.
# On an irregular Voronoi-cell grid, `links_at_node` will be (nnodes, X) where X
# is the number of sides of the side-iest cell, and `nodes_at_patch` will be
# (npatches, 3) because all the patches are Delaunay triangles. And so on.
#
# Lets take a look. Remember, Landlab orders things **clockwise from east**, so
# for a raster the order will the EAST, NORTH, WEST, SOUTH.

# In[ ]:

smg.links_at_node[5]


# In[ ]:

smg.links_at_node.shape


# Undefined directions get recorded as `-1`:

# In[ ]:

smg.links_at_node[8]


# In[ ]:

smg.patches_at_node


# In[ ]:

smg.nodes_at_patch


# Where element-to-element mapping is one-to-one, you get simple, one
# dimensional arrays:

# In[ ]:

smg.node_at_cell  # shape is (n_cells, )


# In[ ]:

smg.cell_at_node  # shape is (n_nodes, ) with -1s as needed


# A bit of thought reveals that things get a bit more complicated for links and
# faces, because they have direction. You'll need a convenient way to record
# whether a given flux (which is positive if it goes with the link's inherent
# direction, and negative if against) actually is travelling into or out of a
# given node. The grid provides `link_dirs_at_node` and
# `active_link_dirs_at_node` to help with this:

# In[ ]:

smg.link_dirs_at_node  # all links; positive points INTO the node; zero where no link


# In[ ]:

# prove there are zeros where links are missing:
np.all((smg.link_dirs_at_node == 0) == (smg.links_at_node == -1))


# In[ ]:

smg.active_link_dirs_at_node  # in this one, inactive links get zero too


# Multiply the fluxes indexed by `links_at_node` and sum by axis=1 to have a
# very convenient way to calculate flux divergences at nodes:

# In[ ]:

fluxes_at_node = smg.at_link['slope'][smg.links_at_node]
# ^...remember we defined the slope field as ones, above
fluxes_into_node = fluxes_at_node*smg.active_link_dirs_at_node
flux_div_at_node = fluxes_into_node.sum(axis=1)
print(flux_div_at_node[smg.core_nodes])


# Why? Remember that earlier in this tutorial we already set the bottom edge to
# `CLOSED_BOUNDARY`. So each of our core nodes has a flux of +1.0 coming in from
# the left, but two fluxes of -1.0 leaving from both the top and the right.
# Hence, the flux divergence is -1. at each node.
#
# Note as well that Landlab offers the one-line grid method
# `calc_flux_div_at_node()` to perform this same operation.

# ### Click here for more <a
# href="https://github.com/landlab/landlab/wiki/Tutorials">Landlab tutorials</a>
