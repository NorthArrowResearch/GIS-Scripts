#!/usr/bin/env python

from osgeo import gdal, ogr
import numpy as np
from scipy import interpolate
from os import path, listdir
import sys
# this allows GDAL to throw Python Exceptions
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
            self.dataType = self.srcband.DataType
            self.band_array = self.srcband.ReadAsArray()
            self.nodata = self.srcband.GetNoDataValue()
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

def array2raster(array, top, left, cellheight, outputRaster,tempPath,DataType):
    '''
        This is just a helper method that takes an band_array and some parameters and
        writes it to a file
    '''
    templateRaster = Raster(tempPath)

    # reversed_arr = array[::-1] # reverse array so the tif looks like the array
    cols = array.shape[0]
    rows = array.shape[1]

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(path.join('rasters', outputRaster), cols, rows, 1, DataType, [ 'COMPRESS=LZW' ])

    outRaster.SetGeoTransform((left, cellheight, 0, top, 0, cellheight))
    outband = outRaster.GetRasterBand(1)

    # we swap axes for some reason
    outband.WriteArray(np.swapaxes(array,0,1))
    if templateRaster.nodata:
        outband.SetNoDataValue(templateRaster.nodata)
    else:
        outband.SetNoDataValue(-9999)
    outRaster.SetProjection(templateRaster.proj)
    outband.FlushCache()


def bilinear_interpolation(x, y, points):
    '''Interpolate (x,y) from values associated with four points.

    The four points are a list of four triplets:  (x, y, value).
    The four points can be in any order.  They should form a rectangle.
    '''
    # See formula at:  http://en.wikipedia.org/wiki/Bilinear_interpolation
    (x1, y1, q11), (_x1, y2, q12), (x2, _y1, q21), (_x2, _y2, q22) = points

    if x1 != _x1 or x2 != _x2 or y1 != _y1 or y2 != _y2:
        raise ValueError('points do not form a rectangle')
    if not x1 <= x <= x2 or not y1 <= y <= y2:
        raise ValueError('(x, y) not within the rectangle')

    return (q11 * (x2 - x) * (y2 - y) +
            q21 * (x - x1) * (y2 - y) +
            q12 * (x2 - x) * (y - y1) +
            q22 * (x - x1) * (y - y1)
           ) / ((x2 - x1) * (y2 - y1) + 0.0)


def NoDataMask(oldGrid, newShape):
    '''
    :param oldGrid: A 2D array. This must be a regularly spaced grid (like a raster band array)
    :param newShape: the new shape you want in tuple format eg: (200,300)
    :return: newArr: The resampled array.
    '''
    newArr = np.nan * np.empty(newShape)
    oldCols, oldRows = oldGrid.shape
    newCols, newRows = newShape
    xMult = float(newCols)/oldCols # 4 in our test case
    yMult = float(newRows)/oldRows

    for (x, y), element in np.ndenumerate(newArr):
        # do a transform to figure out where we are ont he old matrix
        fx = x / xMult
        fy = y / yMult

        ix1 = int(np.floor(fx))
        iy1 = int(np.floor(fy))

        # Special case where point is on upper bounds
        if fx == float(newCols - 1):
            ix1 -= 1
        if fy == float(newRows - 1):
            iy1 -= 1

        ix2 = ix1 + 1
        iy2 = iy1 + 1

        # Test if we're within the raster midpoints
        if (ix1 >= 0) and (iy1 >= 0) and (ix2 < oldCols) and (iy2 < oldRows):
            # get the 4 values we need
            vals = [ oldGrid[ix1,iy1], oldGrid[ix1,iy2], oldGrid[ix2,iy1], oldGrid[ix2,iy2] ]

            # Here's where the actual interpolation is but make sure
            # there aren't any nan values.
            if not np.any([np.isnan(v) for v in vals]):
                newArr[x,y] = 1

    return newArr

def bilinear(oldGrid, newShape):
    '''
    :param oldGrid: A 2D array. This must be a regularly spaced grid (like a raster band array)
    :param newShape: the new shape you want in tuple format eg: (200,300)
    :return: newArr: The resampled array.
    '''
    newArr = np.nan * np.empty(newShape)
    oldCols, oldRows = oldGrid.shape
    newCols, newRows = newShape
    xMult = float(newCols)/oldCols # 4 in our test case
    yMult = float(newRows)/oldRows

    for (x, y), element in np.ndenumerate(newArr):
        # do a transform to figure out where we are ont he old matrix
        fx = x / xMult
        fy = y / yMult

        ix1 = int(np.floor(fx))
        iy1 = int(np.floor(fy))

        # Special case where point is on upper bounds
        if fx == float(newCols - 1):
            ix1 -= 1
        if fy == float(newRows - 1):
            iy1 -= 1

        ix2 = ix1 + 1
        iy2 = iy1 + 1

        # Test if we're within the raster midpoints
        if (ix1 >= 0) and (iy1 >= 0) and (ix2 < oldCols) and (iy2 < oldRows):
            # get the 4 values we need
            vals = [ oldGrid[ix1,iy1], oldGrid[ix1,iy2], oldGrid[ix2,iy1], oldGrid[ix2,iy2] ]

            # Here's where the actual interpolation is but make sure
            # there aren't any nan values.
            if not np.any([np.isnan(v) for v in vals]):
                newArr[x,y] = (vals[0] * (ix2 - fx) * (iy2 - fy) +
                               vals[1] * (fx - ix1) * (iy2 - fy) +
                               vals[2] * (ix2 - fx) * (fy - iy1) +
                               vals[3] * (fx - ix1) * (fy - iy1)
                            ) / ((ix2 - ix1) * (iy2 - iy1) + 0.0)

    return newArr


