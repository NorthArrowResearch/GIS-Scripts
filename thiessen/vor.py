import numpy as np
from scipy.spatial.qhull import QhullError
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import voronoi_plot_2d
import matplotlib.pyplot as plt
from shapely.geometry import *
from shapely.ops import unary_union, linemerge

class NARVoronoi:
    """
    The purpose of this class is to load a shapefile and calculate the voronoi
    shapes from it.
    """

    def __init__(self, points):
        #  The centroid is what we're going to use to shift all the coords around
        self.points = points
        self.centroid = MultiPoint([x.point for x in points]).centroid.coords[0]

        # Give us a numpy array that is easy to work with then subtract the centroid
        # centering our object around the origin so that the QHull method works properly
        adjpoints = np.array(MultiPoint([x.point for x in points]))
        adjpoints = adjpoints - self.centroid

        try:
            self._vor = Voronoi(adjpoints)
        except QhullError as e:
            print "Something went wrong with QHull"
            print e
        except ValueError as e:
            print "Invalid array specified"
            print e

        # bake in region adjacency (I have no idea why it's not in by default)
        self.region_neighbour = []

        # Find which regions are next to which other regions
        for idx, reg in enumerate(self._vor.regions):
            adj = []
            for idy, reg2 in enumerate(self._vor.regions):
                # Adjacent if we have two matching vertices (neighbours share a wall)
                if idx != idy and len(set(reg) - (set(reg) - set(reg2))) >= 2:
                    adj.append(idy)
            self.region_neighbour.append(adj)

        # Transform everything back to where it was (with some minor floating point rounding problems)
        self.vertices = self._vor.vertices + self.centroid
        self.ridge_points = self._vor.ridge_points
        self.ridge_vertices = self._vor.ridge_vertices
        self.regions = self._vor.regions
        self.point_region = self._vor.point_region

    def collectCenterLines(self, flipIsland=None):
        """
        # HERE's WHAT WE HAVE:  .
        # vertices	(ndarray of double, shape (nvertices, ndim)) Coordinates of the Voronoi vertices.

        # ridge_points	(ndarray of ints, shape (nridges, 2)) Indices of the points between which each Voronoi ridge lies.
        # ridge_vertices	(list of list of ints, shape (nridges, *)) Indices of the Voronoi vertices forming each Voronoi ridge.
        # regions	(list of list of ints, shape (nregions, *)) Indices of the Voronoi vertices forming each Voronoi region. -1 indicates vertex outside the Voronoi diagram.

        # point_region	(list of ints, shape (npoints)) Index of the Voronoi region for each input point. If qhull option "Qc" was not specified, the list will contain -1 for points that are not associated with a Voronoi region.
        :param leftpts:
        :param rightpts:
        :return:
        """

        regions = []
        for idx, reg in enumerate(self.region_neighbour):
            # obj will have everything we need to know.
            obj = {
                "id": idx,
                "side": 1,
                "adjacents": reg
            }
            lookupregion = np.where(self._vor.point_region == idx)
            if len(lookupregion[0]) > 0:
                ptidx = lookupregion[0][0]
                point = self.points[int(ptidx)]
                if flipIsland is not None and point.island == flipIsland:
                    obj["side"] = point.side * -1
                else:
                    obj["side"] = point.side
            regions.append(obj)

        centerlines = []
        # loop over ridge_vertices. idx = ridge
        for region in regions:
            for nidx in region['adjacents']:
                neighbour = regions[nidx]
                if neighbour['side'] != region['side']:
                    # Get the two shared points these two regions should have
                    sharedpts = set(self.regions[region['id']]) - (set(self.regions[region['id']]) - set(self.regions[nidx]))
                    # Add this point to the list if it is unique
                    if -1 not in sharedpts:
                        lineseg = []
                        for e in sharedpts:
                            lineseg.append(self.vertices[e])
                        if len(lineseg) == 2:
                            centerlines.append(LineString(lineseg))


        return linemerge(unary_union(centerlines))

    def plot(self):

        voronoi_plot_2d(self._vor)
        plt.show()

    def createshapes(self):
        polys = []
        for region in self.regions:
            if len(region) >= 3:
                polys.append(Polygon([self.vertices[ptidx] for ptidx in region if ptidx >=0]))
        self.polys = MultiPolygon(polys)


# def connectTheDots(multiline):
#     """
#     Take a series of adjacent line segments and return a single line
#     :param multiline:
#     :return:
#     """
#     line = []
#     fwd = True
#     lstmulti = list(multiline)
#     firstline = lstmulti[0]
#     lstmulti.remove(firstline)
#
#     # Pick a line, Any line, to start with
#     for point in firstline.coords:
#         nextpt = point
#         while nextpt is not None:
#             nextpt = findNext(nextpt, lstmulti)
#             if nextpt is not None:
#                 line.append(nextpt) if fwd else line.insert(0, nextpt)
#         fwd = not fwd
#
#     return LineString(line)
#
# def findNext(point, lstLine):
#     """
#     Simple function for returning the next point in a disjointed series of 2-point lines
#     :param point:
#     :param lstLine:
#     :return:
#     """
#     for idx, line in enumerate(lstLine):
#         if line.coords[0] == point:
#             lstLine.remove(line)
#             return line.coords[1]
#         elif line.coords[1] == point:
#             lstLine.remove(line)
#             return line.coords[0]
#     return None

