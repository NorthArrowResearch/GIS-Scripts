from logger import Logger
from raster import Raster
import numpy as np
from shapely.geometry import *
import math

def calcMetrics(xsobjList, rivershapeWithDonuts, sDEM, fStationInterval = 0.5):
    """
    Jhu Li: Do the thing!!!!!!
    :param validXS: List of centerlines, each contains a list of cross sections on that centerline. Each cross section is XSObj that has member Shapely Line and empty member dict for metrics
    :param rivershape:
    :param sDEM:
    :return:
    """
    log = Logger('Metrics')
    dem = Raster(sDEM)

    log.info("Calculating metrics for all crosssections")
    for xs in xsobjList:
        arrRaw = interpolateRasterAlongLine(xs.geometry, dem, fStationInterval)
        # Mask out the np.nan values
        arrMasked = np.ma.masked_invalid(arrRaw)

        # Get the reference Elevation from the edges
        refElev = getRefElev(arrMasked)
        if refElev == 0:
            xs.isValid = False

        # The depth array must be calculated
        deptharr = refElev - arrMasked

        xs.metrics["XSLength"] = xs.geometry.length
        xs.metrics["WetWidth"] = dryWidth(xs.geometry, rivershapeWithDonuts)
        # xs.metrics["DryWidth"] = xs.metrics["XSLength"] - xs.metrics["WetWidth"]
        # xs.metrics["MaxDepth"] = maxDepth(arrMasked)
        # xs.metrics["MeanDepth"] = meanDepth(deptharr)
        #
        # if xs.metrics["MaxDepth"] == 0.0:
        #     xs.metrics["W2MxDepth"] = 0
        # else:
        #     xs.metrics["W2MxDepth"] = xs.metrics["WetWidth"] / xs.metrics["MaxDepth"]
        #
        # if xs.metrics["MeanDepth"] == 0.0:
        #     xs.metrics["W2AvDepth"] = 0
        # else:
        #     xs.metrics["W2AvDepth"] = xs.metrics["WetWidth"] / xs.metrics["MeanDepth"]

def getRefElev(arr):
    """
    Take a masked array and return a reference depth
    :param arr: Masked array
    :return:
    """
    # TODO: What to do when the endpoints don't have depth?
    # WARNING: THIS MAY PRODUCE A DIVISION BY 0!!!!!

    fValue = np.average(arr[0] + arr[-1]) / 2
    if arr.mask[0] or arr.mask[-1]:
        fValue = 0

    return fValue

def maxDepth(arr):
    """
    Calculate the maximum depth from a list of values
    :param arr:
    :return:
    """
    refElev = np.average(arr[0] + arr[-1]) / 2
    return refElev - min(arr)


def meanDepth(deptharr):
    """
    Calculate the mean depth from a list of depths
    :param deptharr:
    :return:
    """
    fValue = np.average([x for x in deptharr if x > 0])
    if np.isnan(fValue):
        fValue = 0

    return fValue

def dryWidth(xs, rivershapeWithDonuts):
    """

    :param xs: shapely cross section object
    :param rivershapeWithDonuts: Polygon with non-qualifying donuts retained
    :return:
    """

    # Get all intersects of this crosssection with the rivershape
    intersects = xs.intersection(rivershapeWithDonuts)

    # The intersect may be one object (LineString) or many. We have to handle both cases
    if intersects.type == "LineString":
        intersects = MultiLineString([intersects])

    return sum([intersect.length for intersect in intersects])

def interpolateRasterAlongLine(xs, raster, fStationInterval):
    """
    Proof of concept. Get the raster values at every point along a cross section
    :param xs:
    :param raster:
    :return:
    """
    points = [xs.interpolate(currDist) for currDist in np.arange(0, xs.length, fStationInterval)]
    vals = [raster.getPixelVal(pt.coords[0]) for pt in points]
    return vals