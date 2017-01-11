# Utility functions we need
import unittest
import numpy as np

class TestRasterClass(unittest.TestCase):
    """
    Before we do anything we need to test the underlying core class
    There is only one method we wrote for this:
    """
    def test_getPixelVal(self):
        from raster import Raster
        self.assertTrue(False)

    def test_isClose(self):
        """
        Oh, also this little helper method:
        I didn't write it so we'd better test it well
        """
        from raster import isclose
        self.assertTrue(False)

class TestShapeHelpers(unittest.TestCase):

    def test_getBufferedBounds(self):
        from shapes import getBufferedBounds
        self.assertTrue(False)

    def test_getDiag(self):
        from shapes import getDiag
        self.assertTrue(False)

    def test_rectIntersect(self):
        from shapes import rectIntersect
        self.assertTrue(False)

    def test_getExtrapoledLine(self):
        from shapes import getExtrapoledLine
        self.assertTrue(False)

    def test_reconnectLine(self):
        from shapes import reconnectLine
        self.assertTrue(False)

    def test_splitClockwise(self):
        """
        This is the big one. Needs more careful testing than the rest
        :return:
        """
        from shapes import splitClockwise
        self.assertTrue(False)

class TestMetricClass(unittest.TestCase):

    def test_interpolateRasterAlongLine(self):
        from metrics import interpolateRasterAlongLine
        self.assertTrue(False)

    def test_dryWidth(self):
        from metrics import dryWidth
        self.assertTrue(False)

    def test_meanDepth(self):
        from metrics import meanDepth

        depthValues = [1, 2, 3, 4, 5]

        fValue = meanDepth(depthValues)
        self.assertEqual(fValue, 3)

        depthValues = [np.nan, 2, 3, 4, 5]
        depthValuesma = np.ma.masked_invalid(depthValues)
        fValue = meanDepth(depthValuesma)
        self.assertEqual(fValue, 3.5)

        depthValues = [np.nan, np.nan, np.nan, np.nan, np.nan]
        depthValuesma = np.ma.masked_invalid(depthValues)
        fValue = meanDepth(depthValuesma)
        self.assertEqual(fValue, 0)

    def test_maxDepth(self):
        from metrics import maxDepth
        self.assertTrue(False)

    def test_getRefElev(self):
        from metrics import getRefElev
        self.assertTrue(False)


    # end point on XS when XS is not precise multiple of station distance
    # An idea for this test is get the original line length and compare with
    # the array size multiplied by the station interval

    # Figure out how to handle cross sections with no data parts

    # Which width to use for ratios... is it wetted width or total length

    # Write the attributes to the shapefile



class TestVoronoiClass(unittest.TestCase):

    def test_collectCenterLines(self):
        from vor import NARVoronoi
        self.assertTrue(False)

    def test_createshapes(self):
        from vor import NARVoronoi
        self.assertTrue(False)

class TestGeoSmoothingClass(unittest.TestCase):
    """
    This is going to be a hard one to test but it came from someone else's implementation so
    I think we should try since testing will help us understand what we are using.
    """

    def test_smooth(self):
        from geosmoothing import *
        self.assertTrue(False)