import numpy as np
from scipy.spatial.qhull import QhullError
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

class NARVoronoi:
    """
    The purpose of this class is to load a shapefile and calculate the voronoi
    shapes from it.
    """

    def __init__(self, points):
        self._vor = None

        # Find the min and max (voronoi doesn't play nice at large shifts)
        self.minx = min([x[0] for x in points])
        self.miny = min([x[1] for x in points])

        # Give us a numpy array that is easy to work with
        adjpoints = np.array(points)
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