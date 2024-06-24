#!/usr/bin/env python
# coding: utf-8

# ### JOHN KENNEDY BOAFO  
# 
# 

# ## Objective
# To download Sentinel satellite images for a speciﬁed
# area of interest (AOI) in GeoJSON or shapeﬁle format, covering speciﬁed periods. Additionally, the script should calculate the
# Normalized Difference Vegetation Index (NDVI) statistics for the AOI and plot the change in vegetation over time on a graph.
# Calculate the Mean, Minimum and Maximum NDVI 

# #### Used Google Earth Engine(GEE) Python API

# In[2]:


#Importing the Module and authenticating google earth engine

import os
import ee
import geemap
import pandas as pd
import geopandas as gpd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from ipywidgets import Output
from ipyleaflet import WidgetControl


# In[3]:


#ee.Authenticate()


# In[4]:


# Initialize Earth Engine
ee.Initialize()


# In[5]:


# Load the shapefile(AOI) using GeoPandas
GH_shp = gpd.read_file('C:/Users/user/Documents/Ghana Shapefile (New)/GHANA BD/GHANA_BD.shp')


# In[6]:


# Create a GeoJSON representation from the GeoPandas dataframe
GH_geojson = geemap.gdf_to_ee(GH_shp)


# In[7]:


#Using Basemaps
Map = geemap.Map()
Map.centerObject(GH_geojson,7)  


# In[8]:


# Define the Sentinel-2 collection with AOI
start_date = '2023-01-01'
end_date = '2023-12-31'

# Filter the sentinel data by date and cover
sentinel2A_data = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterMetadata("CLOUD_COVERAGE_ASSESSMENT",'less_than',20).filterDate(start_date,end_date).filterBounds(GH_geojson);


# Check if there are any images available
count = sentinel2A_data.size().getInfo()
if count == 0:
    print("No images available for the specified criteria.")


# In[9]:


#  NDVI COMPUTATION
def calculate_ndvi(image):
    # Get the 'CLOUD_COVERAGE_ASSESSMENT' property of the image
    cloudCoverage = ee.Number(image.get('CLOUD_COVERAGE_ASSESSMENT'))

    # Calculate NDVI
    ndviImage = image.expression(
        '(NIR - RED) / (NIR + RED)',
        {
            'NIR': image.select('B8'),
            'RED': image.select('B4'),
        }
    ).float().rename('NDVI').copyProperties(image, ["system:time_start"])
    return ndviImage.set('CLOUD_COVERAGE_ASSESSMENT', cloudCoverage) 


# In[11]:


# Calculate NDVI for the filtered sentinel data collection
ndvi_data = sentinel2A_data.map(calculate_ndvi)


# In[12]:


# Clip the NDVI to the shapefile with median composite
ndvi_clip = ndvi_data.mean().clip(GH_geojson)


# In[13]:


# Center the map on the shapefile
Map.centerObject(GH_geojson, 7)  


# In[14]:


#Normalized Difference Vegetation Index (NDVI) value range = -1 to 1
# Add the NDVI layer on top
ndvi_param = {
    'min': -1,
    'max': 1,
    'palette': ['d73027', 'f46d43', 'fdae61', 'fee08b',
        'ffffbf', 'd9ef8b', 'a6d96a', '66bd63','1a9850','006837']
}
Map.addLayer(ndvi_clip, ndvi_param, 'NDVI')


# In[16]:


# Add the colorbar legend
Map.add_colorbar(ndvi_param['palette'], vmin=ndvi_param['min'], vmax=ndvi_param['max'], label='NDVI')


# Add layer control to toggle the NDVI layer
Map.addLayerControl()


# Define the NDVI color palette
#     "#8B4513",  # Barren land, non-vegetated (-1.0 to -0.1)
#     "#A52A2A",  # Bare soil, sparse vegetation (-0.1 to 0.0)
#     "#FFFF00",  # Sparse vegetation (0.0 to 0.2)
#     "#ADFF2F",  # Moderate vegetation (0.2 to 0.4)
#     "#00FF00",  # Healthy vegetation (0.4 to 0.6)
#     "#006400",  # Very healthy vegetation (0.6 to 0.8)
#     "#003300"   # Extremely healthy vegetation, dense forest (0.8 to 1.0)

# In[17]:


Map


# In[18]:


image = ndvi_clip

# Define the region from the GeoJSON object
region = GH_geojson.geometry()


# In[19]:


# Generate the thumbnail with appropriate dimensions
out_img = 'C:/Users/user/Documents/GEEMAP Projects/NDVI/GH_NDVI2023.png'
dimensions = 1000  # Increase dimensions for better coverage

# Generate the thumbnail
geemap.get_image_thumbnail(image, out_img, vis_params=ndvi_param, dimensions=dimensions, region=region.getInfo(), format='png')


# In[20]:


geemap.show_image(out_img)


# In[23]:





# In[24]:


# Create a list of dates, NDVI stats and 'CLOUD_COVERAGE_ASSESSMENT' values for the chart
def createChartData(image):
    date = ee.Date(image.get('system:time_start'))
    ndviValue = image.reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = GH_geojson,
        scale = 10,
        maxPixels = 1e13
    ).get('NDVI')
    cloudPercentage = image.get('CLOUD_COVERAGE_ASSESSMENT')
    
    return ee.Feature(None, {
        'date': date,
        'NDVI': ndviValue,
        'Cloudy Percentage': cloudPercentage,
       
    })
