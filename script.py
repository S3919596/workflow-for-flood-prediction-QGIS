import os
import processing


#path input and output
inputfilepath = 'D:/Master RMIT/Geo Programming/Final Project/Inputs/'
outputsfilepath = 'D:/Master RMIT/Geo Programming/Final Project/Outputs/'

#Outputs 
fillDEM_output= 'fillDEM.tif'
flowAcc = 'flowAccumulation.tif'
strahler ="strahler.tif"
strahler6 ="strahler6.tif"
bsChannels_layer = 'channels.shp'
flowDir_output = 'D8flowDirection.tif'
pourPointSnap = 'pourPointSnap.shp'
pourPointSnapXY = 'pourPointSnapXY.shp'
catchment = 'catchment.tif'
catchmentVect = 'catchmentVector.shp'
slopeDEM = 'slopeDEM.tif'
slopeAreaTerm = 'slopeAreaTerm.tif'
slpAreaClip = 'slopeAreaTermClip.tif'
statist= 'statist.txt'
velocityLayer= 'velocityLayer.tif'
weighted= 'weighted.tif'
flowDirClip= 'flowDirClip.tif'

#----add vector layer and raster layers
DEMlayer = iface.addRasterLayer(inputfilepath + "DEM_test.tif")
pourPoint = iface.addVectorLayer(inputfilepath + 'PourPoint.shp', "", "ogr")

#---- Fill sniks and Flow direction --------
fillParameters={"ELEV":DEMlayer,"FILLED":outputsfilepath + fillDEM_output ,"FDIR":outputsfilepath + flowDir_output ,"WSHED":QgsProcessing.TEMPORARY_OUTPUT ,"MINSLOPE": 0.01 }
processing.run("saga:fillsinkswangliu", fillParameters)
DEM_filled = iface.addRasterLayer(outputsfilepath + fillDEM_output)

