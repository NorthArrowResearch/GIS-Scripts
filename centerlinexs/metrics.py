from logger import Logger
from raster import Raster
import numpy as np
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

    dMetrics = {} # key is Cross Section index to value of a dictionary where key is metric field name and value is metric value

    dem = Raster(sDEM)

    for lineXS in validXS:
        for xs in lineXS:
            arrRaw = interpolateRasterAlongLine(xs.geometry, dem, fStationInterval)
            arr = [x for x in arrRaw if x is not None]

            refElev = np.average(arr[0] + arr[-1]) / 2

            xs.metrics["XSLength"] = xs.geometry.length
            xs.metrics["WetWidth"] = DryWidth(xs.geometry, rivershapeWithDonuts)
            xs.metrics["DryWidth"] = xs.metrics["XSLength"] - xs.metrics["WetWidth"]
            xs.metrics["MaxDepth"] = refElev - min(arr)

            deptharr = refElev - arr
            xs.metrics["MeanDepth"] = np.average([x for x in deptharr if x > 0])

            xs.metrics["W2MxDepth"] = xs.metrics["XSLength"] / xs.metrics["MaxDepth"]
            xs.metrics["W2AvDepth"] = xs.metrics["XSLength"] / xs.metrics["MeanDepth"]

def DryWidth(xs, rivershapeWithDonuts):
    """

    :param xs: shapely cross section object
    :param rivershapeWithDonuts: Polygon with non-qualifying donuts retained
    :return:
    """

    intersects = xs.intersection(rivershapeWithDonuts)

    if intersects.type == "LineString":
        return intersects.length
    else:
        a = 0
        for intersect in intersects:
            a += intersect.length

    return a

def interpolateRasterAlongLine(xs, raster, fStationInterval):
    """
    Proof of concept. Get the raster values at every point along a cross section
    :param xs:
    :param raster:
    :return:
    """
    points = [xs.interpolate(currDist) for currDist in np.arange(0, xs.length, fStationInterval)]
    vals = []
    for pt in points:
        vals.append(raster.getPixelVal(pt.coords[0]))
    return vals