def fileToGrid(name):
    fileArr = np.loadtxt(open(name,"rb"),delimiter=" ")
    cellSize = 1.0
    padding = 10.0

    # Get the extents (plus some padding):
    XMax = np.amax(fileArr[:,1]) + padding
    YMax = np.amax(fileArr[:,2]) + padding

    XMin = np.amin(fileArr[:,1]) - padding
    YMin = np.amin(fileArr[:,2]) - padding

    rows = int((YMax-YMin) / cellSize)
    cols = int((XMax-XMin) / cellSize)
    top = (YMin - (cellSize /2))
    left = (XMin - (cellSize /2))

    # Set up an empty array with the right size
    z_array = np.nan * np.empty((cols, rows))
    # If there is a :, python will pass a slice:
    X = (fileArr[:,1] - XMin).astype(int)
    Y = (fileArr[:,2] - YMin).astype(int)

    z_array[X, Y] = fileArr[:,3]

    # Output the 1m raster to prove we can do it
    basename = path.splitext(path.basename(name))[0]
    array2raster(z_array, top, left, cellSize, basename + "_1m.tif", "template.tif", gdal.GDT_Float64)

    '''
        nearest
            return the value at the data point closest to the point of interpolation.
            See NearestNDInterpolator for more details.
        linear
            tesselate the input point set to n-dimensional simplices, and interpolate
            linearly on each simplex. See LinearNDInterpolator for more details.
        cubic (2-D)
            return the value determined from a piecewise cubic, continuously differentiable (C1),
            and approximately curvature-minimizing polynomial surface. See CloughTocher2DInterpolator for more details.

        bilinear
            The Bilinear method here is one that I wrote based on the wikipedia article. It takes about
            100x longer than any other method
    '''

    newCellSize = 0.25

    # New shape is a tuple with the new rows and cols based on our new cellsize
    newShape = (int(cols/newCellSize), int(rows/newCellSize))

    # I wrote a special, speedier version of bilinear resample that just gives us a nodata Mask
    noData = NoDataMask(z_array, newShape)

    XaxisNew, YaxisNew = np.mgrid[0:cols:newCellSize, 0:rows:newCellSize]

    grid_nearest = noData * interpolate.griddata((X, Y), fileArr[:,3], (XaxisNew, YaxisNew), method='nearest')
    grid_linear = noData * interpolate.griddata((X, Y), fileArr[:,3], (XaxisNew, YaxisNew), method='linear')
    grid_cubic = noData * interpolate.griddata((X, Y), fileArr[:,3], (XaxisNew, YaxisNew), method='cubic')

    array2raster(grid_nearest, top, left, newCellSize, basename + "_025mNearest.tif", "template.tif", gdal.GDT_Float64)
    array2raster(grid_linear, top, left, newCellSize, basename + "_025mLinear.tif", "template.tif", gdal.GDT_Float64)
    array2raster(grid_cubic, top, left, newCellSize, basename + "_025mCubic.tif", "template.tif", gdal.GDT_Float64)

    # ====================================================================================
    # OK Now let's try bilinear resampling...
    # ====================================================================================



    # throw a grid and a new size at this function and it should resample it for you.
    z_arrayBil = bilinear(z_array, newShape)
    array2raster(z_arrayBil, top, left, newCellSize, basename + "_025mBilinear.tif", "template.tif", gdal.GDT_Float64)

    print "Finished: " + basename

def main():
    '''

    :return:
    '''
    # We're just iterating over a folder. Change this to something else if you want
    dirpath = '/Users/matt/Projects/nar/GrandCanyon/Sandbars/Topo_Data/corgrids/003Lcorgrids'

    for filename in listdir(dirpath):
        if filename.endswith(".txt") or filename.endswith(".TXT"):
            fullpath = path.join(dirpath, filename)
            fileToGrid(fullpath)
            continue
        else:
            continue
    print "done"

if __name__ == "__main__":
    main()