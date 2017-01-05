#!/usr/bin/env python
from vor import NARVoronoi
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from shapes import *
import fiona
from shapely.geometry import *

class River:

    def __init__(self, sWetExtent, sThalweg):

        wet = MultiPolygon([shape(pol['geometry']) for pol in fiona.open(sWetExtent, 'r')])
        # We're assuming here that the thalweg only has one line segment
        thalweg = MultiLineString([shape(line['geometry']) for line in fiona.open(sThalweg, 'r')])[0]

        # First and last line segment we need to extend
        thalwegStart = LineString([thalweg.coords[1], thalweg.coords[0]])
        thalwegEnd = LineString([thalweg.coords[-2], thalweg.coords[-1]])

        wetBounds = getBufferedBounds(wet, 10)

        # Now see where the lines intersect the rectangle
        thalwegStartExt = rectIntersect(thalwegStart, wetBounds)
        thalwegEndExt = rectIntersect(thalwegEnd, wetBounds)

        thalweglist = list(thalweg.coords)
        thalweglist.insert(0, thalwegStartExt.coords[1])
        thalweglist.append(thalwegEndExt.coords[1])

        newThalweg = LineString(thalweglist)

        # Now split clockwise to get left and right bank
        bankshapes = splitClockwise(wetBounds, newThalweg)

        # Add all the points (including islands) to the list
        points = []
        leftpts = []
        rightpts = []

        for pol in wet:
            pts = list(pol.exterior.coords)
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
        myVorL.collectCenterLines(leftpts, rightpts)

        # Do a little show and tell with plotting and whatnot
        # --------------------------------------------------------
        fig = plt.figure(1, figsize=(10, 10))
        ax = fig.gca()

        plotShape(ax, bankshapes[0], '#DDCCCC', 1, 0)
        plotShape(ax, bankshapes[1], '#AAAABB', 1, 0)
        # plotShape(ax, wetBounds, 'b', 1, 0)
        # plotShape(ax, wet.envelope, 'b', 0.2, 2)

        plotShape(ax, wet, '#AACCAA', 0.2, 5)

        # plotShape(ax, MultiPoint(points), 'r', 1, 10)
        plotShape(ax, MultiPoint(leftpts), 'r', 1, 10)
        plotShape(ax, MultiPoint(rightpts), 'b', 1, 10)
        plotShape(ax, newThalweg, 'r', 1, 10)
        plotShape(ax, thalweg, 'g', 1, 14)

        plt.autoscale(enable=True)
        plt.show()


def plotShape(ax, mp, color, alpha, zord):
    # We're using Descartes here for polygonpathc
    if mp.type == 'Polygon':
        ax.add_patch(PolygonPatch(mp, fc=color, ec='#000000', lw=0.2, alpha=alpha, zorder=zord))

    elif mp.type == 'LineString':
        x, y = mp.xy
        ax.plot(x, y, color=color, alpha=alpha, linewidth=3, solid_capstyle='round', zorder=zord)

    elif mp.type == 'MultiPoint':
        for idx, p in enumerate(mp):
            x, y = p.xy
            ax.plot(x, y, color=color, alpha=alpha, markersize=2, marker=".", zorder=zord)

    elif mp.type == 'MultiLineString':
        for idx, p in enumerate(mp):
            x, y = p.xy
            ax.plot(x, y, color=color, alpha=alpha, linewidth=3, solid_capstyle='round', zorder=zord)

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
    theRiver = River("sample/WettedExtent.shp", "sample/Thalweg.shp")
    # vor = NARVoronoi(theRiver.wet.points)
    # vor.plot()

    print "done"

if __name__ == "__main__":
    main()