#---- Flow accumulation -------
flowParam={ '-3' : False, '-m' : False, '-u' : False, 'GRASS_OUTPUT_TYPE_PARAMETER' : 0, 'GRASS_RASTER_FORMAT_META' : '', 'GRASS_RASTER_FORMAT_OPT' : '', 'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 'GRASS_REGION_PARAMETER' : None, 'GRASS_VECTOR_DSCO' : '', 'GRASS_VECTOR_EXPORT_NOCAT' : False, 'GRASS_VECTOR_LCO' : '', 'aspect' : None, 'barrier' : None, 'bound' : None, 'elevation' : DEM_filled,'flowaccumulation' : outputsfilepath + flowAcc, 'flowlength' : 'TEMPORARY_OUTPUT','flowline' : 'TEMPORARY_OUTPUT', 'skip' : None }
processing.run("grass7:r.flow", flowParam)
flowAcc = iface.addRasterLayer(outputsfilepath + flowAcc)


#---Strahler order 
strahlerParam={"DEM":DEM_filled, "STRAHLER":outputsfilepath + strahler}
processing.run("saga:strahlerorder", strahlerParam)
Strahler_order = iface.addRasterLayer(outputsfilepath + strahler)


#---- Raster calculator  (Streams >5 )
calcParam={'BAND_A' : 1, 'BAND_B' : None, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,\
'BAND_F' : None, 'EXTRA' : '', 'FORMULA' : 'A > 5', 'INPUT_A' : Strahler_order, 'INPUT_B' : None,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : '',\
'OUTPUT' : outputsfilepath + strahler6, 'RTYPE' : 5}
processing.run('gdal:rastercalculator', calcParam)
strahlerOrder8 = iface.addRasterLayer(outputsfilepath + strahler6)


#---- Channel Network (extraccion de streams) -------
channelsParam={"DEM":DEM_filled, "THRESHOLD":8,"SEGMENTS":outputsfilepath + bsChannels_layer,\
"DIRECTION":outputsfilepath + flowDir_output,"CONNECTION":QgsProcessing.TEMPORARY_OUTPUT,\
"ORDER":QgsProcessing.TEMPORARY_OUTPUT, "BASINS":QgsProcessing.TEMPORARY_OUTPUT,\
"BASIN":QgsProcessing.TEMPORARY_OUTPUT, "NODES":QgsProcessing.TEMPORARY_OUTPUT}
processing.run("saga:channelnetworkanddrainagebasins", channelsParam)
channelLayer = iface.addVectorLayer(outputsfilepath + bsChannels_layer, "", "ogr")
flwDir= iface.addRasterLayer(outputsfilepath + flowDir_output)

#---- Snap pour point to channels ----
snapParm={'BEHAVIOR':0, 'INPUT':pourPoint, 'REFERENCE_LAYER':channelLayer, 'TOLERANCE':100, 'OUTPUT':outputsfilepath + pourPointSnap}
processing.run('native:snapgeometries',snapParm)
pourPointSnap= iface.addVectorLayer(outputsfilepath + pourPointSnap, "", "ogr")

#---- Add xy coordiante pour point snaped----
xyParam={'INPUT':pourPointSnap, 'CRS':QgsCoordinateReferenceSystem('Australian_Lambert_Conformal_Conic'), 'PREFIX':'', 'OUTPUT':outputsfilepath + pourPointSnapXY }
processing.run('native:addxyfields',xyParam)
pourPointSnapXY= iface.addVectorLayer(outputsfilepath + pourPointSnapXY, "", "ogr")

#--- Extract XY from pourPointSnapXY
layer = pourPointSnapXY
for f in layer.getFeatures():
    x=f['x']
    y=f['y']

#----- Upslope Area ----
upslopeParam={'TARGET':None, 'TARGET_PT_X':x, 'TARGET_PT_Y':y, 'ELEVATION':DEM_filled, 'SINKROUTE':None,'AREA': outputsfilepath + catchment, 'METHOD':0, 'CONVERGE':1.1}
processing.run('saga:upslopearea',upslopeParam)
cathment= iface.addRasterLayer(outputsfilepath + catchment)

#---- Poligonize catchment
vectParam={ 'BAND' : 1, 'EIGHT_CONNECTEDNESS' : False, 'EXTRA' : '', 'FIELD' : 'DN', 'INPUT' : cathment , 'OUTPUT' : outputsfilepath + catchmentVect }
processing.run('gdal:polygonize',vectParam)
catchmentVect=iface.addVectorLayer(outputsfilepath + catchmentVect, "", "ogr")

#---- Slope from DEMfill
slopeParam={ 'INPUT' : DEM_filled, 'OUTPUT' : outputsfilepath + slopeDEM, 'Z_FACTOR' : 1 }
processing.run('native:slope',slopeParam)
slope= iface.addRasterLayer(outputsfilepath + slopeDEM)

#---- Raster calculator slope-area term ----
calcParam2={'BAND_A' : 1, 'BAND_B' : 1, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,\
'BAND_F' : None, 'EXTRA' : '', 'FORMULA' : '  sqrt ( "slopeDEM@1")* sqrt ( "flowAccumulation@1")', 'INPUT_A' : slope, 'INPUT_B' : flowAcc,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : '',\
'OUTPUT' : outputsfilepath + slopeAreaTerm , 'RTYPE' : 5}
processing.run('gdal:rastercalculator', calcParam2)
slopeAreaTerm = iface.addRasterLayer(outputsfilepath + slopeAreaTerm)

#------Clip slopeAreaTerm -----
clipParam={ 'ALPHA_BAND' : False, 'CROP_TO_CUTLINE' : True, 'DATA_TYPE' : 0, 'EXTRA' : '','INPUT' : slopeAreaTerm,\
'KEEP_RESOLUTION' : False,'MASK' : catchmentVect, 'MULTITHREADING' : False,'NODATA' : None, 'OPTIONS' : '',\
'OUTPUT':outputsfilepath + slpAreaClip , 'SET_RESOLUTION' : False, 'SOURCE_CRS' : None,'TARGET_CRS' : None,\
'TARGET_EXTENT' : None, 'X_RESOLUTION' : -999999999, 'Y_RESOLUTION' : None }
processing.run('gdal:cliprasterbymasklayer', clipParam)
slpAreaClip = iface.addRasterLayer(outputsfilepath + slpAreaClip)

#---- Extract mean by Clip slopeAreaTerm---
statisParam={ 'BAND' : 1, 'INPUT' : slpAreaClip,'OUTPUT_HTML_FILE' : outputsfilepath + statist }
processing.run('native:rasterlayerstatistics', statisParam)



#------ Raster Calculator - Calculate velocity ----
calcParam3={'BAND_A' : 1, 'BAND_B' : None, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,'BAND_F' : None,\
'EXTRA' : '', 'FORMULA' : ' (A / 4.220523025569131)*0.1 ', 'INPUT_A' : slpAreaClip, 'INPUT_B' : None,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : ''\
,'OUTPUT' : outputsfilepath + velocityLayer,'RTYPE' : 5}
processing.run('gdal:rastercalculator', calcParam3)
velocityLayer=iface.addRasterLayer(outputsfilepath + velocityLayer)



#------ Raster Calculator - weight grid ----
calcParam4={'BAND_A' : 1, 'BAND_B' : None, 'BAND_C' : None, 'BAND_D' : None, 'BAND_E' : None,'BAND_F' : None,\
'EXTRA' : '', 'FORMULA' : ' 1/A', 'INPUT_A' : velocityLayer, 'INPUT_B' : None,\
'INPUT_C' : None, 'INPUT_D' : None, 'INPUT_E' : None, 'INPUT_F' : None, 'NO_DATA' : None, 'OPTIONS' : ''\
,'OUTPUT' : outputsfilepath + weighted,'RTYPE' : 5}
processing.run('gdal:rastercalculator', calcParam4)
velocityLayer=iface.addRasterLayer(outputsfilepath + weighted)


#------Clip Flow Direction -----
clipParam2={ 'ALPHA_BAND' : False, 'CROP_TO_CUTLINE' : True, 'DATA_TYPE' : 0, 'EXTRA' : '','INPUT' : flwDir,'KEEP_RESOLUTION' : False,'MASK' : catchmentVect, 'MULTITHREADING' : False,'NODATA' : None, 'OPTIONS' : '','OUTPUT':outputsfilepath + flowDirClip , 'SET_RESOLUTION' : False, 'SOURCE_CRS' : None,'TARGET_CRS' : None,'TARGET_EXTENT' : None, 'X_RESOLUTION' : -999999999, 'Y_RESOLUTION' : None }
processing.run('gdal:cliprasterbymasklayer', clipParam2)
flwDirClip = iface.addRasterLayer(outputsfilepath + flowDirClip)

