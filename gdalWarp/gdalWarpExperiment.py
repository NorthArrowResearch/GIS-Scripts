import os
from subprocess import call
import gdal
import numpy as np
import subprocess
from os import path

gdal.UseExceptions()

class Raster:
    def __init__(self, filepath):
        gdal.UseExceptions()
        self.errs = ""
        self.filename = path.basename(filepath)
        try:
            src_ds = gdal.Open( filepath )
        except RuntimeError, e:
            print('Unable to open %s' % filepath)
            exit(1)
        try:
            # Read Raster Properties
            self.srcband = src_ds.GetRasterBand(1)
            self.bands = src_ds.RasterCount
            self.driver = src_ds.GetDriver().LongName
            self.gt = src_ds.GetGeoTransform()

            """ Turn a Raster with a single band into a 2D [x,y] = v array """
            self.array = self.srcband.ReadAsArray()
            # Now we need to return a transposed array so that we can operate on it in numpy
            # as if it was (cols/X, rows/Y)
            self.array = np.flipud(self.array).T

            self.dataType = self.srcband.DataType
            self.nodata = self.srcband.GetNoDataValue()

            if self.nodata is not None:
                self.array = np.ma.masked_array(self.array, np.isnan(self.array))
                self.array = np.ma.masked_equal(self.array, self.nodata)

            self.min = self.srcband.GetMinimum()
            self.max = self.srcband.GetMaximum()
            self.proj = src_ds.GetProjection()
            self.left = self.gt[0]
            self.cellWidth = self.gt[1]
            self.top = self.gt[3]
            self.cellHeight = self.gt[5]
            self.cols = src_ds.RasterXSize
            self.rows = src_ds.RasterYSize

        except RuntimeError as e:
            print('Could not retrieve meta Data for %s' % filepath)
            exit(1)

def printArrayRow(name, arr, row):
    theRow = ' '.join(map(str, arr[row]))
    print "{0}:: {1}".format(name, theRow)

"""

            EXPERIMENT BEGINS BELOW HERE

"""


def ClipRaster(gdalWarpPath, sInputRaster, sOutputRaster, sShapeFile, sWhereClause):

    assert os.path.isfile(gdalWarpPath), "Missing GDAL Warp executable at {0}".format(gdalWarpPath)
    assert os.path.isfile(sInputRaster), "Missing clipping operation input at {0}".format(sInputRaster)
    assert os.path.isfile(sShapeFile), "Missing clipping operation input ShapeFile at {0}".format(sShapeFile.FullPath)

    # Reset the where parameter to an empty string if no where clause is provided
    # TODO: This is giving us 64-bit rasters for some reason and a weird nodata value with nan as well. We're probably losing precision somewhere

    sWhereParameter = ""
    if len(sWhereClause) > 0:
        sWhereParameter = "-cwhere \"{0}\"".format(sWhereClause)

    gdalArgs = " -dstnodata -9999 -cutline {0} {1} {2} {3}".format(sShapeFile, sWhereParameter, sInputRaster, sOutputRaster)

    theReturn = call(gdalWarpPath + gdalArgs, stdout=subprocess.PIPE, shell=True)
    assert theReturn == 0, "Error clipping raster. Input raster {0}. Output raster {1}. ShapeFile {2}".format(sInputRaster, sOutputRaster, sShapeFile)



gdalPath =  "/usr/local/bin/gdalwarp"
sWhere = "(\"{0}\" ='{1}')  AND (\"{2}\"='{3}')".format("Site", "0003L", "Section", "channel")
shapefile = {}
shapefile = "shp/ComputationExtents.shp"


os.remove("outputs/0003L_20000318_dem_clipped.tif")
ClipRaster(gdalPath, "rasters/0003L_20000318_dem.tif", "outputs/0003L_20000318_dem_clipped.tif", shapefile, sWhere)

# Now load the original and clipped and let's make some comparisons:
channelrasterORIG = Raster("rasters/0003L_20000318_dem.tif")
channelraster = Raster("outputs/0003L_20000318_dem_clipped.tif")

print "rasters/0003L_20000318_dem.tif NODATA: {0} DATA Type: {1}".format(channelrasterORIG.nodata, channelrasterORIG.dataType)
print "outputs/0003L_20000318_dem_clipped.tif NODATA: {0} DATA Type: {1}".format(channelraster.nodata, channelraster.dataType)
printArrayRow("ORIG    ", channelrasterORIG.array, 243)
printArrayRow("CLIPPED ", channelraster.array, 243)



# ClipRaster(gdalPath, "rasters/0003L_min_surface.tif", "outputs/0003L_min_surface_clipped.tif", shapefile, sWhere)
# minrasterORIG = Raster("rasters/0003L_min_surface.tif")
# minraster = Raster("outputs/0003L_min_surface_clipped.tif")
#
#
# print "outputs/0003L_min_surface.tif NODATA: {0}".format(minraster.nodata)
# printArrayRow("minRaster ", minraster.array, 243)
print "thing"