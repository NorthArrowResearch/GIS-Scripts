import numpy as np
import gdal
import matplotlib.pyplot as plt

"""

    Tutorial 1: We're going to open a raster, add 10 to every value and then write a new one

"""

filename = "inputs/DEM.tif"

src_ds = gdal.Open( filename )
srcband = src_ds.GetRasterBand(1)
bands = src_ds.RasterCount
driver = src_ds.GetDriver().LongName
gt = src_ds.GetGeoTransform()
nodata = srcband.GetNoDataValue()

""" Turn a Raster with a single band into a 2D [x,y] = v array """
array = srcband.ReadAsArray()

# Now mask out any NAN or nodata values (we do both for consistency)
if nodata is not None:
    array = np.ma.array(array, mask=(np.isnan(array) | (np.isclose(array, nodata))))

dataType = srcband.DataType
min = np.nanmin(array)
max = np.nanmax(array)
proj = src_ds.GetProjection()

# Add 4 to every value
result = array + 4.0

im = plt.imshow(result, cmap='hot')
plt.colorbar(im, orientation='vertical')
plt.show()

print "Done..."


