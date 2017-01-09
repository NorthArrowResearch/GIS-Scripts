#!/usr/bin/env python
from descartes import PolygonPatch
import ogr
import json
import os
import math
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection

from shapes import *

class River:

    def __init__(self, sRiverShape, sIslands, sCenterLine, sXS):

        # --------------------------------------------------------
        # Load the Shapefiles we need
        # --------------------------------------------------------

        # TODO: This is begging for a little abstraction
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(sRiverShape, 0)
        riverjson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']
        spatialRef = dataSource.GetLayer().GetSpatialRef()
        oldrivershape = MultiPolygon([shape(riverjson)])

        # We're assuming here that the centerline only has one line segment
        dataSource = driver.Open(sCenterLine, 0)

        centerlines = []
        for feature in dataSource.GetLayer():
            cljson = json.loads(feature.ExportToJson())['geometry']
            centerlines.append({
                "main": feature.GetField("main"),
                "line": LineString(shape(cljson))
            })

        # Load in the island shapes
        dataSource = driver.Open(sIslands, 0)
        islands = []

        for isl in dataSource.GetLayer():
            if isl.GetField("Qualifying") == 1:
                islandjson = json.loads(isl.ExportToJson())['geometry']
                islands.append(Polygon(shape(islandjson)))

        # --------------------------------------------------------
        # Make a new rivershape using the exterior and only
        # qualifying islands
        # --------------------------------------------------------

        rivershape = Polygon(oldrivershape[0].exterior).difference(MultiPolygon(islands))

        # --------------------------------------------------------
        # Traverse the line(s)
        # --------------------------------------------------------

        # Longest possible line we use to extend our cross sections
        diag = getDiag(rivershape)
        allxslines = []
        throwaway = []

        for line in centerlines:
            linexs = []
            # Get 50cm spaced points
            points = [line["line"].interpolate(currDist) for currDist in np.arange(0, line["line"].length, 0.5)]

            # TODO: This offset method for slope is a little problematic. Would be nice to find a better slope method using shapely
            _offsetpts = [line["line"].interpolate(currDist+0.001) for currDist in np.arange(0, line["line"].length, 0.5)]
            slopes = [((points[idx].coords[0][1] - _offsetpts[idx].coords[0][1]) /
                       (points[idx].coords[0][0] - _offsetpts[idx].coords[0][0])) for idx, pt in enumerate(_offsetpts)]

            # Now create the cross sections with length = 2 * diag
            for ptidx, pt in enumerate(points):
                slope = slopes[ptidx]

                # Nothing to see here. Just linear algebra
                # Make sure to handle the infinite slope case
                if slope == 0:
                    m = 1
                    k = diag
                else:
                    # Negative reciprocal is the perpendicular slope
                    m = np.reciprocal(slopes[ptidx]) * -1
                    k = diag / math.sqrt(1 + math.pow(m, 2))

                # Shoot lines out in both directions using +/- k
                xsLong = LineString([(pt.coords[0][0] - k, pt.coords[0][1] - k * m),
                                          (pt.coords[0][0] + k, pt.coords[0][1] + k * m)])

                if math.isnan(xsLong.coords[0][1]):
                    print list(xsLong.coords)

                # Make a shape that is just the exterior shape and the qualifying islands

                intersections = rivershape.intersection(xsLong)
                inlist = []

                # Intersections returns a number of object types. We need to deal with all the valid ones
                if not intersections.is_empty:
                    if intersections.type == "LineString":
                        inlist = [intersections]
                    elif intersections.type == "MultiLineString":
                        inlist = list(intersections)

                    for xs in inlist:
                        keep = True
                        # Add only lines that contain the centerpoint
                        if xs.interpolate(xs.project(pt)).distance(pt) > 0.01:
                            keep = False
                        # If this is not the main channel and our cross section touches the exterior wall in
                        # more than one place then lose it
                        if line['main'] == "no":
                            dista = Point(xs.coords[0]).distance(rivershape.exterior)
                            distb = Point(xs.coords[1]).distance(rivershape.exterior)
                            if dista < 0.001 and distb < 0.001:
                                keep = False
                        if keep:
                            linexs.append(xs)
                        else:
                            throwaway.append(xs)

            allxslines.append(linexs)

        # --------------------------------------------------------
        # Valid vs invalid?
        # --------------------------------------------------------
        valid = []
        invalid = []
        for xsgroup in allxslines:
            groupvalid = []
            groupinvalid = []
            lengths = [xs.length for xs in xsgroup]
            stdev = np.std(lengths)
            mean = np.mean(lengths)

            # Test each cross section for validity.
            # TODO: Right now it's just stddev test. There should probably be others
            for xs in xsgroup:
                if xs.length > (mean + 4 * stdev):
                    groupvalid.append(xs)
                else:
                    groupinvalid.append(xs)
            valid.append(groupvalid)
            valid.append(groupinvalid)

        # --------------------------------------------------------
        # Write the output Shapefile
        # --------------------------------------------------------
        schema = {'geometry': 'MultiLineString', 'properties': {'name': 'str'}}

        if os.path.exists(sXS):
            driver.DeleteDataSource(sXS)

        outDataSource = driver.CreateDataSource(sXS)
        outLayer = outDataSource.CreateLayer(sXS, spatialRef, geom_type=ogr.wkbMultiLineString)

        # quick and dirty write all xs to shapefile
        exportlines = []
        for g in allxslines:
            for xs in g:
                exportlines.append(xs)

        ogrmultiline = ogr.CreateGeometryFromJson(json.dumps(mapping(MultiLineString(exportlines))))

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

        for c in centerlines:
            plotShape(ax, c['line'], '#000000', 0.5, 20)

        # plotShape(ax, MultiLineString(throwaway), '#FF0000', 1, 20)

        for g in valid:
            plotShape(ax, MultiLineString(g), '#0000FF', 0.3, 20)
        for g in invalid:
            plotShape(ax, MultiLineString(g), '#00FF00', 0.5, 20)

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
    theRiver = River("../thiessen/sample/WettedExtent.shp", "../thiessen/sample/Islands.shp", "../thiessen/output/centerline.shp", "output/crosssection.shp")
    # vor = NARVoronoi(theRiver.wet.points)
    # vor.plot()

    print "done"

if __name__ == "__main__":
    main()

