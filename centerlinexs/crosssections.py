#!/usr/bin/env python
from shapely.geometry import *
import argparse
import sys
import numpy as np
from shapes import *
from plotting import Plotter
from logger import Logger
from metrics import *

def crosssections(args):
    """
    A Note about debugging:

    You can use the following paths in this repo:

    "../sampledata/Visit_2425/WettedExtent.shp" "../sampledata/Visit_2425/Islands.shp" "../sampledata/outputs/centerline.shp" "../sampledata/Visit_2425/DEM.tif" "../sampledata/outputs/crosssections.shp"

    :param args:
    :return:
    """

    # --------------------------------------------------------
    # Load the Shapefiles we need
    # --------------------------------------------------------
    log.info("Opening Shapefiles...")
    rivershp = Shapefile(args.river.name)
    centerline = Shapefile(args.centerline.name)
    islandsshp = Shapefile(args.islands.name)

    # Pull the geometry objects out and disregard the fields
    polyRiverShape = rivershp.featuresToShapely()[0]['geometry']
    centerlines = centerline.featuresToShapely()

    # Load in the island shapes then filter them to qualifying only
    islList = islandsshp.featuresToShapely()
    multipolIslands = MultiPolygon([isl['geometry'] for isl in islList if isl['fields']['Qualifying'] == 1])

    # Make a new rivershape using the exterior and only qualifying islands from that shapefile
    log.info("Combining exterior and qualifying islands...")
    rivershape = Polygon(polyRiverShape.exterior).difference(multipolIslands)

    # --------------------------------------------------------
    # Traverse the line(s)
    # --------------------------------------------------------
    log.info("Starting Centerline Traversal...")
    # Longest possible line we use to extend our cross sections
    diag = getDiag(rivershape)
    allxslines = []
    throwaway = []

    for line in centerlines:
        linexs = []
        linegeo = line['geometry']

        # Get 50cm spaced points
        points = [linegeo.interpolate(currDist) for currDist in np.arange(0, linegeo.length, 0.5)]

        # TODO: This offset method for slope is a little problematic. Would be nice to find a better slope method using shapely
        _offsetpts = [linegeo.interpolate(currDist+0.001) for currDist in np.arange(0, linegeo.length, 0.5)]
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
                    if line['fields']['main'] == "no":
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
    # Valid/invalid line testing
    # --------------------------------------------------------
    log.info("Testin XSs for Validity...")

    class XSObj:

        def __init__(self, centerlineID, geometry, isValid):
            self.centerlineID = centerlineID
            self.geometry = geometry
            self.metrics = {}
            self.valid = isValid

    xsObjList = []
    for xsgroup in allxslines:

        lengths = [xs.length for xs in xsgroup]
        stdev = np.std(lengths)
        mean = np.mean(lengths)

        # Test each cross section for validity.
        # TODO: Right now it's just stddev test. There should probably be others
        for idx, xs in enumerate(xsgroup):

            isValid =  xs.length > (mean + 4 * stdev)
            xsobj = XSObj(idx, xs, isValid)
            xsObjList.append(xsobj)

    # --------------------------------------------------------
    # Metric Calculation
    # --------------------------------------------------------
    calcMetrics(xsObjList, polyRiverShape, args.dem.name)

    # --------------------------------------------------------
    # Write the output Shapefile
    # --------------------------------------------------------
    # TODO: I'd love to abstract all this away but it's a pain to do this in a generic way
    log.info("Writing Shapefiles...")
    outShape = Shapefile()
    outShape.create(args.crosssections, rivershp.spatialRef, geoType=ogr.wkbLineString)

    featureDefn = outShape.layer.GetLayerDefn()

    field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
    outShape.layer.CreateField(field_defn)

    for idx, xs in enumerate(xsObjList):
        outFeature = ogr.Feature(featureDefn)
        ogrLine = ogr.CreateGeometryFromJson(json.dumps(mapping(xs.geometry)))
        outFeature.SetGeometry(ogrLine)
        outFeature.SetField("ID", idx)

        for metricName, metricValue in xs.metrics.iteritems():

            if featureDefn.GetFieldIndex(metricName) < 0:
                aField = ogr.FieldDefn(metricName, ogr.OFTReal)
                outShape.layer.CreateField(aField)

            outFeature.SetField(metricName, metricValue)

        outShape.layer.CreateFeature(outFeature)


    # --------------------------------------------------------
    # Do a little show and tell with plotting and whatnot
    # --------------------------------------------------------
    if not args.noviz:
        log.info("Plotting Results...")
        plt = Plotter()

        # The shape of the river is grey (this is the one with only qualifying islands
        plt.plotShape(rivershape, '#AAAAAA', 1, 5)

        # Centerline is black
        for c in centerlines:
            plt.plotShape(c['geometry'], '#000000', 0.5, 20)

        # Throwaway lines (the ones that are too whack to even test for validity) are faded red
        plt.plotShape(MultiLineString(throwaway), '#FF0000', 0.1, 20)

        # The valid crosssections are blue
        for g in xsObjList:
            plt.plotShape(g.geometry, '#0000FF', 0.7, 25)
        # Invalid crosssections are orange
        for g in xsObjList:
            plt.plotShape(g.geometry, '#00FF00', 0.7, 20)

        plt.showPlot(rivershape.bounds)


if __name__ == "__main__":

    log = Logger("Initializing")

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('river',
                        help='Path to the river shape file. Donuts will be ignored.',
                        type=argparse.FileType('r'))
    parser.add_argument('islands',
                        help='Path to the islands shapefile.',
                        type=argparse.FileType('r'))
    parser.add_argument('centerline',
                        help='Path to the centerline shapefile',
                        type=argparse.FileType('r'))
    parser.add_argument('dem',
                        help='Path to the DEM Raster (used for metric calculation)',
                        type=argparse.FileType('r'))
    parser.add_argument('crosssections',
                        help='Path to the desired output crosssections')
    parser.add_argument('--noviz',
                        help = 'Disable result visualization',
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    if not args.river or not args.centerline or not args.islands or not args.crosssections or not args.dem:
        print "ERROR: Missing arguments"
        parser.print_help()
        exit(0)

    log = Logger("Program")

    try:
        crosssections(args)
    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)


