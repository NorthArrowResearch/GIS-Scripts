#!/usr/bin/env python
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import ogr
import json
import os
from shapely.geometry import *
import numpy as np
from shapes import *

class River:

    def __init__(self, sRiverShape, sCenterLine, sXS):

        # --------------------------------------------------------
        # Load the Shapefiles we need
        # --------------------------------------------------------

        # TODO: This is begging for a little abstraction
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(sRiverShape, 0)
        riverjson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']
        spatialRef = dataSource.GetLayer().GetSpatialRef()
        rivershape = MultiPolygon([shape(riverjson)])

        # We're assuming here that the centerline only has one line segment
        dataSource = driver.Open(sCenterLine, 0)

        cljson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']
        centerline = LineString(shape(cljson))


        # --------------------------------------------------------
        # Traverse the line
        # --------------------------------------------------------

        ended = False
        currDist = 0
        # Get 50cm spaced points
        points = [centerline.interpolate(currDist) for currDist in np.arange(0, centerline.length, 0.5)]
        # TODO: This offset method is a little problematic. Would be nice to fins a better slope method using shapely
        _offsetpts = [centerline.interpolate(currDist+0.001) for currDist in np.arange(0, centerline.length, 0.5)]
        slopes = [((points[idx].coords[0][1] - _offsetpts[idx].coords[0][1]) /
                   (points[idx].coords[0][0] - _offsetpts[idx].coords[0][0])) for idx,pt in enumerate(_offsetpts)]

        # Longest possible line
        diag = getDiag(rivershape)
        xslines = []
        throwaway = []

        # Now create the cross sections with lengtho = 2*diag
        for ptidx, pt in enumerate(points):
            slope = slopes[ptidx]
            # Negative reciprocal is the negative slope
            m = np.reciprocal(slopes[ptidx]) * -1
            # Create a line
            k = diag / math.sqrt(1 + math.pow(m, 2))

            # Shoot lines out in both directions using +/- k
            xsLong = LineString([(pt.coords[0][0] - k, pt.coords[0][1] - k * m),
                                      (pt.coords[0][0] + k, pt.coords[0][1] + k * m)])

            intersections = rivershape.intersection(xsLong)

            if not intersections.is_empty:
                if intersections.type == "LineString":
                    xslines.append(intersections)
                elif intersections.type == "MultiLineString":
                    interList = list(intersections)
                    # Add lines that contain the centerpoint
                    for xs in interList:
                        if xs.interpolate(xs.project(pt)).distance(pt) < 0.01:
                            xslines.append(xs)
                        else:
                            throwaway.append(xs)

        # --------------------------------------------------------
        # Traverse the line
        # --------------------------------------------------------
        valid = []
        lengths = [xs.length for xs in xslines]
        stdev = np.std(lengths)
        mean = np.mean(lengths)

        for xs in xslines:
            isValid = True
            if xs.length > (mean + 4 * stdev):
                isValid = False
            valid.append(isValid)

        validXS = [xs for idx, xs in enumerate(xslines) if valid[idx]]

        # --------------------------------------------------------
        # Write the output Shapefile
        # --------------------------------------------------------
        schema = {'geometry': 'MultiLineString', 'properties': {'name': 'str'}}

        if os.path.exists(sXS):
            driver.DeleteDataSource(sXS)

        outDataSource = driver.CreateDataSource(sXS)
        outLayer = outDataSource.CreateLayer(sXS, spatialRef, geom_type=ogr.wkbMultiLineString)

        ogrmultiline = ogr.CreateGeometryFromJson(json.dumps(mapping(MultiLineString(xslines))))

        idField = ogr.FieldDefn('name', ogr.OFTString)
        outLayer.CreateField(idField)

        featureDefn = outLayer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(ogrmultiline)
        outFeature.SetField('name', ogr.OFTString)
        outLayer.CreateFeature(outFeature)


        # --------------------------------------------------------
        # Do a little show and tell with plotting and whatnot
        # --------------------------------------------------------
        fig = plt.figure(1, figsize=(10, 10))
        ax = fig.gca()

        plotShape(ax, rivershape, '#AAAAAA', 1, 5)
        plotShape(ax, MultiPoint(points), '#000000', 1, 10)
        plotShape(ax, centerline, '#FFAABB', 0.5, 20)

        plotShape(ax, MultiLineString(throwaway), '#FF0000', 1, 20)
        plotShape(ax, MultiLineString(xslines), '#00FF00', 1, 25)
        plotShape(ax, MultiLineString(validXS), '#0000FF', 1, 30)

        plt.autoscale(enable=True)
        plt.show()


def getDiag(rect):
    """
    return the biggest possible distance inside a rectangle (the diagonal)
    :param rect: rectangle polygon
    :return:
    """
    return math.sqrt(
        math.pow((rect.bounds[3] - rect.bounds[1]), 2) +
        math.pow((rect.bounds[2] - rect.bounds[0]), 2))

def plotShape(ax, mp, color, alpha, zord):
    """
    Nothing fancy here. Just a plotting function to help us visualize
    :param ax:
    :param mp:
    :param color:
    :param alpha:
    :param zord:
    :return:
    """
    # We're using Descartes here for polygonpathc
    if mp.type == 'Polygon':
        ax.add_patch(PolygonPatch(mp, fc=color, ec='#000000', lw=0.2, alpha=alpha, zorder=zord))

    elif mp.type == 'LineString':
        x, y = mp.xy
        ax.plot(x, y, color=color, alpha=alpha, linewidth=1, solid_capstyle='round', zorder=zord)

    elif mp.type == 'MultiPoint':
        for idx, p in enumerate(mp):
            x, y = p.xy
            ax.plot(x, y, color=color, alpha=alpha, markersize=2, marker="o", zorder=zord)

    elif mp.type == 'MultiLineString':
        for idx, p in enumerate(mp):
            x, y = p.xy
            ax.plot(x, y, color=color, alpha=alpha, linewidth=1, solid_capstyle='round', zorder=zord)

    elif mp.type == 'MultiPolygon':
        patches = []
        for idx, p in enumerate(mp):
            patches.append(PolygonPatch(p, fc=color, ec='#000000', lw=0.2, alpha=alpha, zorder=zord))
        ax.add_collection(PatchCollection(patches, match_original=True))


def main():
    '''

    :return:
    '''

    # We're just iterating over a folder. Change this to something else if you want
    theRiver = River("sample/WettedExtent.shp", "../thiessen/output/centerline.shp", "output/crosssection.shp")
    # vor = NARVoronoi(theRiver.wet.points)
    # vor.plot()

    print "done"

if __name__ == "__main__":
    main()

