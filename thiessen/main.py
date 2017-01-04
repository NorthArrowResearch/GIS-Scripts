#!/usr/bin/env python
from ogrfunc import *
from vor import NARVoronoi
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import fiona
from shapely import wkt, geometry
from shapely.geometry import Polygon, MultiPolygon, MultiLineString, shape, LineString
import json
import numpy as np


class River:

    def __init__(self, sWetExtent, sThalweg):

        wet = MultiPolygon([shape(pol['geometry']) for pol in fiona.open(sWetExtent, 'r')])
        thalweg = MultiLineString([shape(line['geometry']) for line in fiona.open(sThalweg, 'r')])

        # Do a little show and tell with plotting and whatnot
        # --------------------------------------------------------
        fig = plt.figure(1, figsize=(10, 10))
        ax = fig.gca()

        plotShape(ax, wet.envelope, 'b', 'b')
        plotShape(ax, wet, 'r', 'r')
        plotShape(ax, thalweg, 'g', 'g')
        plt.autoscale(enable=True)
        plt.show()

def getExtrapoledLine(p1,p2):
    'Creates a line extrapoled in p1->p2 direction'
    EXTRAPOL_RATIO = 10
    a = p1
    b = (p1[0]+EXTRAPOL_RATIO*(p2[0]-p1[0]), p1[1]+EXTRAPOL_RATIO*(p2[1]-p1[1]) )
    return LineString([a,b])

def plotShape(ax, mp, ptcolor, shapecolor):
    if mp.type == 'Polygon':
        ax.add_patch(PolygonPatch(mp, fc=shapecolor, ec=ptcolor, lw=0.2, alpha=0.2, zorder=1))

    elif mp.type == 'MultiLineString':
        patches = []
        for idx, p in enumerate(mp):
            x, y = p.xy
            ax.plot(x, y, color=ptcolor, alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)

    elif mp.type == 'MultiPolygon':
        patches = []
        for idx, p in enumerate(mp):
            patches.append(PolygonPatch(p, fc=shapecolor, ec=ptcolor, lw=0.2, alpha=0.2, zorder=1))
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