chartData = ndvi_data.map(createChartData)


# In[25]:


# Extract dates and values from chartData
dates = chartData.aggregate_array('date').getInfo()
ndviValues = chartData.aggregate_array('NDVI').getInfo()
cloudPercentages = chartData.aggregate_array('Cloudy Percentage').getInfo()


# In[26]:


# Convert dates to Python datetime objects
formatted_dates = [datetime.datetime.fromtimestamp(date['value'] / 1000) for date in dates]


# In[27]:


# Create a DataFrame from the chart data
data = {
    'date': formatted_dates,
    'NDVI': ndviValues,
    'Cloudy Percentage': cloudPercentages
}
df = pd.DataFrame(data)


# In[28]:


# Drop rows with None values
df.dropna(subset=['NDVI'], inplace=True)


# In[29]:


print(df['date'].dtype)  


# In[30]:


# Convert date to string for grouping (if needed)
df['date'] = df['date'].dt.strftime('%Y-%m-%d')


# In[31]:


# Group by date and calculate mean, max, and min NDVI values
grouped_df = df.groupby('date')['NDVI'].agg(['mean', 'max', 'min']).reset_index()


# In[32]:


# Plot the mean, max, and min NDVI values over time
plt.figure(figsize=(20, 10))
plt.plot(grouped_df['date'], grouped_df['mean'], label='Mean NDVI', color='blue',linewidth=3,marker='o', markersize=8)
plt.plot(grouped_df['date'], grouped_df['max'], label='Maximum NDVI', color='red', linestyle='--',linewidth=3)
plt.plot(grouped_df['date'], grouped_df['min'], label='Minimum NDVI', color='green', linestyle='--',linewidth=3)
plt.xlabel('Date', fontsize=16)
plt.ylabel('NDVI Value', fontsize=16)
plt.title('Mean, Max, and Min NDVI values(2023)', fontsize=20)
plt.legend(fontsize=16)
plt.grid(True)


# Set x-axis ticks to show only a few labels
plt.xticks(grouped_df['date'][::20])  # Show every 2nd date label

plt.xticks(rotation=45)
plt.tight_layout()

# Increase fontsize for all tick labels
plt.tick_params(axis='both', which='major', labelsize=14)
plt.show()

plt.savefig('C:/Users/user/Documents/GEEMAP Projects/NDVI/NDVI2023.png')


# Fill in the area between max and min

# In[46]:


# Plot the mean, max, and min NDVI values over time
plt.figure(figsize=(20, 10))

# Plot mean NDVI
plt.plot(grouped_df['date'], grouped_df['mean'], label='Mean NDVI', color='blue', linewidth=3, marker='o', markersize=8)

# Plot max NDVI
plt.plot(grouped_df['date'], grouped_df['max'], label='Maximum NDVI', color='red', linestyle='--', linewidth=3)

# Plot min NDVI
plt.plot(grouped_df['date'], grouped_df['min'], label='Minimum NDVI', color='green', linestyle='--', linewidth=3)

# Fill the area between max and min
plt.fill_between(grouped_df['date'], grouped_df['min'], grouped_df['max'], color='#99cc00', alpha=0.3)

plt.xlabel('Date', fontsize=16, fontweight='bold')
plt.ylabel('NDVI Value', fontsize=16, fontweight='bold')
plt.title('Mean, Max, and Min NDVI values (2023)', fontsize=20, fontweight='bold')
plt.legend(fontsize=16)
plt.grid(True)

# Set x-axis ticks to show only a few labels
plt.xticks(grouped_df['date'][::20], rotation=45)  # Show every 20th date label with rotation

plt.tight_layout()

# Increase fontsize for all tick labels
plt.tick_params(axis='both', which='major', labelsize=14)

# Save the histogram as an image
plt.savefig('C:/Users/user/Documents/GEEMAP Projects/NDVI/NDVI_MINMAX.png', dpi=300)

plt.show()


# In[45]:


# For demonstration, let's create a DataFrame with random NDVI values
np.random.seed(42)
ndvi_data = pd.DataFrame({'NDVI': np.random.normal(loc=0.5, scale=0.2, size=1000)})

# Plot the histogram
plt.style.use('seaborn-whitegrid')
plt.figure(figsize=(10, 6))
plt.hist(ndvi_data['NDVI'], bins=30, color='#99cc00', edgecolor='black', alpha=0.7)
plt.title('Distribution of NDVI values', fontsize=20, fontweight='bold')
plt.xlabel('NDVI Value', fontsize=16, fontweight='bold')
plt.ylabel('Frequency', fontsize=16, fontweight='bold')
plt.grid(axis='y', alpha=0.75)

# Set x-axis limits to cover the NDVI range (-1 to 1)
plt.xlim(-1, 1)

# Increase fontsize for all tick labels
plt.tick_params(axis='both', which='major', labelsize=14)

plt.tight_layout()

# Save the histogram as an image
plt.savefig('C:/Users/user/Documents/GEEMAP Projects/NDVI/NDVI_Histogram1.png', dpi=300)

plt.show()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




