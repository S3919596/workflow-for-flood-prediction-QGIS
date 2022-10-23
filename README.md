# Script to watershed delineation and raster generation needed to predict floods using pyQGIS

## Factors to consider before using the code 
QGIS 3.0 or higher versions: The latest versions of QGIS use new dependencies for SAGA. This causes an error in the tool SAGA - Terrain Analysis - Hydrology - Slope Area. To run the scrip correctly it is necessary to perform the steps described in the following link, otherwise the tool will not work.
  - Upslope area shows an error stating tool needs graphical user interface: https://gis.stackexchange.com/questions/407307/upslope-area-shows-an-error-stating-tool-needs-graphical-user-interface
  - Work around for using SAGA Upslope Area tool in QGIS with new dependencies: https://gis.stackexchange.com/questions/407307/upslope-area-shows-an-error-stating-tool-needs-graphical-user-interface
  
  ## Example usage
  
  Example data used in this tutorial:
  
  Location: Melbourne 
  - Digital Elevation Model:  [DEM_test](https://github.com/S3919596/workflow-for-flood-prediction-QGIS/blob/master/Inputs.zip)
  - Pour point: [PourPoint](https://github.com/S3919596/workflow-for-flood-prediction-QGIS/blob/master/Inputs.zip)
  
## Code
### Add vector layer and raster layers
  
  ```python
# Load Layer
# ----------------------------
DEMlayer = iface.addRasterLayer(inputfilepath + "DEM_test.tif")

pourPoint = iface.addVectorLayer(inputfilepath + 'PourPoint.shp', "", "ogr")
```

### Fill sniks 
  ```python

#Parameters
fillParameters={"ELEV":DEMlayer,"FILLED":outputsfilepath + 'fillDEM.tif' ,"FDIR":'TEMPORARY_OUTPUT' ,\
"WSHED":QgsProcessing.TEMPORARY_OUTPUT ,"MINSLOPE": 0.01 }

# Fill pits in DEM
processing.run("saga:fillsinkswangliu", fillParameters)

# Load layer 
DEM_filled = iface.addRasterLayer(outputsfilepath + 'fillDEM.tif')
```

### Compute flow accumulation
  ```python
 
 #Parameters
flowParam={ '-3' : False, '-m' : False, '-u' : False, 'GRASS_OUTPUT_TYPE_PARAMETER' : 0, 'GRASS_RASTER_FORMAT_META' : '',\
'GRASS_RASTER_FORMAT_OPT' : '', 'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 'GRASS_REGION_PARAMETER' : None, 'GRASS_VECTOR_DSCO' : '',\
'GRASS_VECTOR_EXPORT_NOCAT' : False, 'GRASS_VECTOR_LCO' : '', 'aspect' : None, 'barrier' : None, 'bound' : None, 'elevation' : DEM_filled,\
'flowaccumulation' : outputsfilepath + 'flowAcc.tif', 'flowlength' : 'TEMPORARY_OUTPUT','flowline' : 'TEMPORARY_OUTPUT', 'skip' : None }

# Compute flow accumulation
processing.run("grass7:r.flow", flowParam)

# Load layer
flowAcc = iface.addRasterLayer(outputsfilepath + 'flowAcc.tif')
```

### Calculate the Strahler stream order on basis of filled DEM
```python
 
 #Parameters
strahlerParam={"DEM":DEM_filled, "STRAHLER":outputsfilepath + 'strahler.shp'}

# Compute flow accumulation
processing.run("saga:strahlerorder", strahlerParam)

# Load layer
strahler_order = iface.addRasterLayer(outputsfilepath + 'strahler.shp')
```


### Extract the main Strahler streams
```python
 
 #Parameters (stream order >5)
calcParam={'BAND_A' : 1, 'BAND_B' : None, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,\
'BAND_F' : None, 'EXTRA' : '', 'FORMULA' : 'A > 5', 'INPUT_A' : Strahler_order, 'INPUT_B' : None,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : '',\
'OUTPUT' : outputsfilepath + 'strahler6.tif', 'RTYPE' : 5}

# Compute Strahler stream order >5 using raster calculator
processing.run('gdal:rastercalculator', calcParam)

# Load layer
strahlerOrder8 = iface.addRasterLayer(outputsfilepath + 'strahler6.tif')
```

### Extract Channel Network and Flow Direction
```python
 
 #Parameters
channelsParam={"DEM":DEM_filled, "THRESHOLD":8,"SEGMENTS":outputsfilepath + 'bsChannels.shp',\
"DIRECTION":outputsfilepath + 'flowDir.tif',"CONNECTION":QgsProcessing.TEMPORARY_OUTPUT,\
"ORDER":QgsProcessing.TEMPORARY_OUTPUT, "BASINS":QgsProcessing.TEMPORARY_OUTPUT,\
"BASIN":QgsProcessing.TEMPORARY_OUTPUT, "NODES":QgsProcessing.TEMPORARY_OUTPUT}

#Extract Channel Network
processing.run("saga:channelnetworkanddrainagebasins", channelsParam)

# Load layers
channelLayer = iface.addVectorLayer(outputsfilepath + 'bsChannels.shp', "", "ogr")
flwDir= iface.addRasterLayer(outputsfilepath + 'flowDir.tif')
```

### Snap Pour Point to channel network and add new xy coordiante
```python
 
 #Parameters
 snapParm={'BEHAVIOR':0, 'INPUT':pourPoint, 'REFERENCE_LAYER':channelLayer, 'TOLERANCE':100,\
 'OUTPUT':outputsfilepath + 'pourPointSnap.shp'}
 
 #Snap Pour Point to channel network
 processing.run('native:snapgeometries',snapParm)
 
 # Load layer
 pourPointSnap= iface.addVectorLayer(outputsfilepath + 'pourPointSnap.shp', "", "ogr")
 
 #Add xy coordiante to snap pour point 
 #Parameters
 xyParam={'INPUT':pourPointSnap, 'CRS':QgsCoordinateReferenceSystem('Australian_Lambert_Conformal_Conic'),\
 'PREFIX':'', 'OUTPUT':outputsfilepath + 'pourPointSnapXY.shp' }

# ---------------------
 #Add xy coordiante to snap pour point as fields
 processing.run('native:addxyfields',xyParam)

# Extract coordinates in list  
layer = outputsfilepath + 'pourPointSnapXY.shp'
for f in layer.getFeatures():
    x=f['x']
    y=f['y']
  ```
  
### Delineate catchment from filled DEM and XY pour point
```python
 
#Parameters
upslopeParam={'TARGET':None, 'TARGET_PT_X':x, 'TARGET_PT_Y':y, 'ELEVATION':DEM_filled, 'SINKROUTE':None,\
'AREA': outputsfilepath + 'catchment.tif', 'METHOD':0, 'CONVERGE':1.1}
 
#Delineate catchment
processing.run('saga:upslopearea',upslopeParam)
 
#Load layer
cathment= iface.addRasterLayer(outputsfilepath + 'catchment.tif')
 
# ---------------------
#Polygonization of the catchment
 
#Parameters
vectParam={ 'BAND' : 1, 'EIGHT_CONNECTEDNESS' : False, 'EXTRA' : '', 'FIELD' : 'DN', 'INPUT' : cathment ,
'OUTPUT' : outputsfilepath + 'catchmentVect.shp' }

#Polygonization of the catchment 
processing.run('gdal:polygonize',vectParam)

#Load layer
catchmentVect=iface.addVectorLayer(outputsfilepath + 'catchmentVect.shp', "", "ogr")
 ```
 
### Create the velocity field
In this section it will be determine the time it takes water to flow somewhere to better predict when flooding will occur during a hypothetical rainfall event. 
```python
# ---------------------
# Calcurate slope from filled DEM

#Parameters
slopeParam={ 'INPUT' : DEM_filled, 'OUTPUT' : outputsfilepath + 'slopeDEM.tif', 'Z_FACTOR' : 1 }

# Calculate slope
processing.run('native:slope',slopeParam)

# ---------------------
#The slope-area term. This new raster combines slope and flow accumulation area using raster calculator

#Parameters
calcParam2={'BAND_A' : 1, 'BAND_B' : 1, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,\
'BAND_F' : None, 'EXTRA' : '', 'FORMULA' : '  sqrt ( "slopeDEM@1")* sqrt ( "flowAccumulation@1")', \
'INPUT_A' : outputsfilepath + 'slopeDEM.tif', 'INPUT_B' : outputsfilepath + 'flowAcc.tif','INPUT_C' : None,\
'INPUT_D' : None,'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : '',\
'OUTPUT' : outputsfilepath + 'slopeAreaTerm.tif' , 'RTYPE' : 5}

# The slope-area term
processing.run('gdal:rastercalculator', calcParam2)

# ---------------------
# Clip slope-area term using the watershed polygon 

#Parameters
clipParam={ 'ALPHA_BAND' : False, 'CROP_TO_CUTLINE' : True, 'DATA_TYPE' : 0, 'EXTRA' : '','INPUT' : outputsfilepath + 'slopeAreaTerm.tif',\
'KEEP_RESOLUTION' : False,'MASK' : catchmentVect, 'MULTITHREADING' : False,'NODATA' : None, 'OPTIONS' : '',\
'OUTPUT':outputsfilepath + 'slpAreaClip.tif' , 'SET_RESOLUTION' : False, 'SOURCE_CRS' : None,'TARGET_CRS' : None,\
'TARGET_EXTENT' : None, 'X_RESOLUTION' : -999999999, 'Y_RESOLUTION' : None }

#Clip by mask 
processing.run('gdal:cliprasterbymasklayer', clipParam)

#Load layer
slpAreaClip = iface.addRasterLayer(outputsfilepath + slpAreaClip)

# ---------------------
#Calculate mean by clip slope-area term

#Parameters
statisParam={ 'BAND' : 1, 'INPUT' : slpAreaClip,'OUTPUT_HTML_FILE' : outputsfilepath + 'statist.txt' }

# Calculate statistics 
processing.run('native:rasterlayerstatistics', statisParam)


# ---------------------
#Calculate velocity field using raster calculator

#Parameters
calcParam3={'BAND_A' : 1, 'BAND_B' : None, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,'BAND_F' : None,\
'EXTRA' : '', 'FORMULA' : ' (A / 4.220523025569131)*0.1 ', 'INPUT_A' : slpAreaClip, 'INPUT_B' : None,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : ''\
,'OUTPUT' : outputsfilepath + 'velocity.tif','RTYPE' : 5}

#Calculate velocity
processing.run('gdal:rastercalculator', calcParam3)

#Load layer (In this layer, darker colors represent a slower velocity, while lighter colors represent a faster velocity)
velocityLayer=iface.addRasterLayer(outputsfilepath + 'velocity.tif')
```

### Create a weight grid
To determine flow length, you need two variables: flow direction (which you know) and weight (which you don't). Weight, in regard to flow, represents impedance

```python
#Weight grid
#Parameters
calcParam4={'BAND_A' : 1, 'BAND_B' : None, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,'BAND_F' : None,\
'EXTRA' : '', 'FORMULA' : ' 1/A', 'INPUT_A' : outputsfilepath + 'velocity.tif', 'INPUT_B' : None,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : ''\
,'OUTPUT' : outputsfilepath + 'weighted.tif','RTYPE' : 5}

#Weight grid using raster calculator
processing.run('gdal:rastercalculator', calcParam4)

#Load layer
velocityLayer=iface.addRasterLayer(outputsfilepath + 'weighted.tif')


# ---------------------
#Clip Flow Direction

#Parameters
clipParam2={ 'ALPHA_BAND' : False, 'CROP_TO_CUTLINE' : True, 'DATA_TYPE' : 0, 'EXTRA' : '','INPUT' : outputsfilepath + 'flowDir.tif',\
'KEEP_RESOLUTION' : False,'MASK' : catchmentVect, 'MULTITHREADING' : False,'NODATA' : None, 'OPTIONS' : '','OUTPUT':outputsfilepath + 'flowDirClip.tif', \
'SET_RESOLUTION' : False, 'SOURCE_CRS' : None,'TARGET_CRS' : None,'TARGET_EXTENT' : None, 'X_RESOLUTION' : -999999999, 'Y_RESOLUTION' : None }

#Clip by mask 
processing.run('gdal:cliprasterbymasklayer', clipParam2)

#Load layer
flwDirClip = iface.addRasterLayer(outputsfilepath + 'flowDirClip.tif')
```

Finally have all the layers you need to determine flow time. Using weight and flow direction layers it is possible to determine the flow time of each of the cells that make up the basin. For them, it is necessary to use a tool that uses the previous layers and generates a raster that represents the time in seconds that the water takes to flow towards the cell outlet.
Currently QGIS does not have such a tool and the complexity of the calculation was not possible to develop using the raster calculator. Alternatively, it is still possible to use ArcGIS software and the Flow Length tool which will give the result as a function of time.
