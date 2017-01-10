from logger import Logger
from raster import Raster
import numpy as np

def calcMetrics(validXS, rivershape, sDEM ):
    """
    Jhu Li: Do the thing!!!!!!
    :param validXS:
    :param rivershape:
    :param sDEM:
    :return:
    """
    log = Logger('Metrics')

    dem = Raster(sDEM)

    for lineXS in validXS:
        for xs in lineXS:
            arr = interpolateRasterAlongLine(xs, dem)

    log.info("DOING MANY IMPORTANT THINGS!!!!!!")


def interpolateRasterAlongLine(xs, raster):
    """
    Proof of concept. Get the raster values at every point along a cross section
    :param xs:
    :param raster:
    :return:
    """
    points = [xs.interpolate(currDist) for currDist in np.arange(0, xs.length, 0.5)]
    vals = []
    for pt in points:
        vals.append(raster.getPixelVal(pt.coords[0]))
    return vals