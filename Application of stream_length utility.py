
# coding: utf-8

# <a href="http://landlab.github.io"><img style="float: left" src="https://raw.githubusercontent.com/landlab/tutorials/master/landlab_header.png"></a>

# For instructions on how to run an interactive iPython notebook, click here: https://github.com/landlab/tutorials/blob/master/README.md
# For the unexpanded version to download and run, click here:http://nbviewer.jupyter.org/github/landlab/tutorials/blob/master/component_tutorial/component_tutorial_unexpanded.ipynb
# For more Landlab tutorials, click here: https://github.com/landlab/landlab/wiki/Tutorials

# **Application of the stream_length utility on a Sicilian basin**

# This notebook illustrates how to run the stream_length utility on a real topography. For first, a watershed will be extracted from an input DEM by using the watershed utility. Then, a spatial distribution of the distances from each node to the watershed's outlet according to the path set with the D8 algorithm, will be obtained with the stream_length utility.

# First, import what we'll need:

# In[1]:


from landlab.io import read_esri_ascii
from landlab.components import FlowAccumulator
from landlab.plot import imshow_grid
from matplotlib.pyplot import figure
from landlab.utils import watershed
import numpy as np
from landlab.utils.stream_length import calculate_stream_length


# Import a square DEM that includes the watershed:

# In[2]:


(mg, z) = read_esri_ascii('nocella.txt', name='topographic__elevation')


# Run the FlowAccumulator and the DepressionFinderAndRouter components to find depressions, to route the flow across them and to calculate flow direction and drainage area:

# In[3]:


fr = FlowAccumulator(mg, flow_director = 'D8', depression_finder = 'DepressionFinderAndRouter')
fr.run_one_step()


# Fix the outlet's id (the one indicated in this example is the whole watershed's outlet):

# In[4]:


outlet_id = 95913


# Run the watershed utility and show the watershed mask:

# In[5]:


ws_mask = watershed.get_watershed_mask(mg, outlet_id)
figure(); imshow_grid(mg, ws_mask)


# Run the stream_length utility:

# In[6]:


stream__length = calculate_stream_length(mg, add_to_grid=True, noclobber=False)


# Mask the stream__length to the watershed mask:

# In[7]:


flow_length = np.zeros(len(ws_mask))
for i in range (0,len(ws_mask)):
    if ws_mask[i] == True:
        flow_length[i] = stream__length[i]-stream__length[outlet_id]
    else:
        flow_length[i] = 0


# Add the flow_length field to the grid and show the spatial distribution of the distances from each node to the watershed's outlet:

# In[8]:


mg.add_field('node','flow_length',flow_length)
figure(); imshow_grid(mg, mg['node']['flow_length'])

