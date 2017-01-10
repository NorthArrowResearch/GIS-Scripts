#!/usr/bin/env python
import ogr
import json
import os, sys
from shapely.geometry import *
import argparse
from logger import Logger

# We wrote two little files with helper methods:
from vor import NARVoronoi
from shapes import *
from geosmoothing import *

# These are just for graphing
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch


def centerline(args):

    log = Logger("Centerline")

    # --------------------------------------------------------
    # Load the Shapefiles we need
    # --------------------------------------------------------
    rivershp = Shapefile(args.river.name)
    thalwegshp = Shapefile(args.thalweg.name)
    islandsshp = Shapefile(args.islands.name)

    # Pull the geometry objects out and disregard the fields
    polyRiverShape = rivershp.featuresToShapely()[0]['geometry']
    lineThalweg = thalwegshp.featuresToShapely()[0]['geometry']

    # Load in the island shapes then filter them to qualifying only
    islList = islandsshp.featuresToShapely()
    multipolIslands = MultiPolygon([isl['geometry'] for isl in islList if isl['fields']['Qualifying'] == 1])

    # --------------------------------------------------------
    # Make a new rivershape using the exterior and only
    # qualifying islands from that shapefile
    # --------------------------------------------------------

    rivershape = Polygon(polyRiverShape.exterior).difference(multipolIslands)
    riverspliner = GeoSmoothing()
    # The Spline smooth gives us round curves.
    smoothRiver = riverspliner.smooth(rivershape)
    # The simplifyer reduces point count to make things manageable
    smoothRiver = smoothRiver.simplify(0.01)

    # --------------------------------------------------------
    # Find the centerline
    # --------------------------------------------------------

    # First and last line segment we need to extend
    thalwegStart = LineString([lineThalweg.coords[1], lineThalweg.coords[0]])
    thalwegEnd = LineString([lineThalweg.coords[-2], lineThalweg.coords[-1]])

    # Get the bounds of the river with a little extra buffer (10)
    rivershapeBounds = getBufferedBounds(rivershape, 10)

    # Now see where the lines intersect the bounding rectangle
    thalwegStartExt = rectIntersect(thalwegStart, rivershapeBounds)
    thalwegEndExt = rectIntersect(thalwegEnd, rivershapeBounds)

    # Now make a NEW thalweg by adding the extension points to the start
    # and end points of the original
    thalweglist = list(lineThalweg.coords)
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

    # Now we consider interiors. NB: Interiors are only qualifying islands in this case
    for idx, island in enumerate(smoothRiver.interiors):
        for pt in list(island.coords):
            side = 1 if bankshapes[0].contains(Point(pt)) else -1
            points.append(RiverPoint(pt, interior=True, side=side, island=idx))

    # Here's where the Voronoi polygons come into play
    myVorL = NARVoronoi(points)

    # (OPTIONAL). Makes the polygons we will use to visualize
    myVorL.createshapes()

    # This is the function that does the actual work of creating the centerline
    linespliner = GeoSmoothing(spl_smpar=5)
    centerline = myVorL.collectCenterLines()
    centerlineSmooth = linespliner.smooth(centerline)

    # Now we've got the main centerline let's flip the islands one by one
    # and get alternate lines
    alternateLines = []
    for idx, island in enumerate(smoothRiver.interiors):
        altLine = myVorL.collectCenterLines(flipIsland=idx)
        if altLine.type == "LineString":
            # We difference the alternate lines with the main line
            # to get just the bit that is different
            smoothAlt = linespliner.smooth(altLine.difference(centerline))
            alternateLines.append(smoothAlt)

    # --------------------------------------------------------
    # Write the output Shapefile
    # --------------------------------------------------------
    # TODO: I'd love to abstract all this away but it's a pain to do this in a generic way
    outShape = Shapefile()
    outShape.create(args.centerline, rivershp.spatialRef, geoType=ogr.wkbMultiLineString)

    outShape.layer.CreateField(ogr.FieldDefn('main', ogr.OFTString))

    featureDefn = outShape.layer.GetLayerDefn()

    # The main centerline gets written first
    outFeature = ogr.Feature(featureDefn)
    ogrmultiline = ogr.CreateGeometryFromJson(json.dumps(mapping(centerlineSmooth)))
    outFeature.SetGeometry(ogrmultiline)
    outFeature.SetField('main', 'yes')
    outShape.layer.CreateFeature(outFeature)

    # We do all this again for each alternate line
    for altline in alternateLines:
        newfeat = ogr.Feature(featureDefn)
        linething = ogr.CreateGeometryFromJson(json.dumps(mapping(altline)))
        newfeat.SetGeometry(linething)
        newfeat.SetField('main', 'no')
        outShape.layer.CreateFeature(newfeat)

    # --------------------------------------------------------
    # Do a little show and tell with plotting and whatnot
    # --------------------------------------------------------
    if not args.noviz:
        fig = plt.figure(1, figsize=(10, 10))
        ax = fig.gca()

        # Left and right banks are light red and blue
        plotShape(ax, bankshapes[0], '#DDCCCC', 1, 0)
        plotShape(ax, bankshapes[1], '#AAAABB', 1, 0)

        # The Voronoi shapes are light grey
        plotShape(ax, myVorL.polys, '#444444', 0.1, 6)

        # The rivershape is slightly green
        plotShape(ax, rivershape, '#AACCAA', 0.4, 8)
        plotShape(ax, smoothRiver, '#AAAACC', 0.2, 8)

        # Thalweg is green and where it extends to the bounding rectangle is orange
        plotShape(ax, newThalweg, '#FFA500', 1, 15)
        plotShape(ax, lineThalweg, '#00FF00', 1, 20)

        # The centerline we choose is bright red
        plotShape(ax, centerline, '#660000', 0.6, 30)
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


if __name__ == "__main__":

    log = Logger("Initializing")

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('river',
                        help='Path to the river shape file. Donuts will be ignored.',
                        type=argparse.FileType('r'))
    parser.add_argument('thalweg',
                        help='Path to the thalweg shapefile',
                        type=argparse.FileType('r'))
    parser.add_argument('islands',
                        help='Path to the islands shapefile.',
                        type=argparse.FileType('r'))
    parser.add_argument('centerline',
                        help='Path to the desired output centerline shapefile')
    parser.add_argument('--noviz',
                        help = 'Disable graph results',
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    if not args.river or not args.thalweg or not args.islands or not args.centerline:
        print "ERROR: Missing arguments"
        parser.print_help()
        exit(0)

    log = Logger("Program")

    try:
        centerline(args)
    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)

