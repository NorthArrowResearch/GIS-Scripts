import numpy as np
from scipy.spatial.qhull import QhullError
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import voronoi_plot_2d
import matplotlib.pyplot as plt
import itertools

class NARVoronoi:
    """
    The purpose of this class is to load a shapefile and calculate the voronoi
    shapes from it.
    """

    def __init__(self, points):

        self.centroid = points.centroid.coords[0]

        # Give us a numpy array that is easy to work with
        adjpoints = np.array(points)
        adjpoints[:, 0] -= self.centroid[0]
        adjpoints[:, 1] -= self.centroid[1]

        try:
            self._vor = Voronoi(adjpoints)
        except QhullError as e:
            print "Something went wrong with QHull"
            print e
        except ValueError as e:
            print "Invalid array specified"
            print e

        # bake in region adjacency (I have no idea why it's not in by default)
        self.region_adjacency = []

        # Find which regions are next to which other regions
        for idx, reg in enumerate(self._vor.regions):
            adj = []
            for idy, reg2 in enumerate(self._vor.regions):
                # Adjacent if we have two matching vertices (neighbours share a wall)
                if idx != idy and len(set(reg) - (set(reg) - set(reg2))) >= 2:
                    adj.append(idy)
            self.region_adjacency.append(adj)

    def collectCenterLines(self, leftpts, rightpts):
        """
        # HERE's WHAT WE HAVE:
        # points	(ndarray of double, shape (npoints, ndim)) Coordinates of input points.
        # vertices	(ndarray of double, shape (nvertices, ndim)) Coordinates of the Voronoi vertices.

        # ridge_points	(ndarray of ints, shape (nridges, 2)) Indices of the points between which each Voronoi ridge lies.
        # ridge_vertices	(list of list of ints, shape (nridges, *)) Indices of the Voronoi vertices forming each Voronoi ridge.
        # regions	(list of list of ints, shape (nregions, *)) Indices of the Voronoi vertices forming each Voronoi region. -1 indicates vertex outside the Voronoi diagram.

        # point_region	(list of ints, shape (npoints)) Index of the Voronoi region for each input point. If qhull option "Qc" was not specified, the list will contain -1 for points that are not associated with a Voronoi region.
        :param leftpts:
        :param rightpts:
        :return:
        """
        # Go through and make points either left or right side:
        lArr = np.array(leftpts) - self.centroid
        rArr = np.array(rightpts) - self.centroid

        regions = []
        for idx, reg in enumerate(self.region_adjacency):
            # obj will have everything we need to know.
            obj = {
                "id": idx,
                "adjacents": reg
            }
            lookupregion = np.where(self._vor.point_region == idx)
            if len(lookupregion[0]) > 0:
                point = self._vor.points[lookupregion[0][0]]
                if point in lArr:
                    obj["side"] = -1
                elif point in rArr:
                    obj["side"] = 1

        centerlinePts = []

        # loop over ridge_vertices. idx = ridge


        print "heya"

    def plot(self):
        voronoi_plot_2d(self._vor)
        plt.show()
