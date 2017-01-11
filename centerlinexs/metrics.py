from logger import Logger
from raster import Raster
import numpy as np
from shapely import *
import math

def calcMetrics(validXS, rivershapeWithDonuts, sDEM, fStationInterval = 0.5):
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
    for lineXS in validXS:
        for xs in lineXS:
            arrRaw = interpolateRasterAlongLine(xs.geometry, dem, fStationInterval)
            # Mask out the np.nan values
            arrMasked = np.ma.masked_invalid(arrRaw)

            # Get the reference Elevation from the edges
            refElev = getRefElev(arrMasked)

            # The depth array must be calculated
            deptharr = refElev - arrMasked

            xs.metrics["XSLength"] = xs.geometry.length
            xs.metrics["WetWidth"] = dryWidth(xs.geometry, rivershapeWithDonuts)
            xs.metrics["DryWidth"] = xs.metrics["XSLength"] - xs.metrics["WetWidth"]
            xs.metrics["MaxDepth"] = maxDepth(arrMasked)
            xs.metrics["MeanDepth"] = meanDepth(deptharr)

            xs.metrics["W2MxDepth"] = xs.metrics["XSLength"] / xs.metrics["MaxDepth"]
            xs.metrics["W2AvDepth"] = xs.metrics["XSLength"] / xs.metrics["MeanDepth"]

def getRefElev(arr):
    """
    Take a masked array and return a reference depth
    :param arr: Masked array
    :return:
    """
    # TODO: What to do when the endpoints don't have depth?
    # WARNING: THIS MAY PRODUCE A DIVISION BY 0!!!!!
    return np.average(arr[0] + arr[-1]) / 2

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
    return np.average([x for x in deptharr if x > 0])

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
    else:
        a = sum([intersect.length for intersect in intersects])

    return a

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