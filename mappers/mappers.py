# # Mapping values between grid elements
# 
# Imagine that you're using Landlab to write a model of shallow water flow over
# terrain. A natural approach is to place your scalar fields, such as water
# depth, at the nodes. You then place your vector fields, such as water surface
# gradient, flow velocity, and discharge, at the links. But your velocity
# depends on both slope and depth, which means you need to know the depth at
# the links too. How do you do this?
# 
# This tutorial introduces *mappers*: grid functions that map quantities
# defined on one set of elements (such as nodes) onto another set of elements
# (such as links). As you'll see, there are a variety of mappers available.
# 
# 

# ## Mapping from nodes to links
# 
# For the sake of example, we'll start with a simple 3-row by 4-column raster
# grid. The grid will contain a scalar field called `water__depth`, abbreviated
# `h`. We'll populate it with some example values, as follows:

# In[1]:

from __future__ import print_function
from landlab import RasterModelGrid
import numpy as np
mg = RasterModelGrid((3, 4), 100.0)
h = mg.add_zeros('node', 'surface_water__depth')
h[:] = 7 - np.abs(6 - np.arange(12))


# For the sake of visualizing values at nodes on our grid, we'll define a handy
# little function:

# In[2]:

def show_node_values(mg, u):
    for r in range(mg.number_of_node_rows - 1, -1, -1):
        for c in range(mg.number_of_node_columns):
            print(int(u[c + (mg.number_of_node_columns * r)]), end=' ')
        print()


# In[3]:

show_node_values(mg, h)


# Let's review the numbering of nodes and links. The lines below will print a
# list that shows, for each link ID, the IDs of the nodes at the link's tail
# and head:
# 
# In[4]:

for i in range(mg.number_of_links):
    print(i, mg.node_at_link_tail[i], mg.node_at_link_head[i])


# ### Finding the mean value between two nodes on a link
# 
# Suppose we want to have a *link-based* array, called *h_edge*, that contains
# water depth at locations between adjacent pairs of nodes. For each link,
# we'll simply take the average of the depth at the link's two nodes. To
# accomplish this, we can use the `map_mean_of_link_nodes_to_link` grid method.
# At link 8, for example, we'll average the *h* values at nodes 5 and 6, which
# should give us a depth of (6 + 7) / 2 = 6.5:

# In[5]:

h_edge = mg.map_mean_of_link_nodes_to_link('surface_water__depth')
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# ### What's in a name?
# 
# The mapping function has a long name, which is designed to make it as clear
# as possible to understand what the function does. All the mappers start with
# the verb *map*. Then the relationship is given; in this case, we are looking
# at the *mean*. Then the elements from which a quantity is being mapped: we
# are taking values from *link nodes*. Finally, the element to which the new
# values apply: *link*.
# 
# ### Mapping minimum or maximum values
# 
# We can also map the minimum value of *h*:

# In[6]:

h_edge = mg.map_min_of_link_nodes_to_link('surface_water__depth')
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# ... or the maximum:

# In[7]:

h_edge = mg.map_max_of_link_nodes_to_link('surface_water__depth')
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# ### Upwind and downwind
# 
# Numerical schemes often use *upwind differencing* or *downwind differencing*.
# For example, finite difference schemes for equations that include advection
# may use "upwind" rather than centered differences, in which a scalar quantity
# (our *h* for example) is taken from whichever side is upstream in the flow
# field.
# 
# How do we know the flow direction? If the flow is driven by the gradient in
# some scalar field, such as pressure or elevation, one approach is to look at
# the values of this scalar on either end of the link: the end with the higher
# value is upwind, and the end with the lower value is downwind.
# 
# Suppose for example that our water flow is driven by the water-surface slope
# (which is often a good approximation for the *energy slope*, though it omits
# the kinetic energy). Let's define a bed-surface elevation field *z*:

# In[8]:

z = mg.add_zeros('node', 'topographic__elevation')
z[:] = 16 - np.abs(7 - np.arange(12))
show_node_values(mg, z)


# The water-surface elevation is then the sum of *h* and *z*:

# In[9]:

w = z + h
show_node_values(mg, w)


# For every link, we can assign the value of *h* from whichever end of the link
# has the greater *w*:

# In[10]:

h_edge = mg.map_value_at_max_node_to_link(w, h)
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# Consider the middle two nodes (5 and 6). Node 6 is higher (22 versus 20).
# Therefore, the link between them (link 8) should be assigned the value of *h*
# at node 6. This value happens to be 7.0.
# 
# Of course, we could also take the value from the *lower* of the two nodes,
# which gives link 8 a value of 6.0:

# In[11]:

h_edge = mg.map_value_at_min_node_to_link(w, h)
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# ### Heads or tails?
# 
# It is also possible to map the scalar quantity at either the head node or the
# tail node to the link:

# In[12]:

h_edge = mg.map_link_head_node_to_link('surface_water__depth')
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# In[13]:

h_edge = mg.map_link_tail_node_to_link('surface_water__depth')
for i in range(mg.number_of_links):
    print(i, h_edge[i])


# ### Simple example using centered water depth
# The following implements one time-step of a linear-viscous flow model, in
# which flow velocity is calculated with depth at the links is taken as the
# mean of depth at the two bounding nodes. To make the flow a little tamer,
# we'll have our fluid be basaltic lava instead of water, with a dynamic
# viscosity of 100 Pa s.

# In[14]:

gamma = 25000.0  # unit weight of fluid, N/m2
viscosity = 100.0  # dynamic viscosity in Pa s
grad = mg.calc_grad_at_link(w)
h_edge = mg.map_mean_of_link_nodes_to_link(h)
vel = -(gamma / viscosity) * h_edge * h_edge * grad
for ln in range(mg.number_of_links):
    print(ln, h_edge[ln], grad[ln], vel[ln])


# I'm not sure I love the idea of a 5-m thick lava flow moving at over 100 m/s!
# (I guess we can take some comfort from the thought that turbulence would
# probably slow it down)
# 
# How different would the numerical solution be using an upwind scheme for flow
# depth? Let's find out:

# In[15]:

h_edge = mg.map_value_at_max_node_to_link(w, h)
vel = -(gamma / viscosity) * h_edge * h_edge * grad
for ln in range(mg.number_of_links):
    print(ln, h_edge[ln], grad[ln], vel[ln])


# Still pretty scary.
# 
# In any event, this example illustrates how you can use Landlab's mapping
# functions to build mass-conservation models in which the flow rate depends on
# a gradient and a scalar, both of which can be evaluated at links.
