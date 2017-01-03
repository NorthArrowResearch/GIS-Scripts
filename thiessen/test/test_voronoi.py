from osgeo import gdal, ogr, osr
import numpy as np
from scipy.spatial.qhull import QhullError
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import voronoi_plot_2d
import matplotlib.pyplot as plt

class NARVoronoi:
    """
    The purpose of this class is to load a shapefile and calculate the voronoi
    shapes from it.
    """

    def __init__(self, filename):
        self._vor = None
        driver = ogr.GetDriverByName('ESRI Shapefile')
        dataSource = driver.Open(filename, 0)  # 0 means read-only. 1 means writeable.

        print 'Opened %s' % (filename)
        layer = dataSource.GetLayer()

        # Get our multipolygon shape
        feat = layer.GetFeature(0)
        geom = feat.GetGeometryRef()

        # Add all the points (including islands) to the list
        points = []
        # for idx in range(0, geom.GetGeometryCount()):
        for idx in range(0, geom.GetGeometryCount()):
            ring = geom.GetGeometryRef(idx)
            for pt in ring.GetPoints():
                points.append(pt)

        # Find the min and max (voronoi doesn't play nice at large shifts)
        self.minx = min([x[0] for x in points])
        self.miny = min([x[1] for x in points])


        # Give us a numpy array that is easy to work with
        adjpoints = np.array(points[:100])
        adjpoints[:, 0] -= self.minx
        adjpoints[:, 1] -= self.miny

        try:
            self._vor = Voronoi(adjpoints)
        except QhullError as e:
            print "Something went wrong with QHull"
            print e
        except ValueError as e:
            print "Invalid array specified"
            print e


    def plot(self):
        voronoi_plot_2d(self._vor)
        plt.show()


vor = NARVoronoi("../sample/WettedExtent.shp")
vor.plot()
print "done"