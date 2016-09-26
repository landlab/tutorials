
# # Using the Landlab flexure component
# 

# In this example we will:
# * create a Landlab component that solves the flexure equation
# * apply randomly distributed point loads
# * run the component
# * plot some output


import numpy as np


# ## Create the grid
# 
# We are going to build a uniform rectilinear grid with a node spacing of 10 km in the *y*-direction and 20 km in the *x*-direction on which we will solve the flexure equation.
# 
# First we nee to import *RasterModelGrid*.  We also import the Landlab plotting function *imshow_grid* to view the grids.


from landlab import RasterModelGrid
from landlab.plot.imshow import imshow_grid


# Create a rectilinear grid with a spacing of 10 km between rows and 20 km between columns. The numbers of rows and columms are provided as a `tuple` of `(n_rows, n_cols)`, in the same manner as similar numpy functions. The spacing is also a `tuple`, `(dy, dx)`.


grid = RasterModelGrid((200, 400), spacing=(10e3, 20e3))



grid.dy, grid.dx


# ## Create the component

# Now we create the flexure component and tell it to use our newly-created grid. First, though, we'll examine the Flexure component a bit.



from landlab.components.flexure import Flexure


# The Flexure component, as with most landlab components, will require our grid to have some data that it will use. We can get the names of these data fields with the `intput_var_names` attribute of the component *class*.



Flexure.input_var_names


# We see that flexure uses just 1 data field: the change in lithospheric loading. landlab component classes can provide additional information about each of these fields. For instance, to the the units for a field, use the `var_units` method.

 

Flexure.var_units('lithosphere__overlying_pressure_increment')


# To print a more detailed description of a field, use `var_help`.

 

Flexure.var_help('lithosphere__overlying_pressure_increment')


# What about the data that `Flexure` provides? Use the `output_var_names` attribute.

 

Flexure.output_var_names


 

Flexure.var_help('lithosphere_surface__elevation_increment')


# Now that we understand the component a little more, create it using our grid.

 

flex = Flexure(grid, method='flexure')


# ## Add some loading
# We will add loads to the grid. As we saw above, for this component, the name of the variable that hold the applied loads is call, `lithosphere__overlying_pressure`. We add loads of random magnitude at every node of the grid.

 

load = np.random.normal(0, 100 * 2650. * 9.81, grid.number_of_nodes)
grid.at_node['lithosphere__overlying_pressure_increment'] = load


 

imshow_grid(grid, 'lithosphere__overlying_pressure_increment', symmetric_cbar=True,
            cmap='spectral', show=True)


# ## Update the component to solve for deflection
# If you have more than one processor on your machine you may want to use several of them.

 

flex.update(n_procs=4)


# As we saw above, the flexure component creates an output field (`lithosphere_surface__elevation_increment`) that contains surface deflections for the applied loads.

# # Plot the output

# We now plot these deflections with the `imshow` method, which is available to all landlab components.

 

imshow_grid(grid, 'lithosphere_surface__elevation_increment', symmetric_cbar=True,
            cmap='spectral', show=True)


# Maintain the same loading distribution but double the effective elastic thickness.

 

flex.eet *= 2.
flex.update(n_procs=4)
imshow_grid(grid, 'lithosphere_surface__elevation_increment', symmetric_cbar=True,
            cmap='spectral', show=True)


# Now let's add a vertical rectangular load to the middle of the grid.  We plot the load grid first to make sure we did this correctly.

 

load[np.where(np.logical_and(grid.node_x>3000000, grid.node_x<5000000))]=     load[np.where(np.logical_and(grid.node_x>3000000, grid.node_x<5000000))]+1e7
imshow_grid(grid, 'lithosphere__overlying_pressure_increment', symmetric_cbar=True,
            cmap='spectral', show=True)


 

flex.update(n_procs=4)
imshow_grid(grid, 'lithosphere_surface__elevation_increment', symmetric_cbar=True,
            cmap='spectral', show=True)


# ### Click here for more <a href="https://github.com/landlab/landlab/wiki/Tutorials">Landlab tutorials</a>
