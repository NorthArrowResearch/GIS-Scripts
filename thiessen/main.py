#!/usr/bin/env python
import ogr
import json
import os
from shapely.geometry import *

# We wrote two little files with helper methods:
from vor import NARVoronoi
from shapes import *
from geosmoothing import *

# These are just for graphing
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch


class River:

    def __init__(self, sRiverShape, sThalweg, sIslands, sCenterline):

        # --------------------------------------------------------
        # Load the Shapefiles we need
        # --------------------------------------------------------
        # TODO: This is begging for a little abstraction
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(sRiverShape, 0)
        spatialRef = dataSource.GetLayer().GetSpatialRef()
        riverjson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']

        oldrivershape = MultiPolygon([shape(riverjson)])

        # We're assuming here that the thalweg only has one line segment
        dataSource = driver.Open(sThalweg, 0)

        thalwegjson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']
        thalweg = LineString(shape(thalwegjson))

        # Load in the island shapes
        dataSource = driver.Open(sIslands, 0)
        islands = []

        for isl in dataSource.GetLayer():
            if isl.GetField("Qualifying") == 1:
                islandjson = json.loads(isl.ExportToJson())['geometry']
                islands.append(Polygon(shape(islandjson)))


        # --------------------------------------------------------
        # Make a new rivershape using the exterior and only
        # qualifying islands from that shapefile
        # --------------------------------------------------------

        rivershape = Polygon(oldrivershape[0].exterior).difference(MultiPolygon(islands))
        smoothing = GeoSmoothing()
        smoothRiver = smoothing.smooth(rivershape)
        smoothRiver = smoothRiver.simplify(0.02)


        # --------------------------------------------------------
        # Find the centerline
        # --------------------------------------------------------

        # First and last line segment we need to extend
        thalwegStart = LineString([thalweg.coords[1], thalweg.coords[0]])
        thalwegEnd = LineString([thalweg.coords[-2], thalweg.coords[-1]])

        # Get the bounds of the river with a little extra buffer (10)
        rivershapeBounds = getBufferedBounds(rivershape, 10)

        # Now see where the lines intersect the bounding rectangle
        thalwegStartExt = rectIntersect(thalwegStart, rivershapeBounds)
        thalwegEndExt = rectIntersect(thalwegEnd, rivershapeBounds)

        # Now make a NEW thalweg by adding the extension points to the start
        # and end points of the original
        thalweglist = list(thalweg.coords)
        thalweglist.insert(0, thalwegStartExt.coords[1])
        thalweglist.append(thalwegEndExt.coords[1])

        newThalweg = LineString(thalweglist)

        # splitClockwise gives us our left and right bank polygons
        bankshapes = splitClockwise(rivershapeBounds, newThalweg)

        # Add all the points (including islands) to the list
        points = []

        # Exterior is the shell and there is only ever 1
        for pt in list(smoothRiver.exterior.coords):
            side = 1 if bankshapes[0].contains(Point(pt)) else -1
            points.append(RiverPoint(pt, interior=False, side=side))

        # NOTE: We ignore interiors and use the islands shapefile instead
        for idx, island in enumerate(smoothRiver.interiors):
            for pt in list(island.coords):
                side = 1 if bankshapes[0].contains(Point(pt)) else -1
                points.append(RiverPoint(pt, interior=True, side=side, island=idx))

        # Here's where the Voronoi polygons come into play
        myVorL = NARVoronoi(points)

        # (OPTIONAL). Makes the polygons we will use to visualize
        myVorL.createshapes()

        # This is the function that does the actual work of creating the centerline
        centerline = myVorL.collectCenterLines()
        centerlineSmooth = smoothing.smooth(centerline)

        print len(centerline.coords)
        print len(centerlineSmooth.coords)

        # Now we've got the main centerline let's flip the islands one by one
        # and get alternate lines
        alternateLines = []
        for idx, island in enumerate(smoothRiver.interiors):
            altLine = myVorL.collectCenterLines(flipIsland=idx)
            if altLine.type == "LineString":
                # We difference the alternate lines with the main line
                # to get just the bit that is different
                smoothAlt = smoothing.smooth(altLine.difference(centerline))
                alternateLines.append(smoothAlt)


        # --------------------------------------------------------
        # Write the output Shapefile
        # --------------------------------------------------------

        schema = {'geometry': 'MultiLineString', 'properties': {'name': 'str'}}

        if os.path.exists(sCenterline):
            driver.DeleteDataSource(sCenterline)
        outDataSource = driver.CreateDataSource(sCenterline)
        outLayer = outDataSource.CreateLayer(sCenterline, spatialRef, geom_type=ogr.wkbMultiLineString)
        outLayer.CreateField(ogr.FieldDefn('main', ogr.OFTString))

        featureDefn = outLayer.GetLayerDefn()
        # The main centerline gets written first
        outFeature = ogr.Feature(featureDefn)
        ogrmultiline = ogr.CreateGeometryFromJson(json.dumps(mapping(centerlineSmooth)))
        outFeature.SetGeometry(ogrmultiline)
        outFeature.SetField('main', 'yes')
        outLayer.CreateFeature(outFeature)

        # We do all this again for each alternate line
        for altline in alternateLines:
            newfeat = ogr.Feature(featureDefn)
            linething = ogr.CreateGeometryFromJson(json.dumps(mapping(altline)))
            newfeat.SetGeometry(linething)
            newfeat.SetField('main', 'no')
            outLayer.CreateFeature(newfeat)



        # --------------------------------------------------------
        # Do a little show and tell with plotting and whatnot
        # --------------------------------------------------------

        fig = plt.figure(1, figsize=(10, 10))
        ax = fig.gca()

        # Left and right banks are light red and blue
        plotShape(ax, bankshapes[0], '#DDCCCC', 1, 0)
        plotShape(ax, bankshapes[1], '#AAAABB', 1, 0)

        # The Voronoi shapes are light grey
        plotShape(ax, myVorL.polys, '#444444', 0.1, 6)

        # The rivershape is slightly green
        plotShape(ax, rivershape, '#AACCAA', 0.4, 8)
        plotShape(ax, smoothRiver, '#AAAACC', 0.4, 8)

        # Thalweg is green and where it extends to the bounding rectangle is orange
        plotShape(ax, newThalweg, '#FFA500', 1, 15)
        plotShape(ax, thalweg, '#00FF00', 1, 20)

        # The centerline we choose is bright red
        plotShape(ax, centerlineSmooth, '#FF0000', 0.8, 30)
        # The alternate lines are in yellow
        plotShape(ax, MultiLineString(alternateLines), '#FFFF00', 0.8, 25)

        plt.ylim(rivershapeBounds.bounds[1], rivershapeBounds.bounds[3])
        plt.xlim(rivershapeBounds.bounds[0], rivershapeBounds.bounds[2])
        plt.autoscale(enable=False)
        plt.show()


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
            ax.plot(x, y, color=color, alpha=alpha, markersize=2, marker=".", zorder=zord)

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
    theRiver = River("sample/WettedExtent.shp", "sample/Thalweg.shp", "sample/Islands.shp", "output/centerline.shp")

    print "done"

if __name__ == "__main__":
    main()

