#!/usr/bin/env python
import os, sys
from shapely.geometry import *
import argparse
from logger import Logger

# We wrote two little files with helper methods:
from vor import NARVoronoi
from shapes import *
from geosmoothing import *
from plotting import Plotter

########################################################
# Here are some factors you can play with

# This is the smoothing factor (k) that we apply to the spline AFTER the centerline has
# been created
LINE_SPL_SMPAR = 5
# The factor to throw into shapely.simplify (http://toblerity.org/shapely/manual.html)
SHAPELY_SIMPLIFY = 0.01
########################################################


# These are just for graphing
def centerline(args):
    """
    A Note about debugging:

    You can use the following paths in this repo:

     "../sampledata/Visit_2425/WettedExtent.shp" "../sampledata/Visit_2425/Thalweg.shp" "../sampledata/Visit_2425/Islands.shp" "../sampledata/outputs/centerline.shp"

    :param args:
    :return:
    """

    log = Logger("Centerline")

    # --------------------------------------------------------
    # Load the Shapefiles we need
    # --------------------------------------------------------
    log.info("Opening Shapefiles...")
    rivershp = Shapefile(args.river.name)
    thalwegshp = Shapefile(args.thalweg.name)
    islandsshp = Shapefile(args.islands.name)

    # Pull the geometry objects out and disregard the fields
    polyRiverShape = rivershp.featuresToShapely()[0]['geometry']
    lineThalweg = thalwegshp.featuresToShapely()[0]['geometry']

    # Load in the island shapes then filter them to qualifying only
    islList = islandsshp.featuresToShapely()
    multipolIslands = MultiPolygon([isl['geometry'] for isl in islList if isl['fields']['Qualifying'] == 1])

    # Make a new rivershape using the exterior and only qualifying islands from that shapefile
    log.info("Combining exterior and qualifying islands...")
    rivershape = Polygon(polyRiverShape.exterior).difference(multipolIslands)

    # The Spline smooth gives us round curves.
    log.info("Spline Smoothing...")
    riverspliner = GeoSmoothing()
    smoothRiver = riverspliner.smooth(rivershape)
    # The simplifyer reduces point count to make things manageable
    smoothRiver = smoothRiver.simplify(SHAPELY_SIMPLIFY)

    # --------------------------------------------------------
    # Find the Centerline
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
    log.info("Calculating Voronoi Polygons...")
    myVorL = NARVoronoi(points)

    # This is the function that does the actual work of creating the centerline
    log.info("Spline Smoothing Main Line...")
    linespliner = GeoSmoothing(spl_smpar=LINE_SPL_SMPAR)
    centerline = myVorL.collectCenterLines()
    centerlineSmooth = linespliner.smooth(centerline)

    # Trim to be inside the river shape.
    # TODO: Is this dangerous? Maybe.... Might want to do a bit of testing
    centerlineSmooth = centerlineSmooth.intersection(rivershape)

    # Now we've got the main centerline let's flip the islands one by one
    # and get alternate lines
    alternateLines = []
    for idx, island in enumerate(smoothRiver.interiors):
        altLine = myVorL.collectCenterLines(flipIsland=idx)
        log.info("  Spline Smoothing Alternate line...")
        if altLine.type == "LineString":
            # We difference the alternate lines with the main line
            # to get just the bit that is different
            diffaltline = altLine.difference(centerline)

            # Now smooth this line to be roughly the consistency of skippy peanut butter
            smoothAlt = linespliner.smooth(diffaltline)

            # Now we reconnect the bit that is different with the smoothed
            # Segment since smoothing can mess up the intersection
            reconLine = reconnectLine(centerlineSmooth, smoothAlt)

            alternateLines.append(reconLine)

    # --------------------------------------------------------
    # Write the output Shapefile
    # --------------------------------------------------------
    # TODO: I'd love to abstract all this away but it's a pain to do this in a generic way
    log.info("Writing Shapefiles...")
    outShape = Shapefile()
    outShape.create(args.centerline, rivershp.spatialRef, geoType=ogr.wkbMultiLineString)

    outShape.layer.CreateField(ogr.FieldDefn('Channel', ogr.OFTString))

    # ShapeFiles must have an ID field
    field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
    outShape.layer.CreateField(field_defn)

    featureDefn = outShape.layer.GetLayerDefn()

    # The main centerline gets written first
    outFeature = ogr.Feature(featureDefn)
    ogrmultiline = ogr.CreateGeometryFromJson(json.dumps(mapping(centerlineSmooth)))
    outFeature.SetGeometry(ogrmultiline)
    outFeature.SetField('Channel', 'Main')
    featureID = 1
    outFeature.SetField('ID', featureID)
    outShape.layer.CreateFeature(outFeature)

    # We do all this again for each alternate line
    for altline in alternateLines:
        newfeat = ogr.Feature(featureDefn)
        linething = ogr.CreateGeometryFromJson(json.dumps(mapping(altline)))
        newfeat.SetGeometry(linething)
        newfeat.SetField('Channel', 'Side')
        featureID += 1
        newfeat.SetField('ID', featureID)
        outShape.layer.CreateFeature(newfeat)

    # --------------------------------------------------------
    # Do a little show and tell with plotting and whatnot
    # --------------------------------------------------------
    if not args.noviz:
        log.info("Plotting Results...")
        plt = Plotter()

        # (OPTIONAL). Makes the polygons we will use to visualize
        myVorL.createshapes()

        # Left and right banks are light red and blue
        plt.plotShape(bankshapes[0], '#DDCCCC', 1, 0)
        plt.plotShape(bankshapes[1], '#AAAABB', 1, 0)

        # The Voronoi shapes are light grey (really slow for some reason)
        plt.plotShape(myVorL.polys, '#444444', 0.1, 6)

        # The rivershape is slightly green
        plt.plotShape(rivershape, '#AACCAA', 0.4, 8)
        plt.plotShape(smoothRiver, '#AAAACC', 0.2, 8)

        # Thalweg is green and where it extends to the bounding rectangle is orange
        plt.plotShape(newThalweg, '#FFA500', 1, 15)
        plt.plotShape(lineThalweg, '#00FF00', 1, 20)

        # The centerline we choose is bright red
        # plt.plotShape(centerline, '#660000', 0.6, 30)
        plt.plotShape(centerlineSmooth, '#FF0000', 0.8, 30)
        # The alternate lines are in yellow
        plt.plotShape(MultiLineString(alternateLines), '#FFFF00', 0.8, 25)

        plt.showPlot(rivershapeBounds.bounds)



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
                        help = 'Disable result visualization',
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    if not args.river or not args.thalweg or not args.islands or not args.centerline:
        log.error("ERROR: Missing arguments")
        parser.print_help()
        exit(0)

    log = Logger("Program")

    try:
        centerline(args)
        log.info("Completed Successfully")
    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)

