#!/usr/bin/env python

# http://sciience.tumblr.com/post/101026151217/quick-python-script-for-making-voronoi-polygons

from osgeo import gdal, ogr, osr

from os import path
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
from scipy.spatial.qhull import QhullError
import numpy as np
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

class pt:

    def __init__(self, pt):
        self.pt = pt
        self.angle = 0
        print "hello"


def getShapes(shpFile):
    """

    :param shpFile:
    :return:
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(shpFile, 0) # 0 means read-only. 1 means writeable.


    # Check to see if shapefile is found.
    if dataSource is None:
        print 'Could not open %s' % (shpFile)
        return

    print 'Opened %s' % (shpFile)
    layer = dataSource.GetLayer()

    # Get our multipolygon shape
    feat = layer.GetFeature(0)
    geom = feat.GetGeometryRef()

    # Add all the points (including islands) to the list
    points = []
    for idx in range(geom.GetGeometryCount()):
        ring = geom.GetGeometryRef(idx)
        for pt in ring.GetPoints():
            points.append(pt)

    # Give us a numpy array that is easy to work with
    adjpoints = np.array(points)

    # Find the min and max (voronoi doesn't play nice at large shifts)
    minx = min([x[0] for x in points])
    miny = min([x[1] for x in points])

    adjpoints = np.array(points)
    adjpoints[:, 0] -= minx
    adjpoints[:, 1] -= miny

    try:
        vor = Voronoi(adjpoints)
    except QhullError as e:
        print "Something went wrong with QHull"
        print e
    except ValueError as e:
        print "Invalid array specified"
        print e

    voronoi_plot_2d(vor)

    plt.show()
    return


def ptInShape(point, polygon):
    """
    This is kind of rough but it's the right idea
    :param point:
    :param polygon:
    :return:
    """
    spatialReference = osr.SpatialReference()
    spatialReference.SetWellKnownGeogCS("WGS84")
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.AssignSpatialReference()
    return pt.Within(polygon)

def main():
    '''

    :return:
    '''
    # We're just iterating over a folder. Change this to something else if you want
    getShapes("sample/WettedExtent.shp")
    print "done"

if __name__ == "__main__":
    main()