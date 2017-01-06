#!/usr/bin/env python
from vor import NARVoronoi
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from shapes import *
import ogr
import json
import os
from shapely.geometry import *

class River:

    def __init__(self, sRiverShape, sThalweg, sCenterline):
        # Open the file and extract the shapes we need
        # TODO: This is begging for a little abstraction
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(sRiverShape, 0)
        spatialRef = dataSource.GetLayer().GetSpatialRef()
        riverjson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']

        rivershape = MultiPolygon([shape(riverjson)])

        # We're assuming here that the thalweg only has one line segment
        dataSource = driver.Open(sThalweg, 0)


        thalwegjson = json.loads(dataSource.GetLayer().GetFeature(0).ExportToJson())['geometry']
        thalweg = LineString(shape(thalwegjson))

        # First and last line segment we need to extend
        thalwegStart = LineString([thalweg.coords[1], thalweg.coords[0]])
        thalwegEnd = LineString([thalweg.coords[-2], thalweg.coords[-1]])

        rivershapeBounds = getBufferedBounds(rivershape, 10)

        # Now see where the lines intersect the rectangle
        thalwegStartExt = rectIntersect(thalwegStart, rivershapeBounds)
        thalwegEndExt = rectIntersect(thalwegEnd, rivershapeBounds)

        # Now make a new thalweg by adding the extension points to the start
        # and end points of the original
        thalweglist = list(thalweg.coords)
        thalweglist.insert(0, thalwegStartExt.coords[1])
        thalweglist.append(thalwegEndExt.coords[1])

        newThalweg = LineString(thalweglist)

        # Now split clockwise to get left and right envelopes
        bankshapes = splitClockwise(rivershapeBounds, newThalweg)

        # Add all the points (including islands) to one of three lists
        points = []
        leftpts = []
        rightpts = []

        for pol in rivershape:
            # Exterior is the shell
            pts = list(pol.exterior.coords)
            # Interiors are the islands
            for interior in pol.interiors:
                pts = pts + list(interior.coords)
            for pt in pts:
                points.append(pt)
                if bankshapes[0].contains(Point(pt)):
                    leftpts.append(pt)
                else:
                    rightpts.append(pt)

        # Here's where the Voronoi polygons come into play
        myVorL = NARVoronoi(MultiPoint(points))
        # myVorL.plot()
        myVorL.createshapes() # optional. Makes the polygons we will use to visualize
        centerline = myVorL.collectCenterLines(leftpts, rightpts)

        schema = {'geometry': 'MultiLineString', 'properties': {'name': 'str'}}

        if os.path.exists(sCenterline):
            driver.DeleteDataSource(sCenterline)
        outDataSource = driver.CreateDataSource(sCenterline)
        outLayer = outDataSource.CreateLayer(sCenterline, spatialRef, geom_type=ogr.wkbMultiLineString)

        ogrmultiline = ogr.CreateGeometryFromJson(json.dumps(mapping(centerline)))

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

        plotShape(ax, bankshapes[0], '#DDCCCC', 1, 0)
        plotShape(ax, bankshapes[1], '#AAAABB', 1, 0)

        plotShape(ax, myVorL.polys, '#444444', 0.2, 6)

        plotShape(ax, rivershape, '#AACCAA', 0.2, 8)

        plotShape(ax, MultiPoint(leftpts), '#FF0000', 0.8, 10)
        plotShape(ax, MultiPoint(rightpts), '#0000FF', 0.8, 10)

        plotShape(ax, newThalweg, '#FFA500', 0.5, 15)
        plotShape(ax, thalweg, '#00FF00', 0.8, 20)

        plotShape(ax, centerline, '#FF0000', 0.8, 30)

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
    theRiver = River("sample/WettedExtent.shp", "sample/Thalweg.shp", "output/centerline.shp")
    # vor = NARVoronoi(theRiver.wet.points)
    # vor.plot()

    print "done"

if __name__ == "__main__":
    main()

