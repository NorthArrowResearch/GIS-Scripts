#!/usr/bin/env python
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import fiona
from shapely.geometry import *
from shapes import *

class River:

    def __init__(self, sWetExtent, sCenterLine, sXS):
        source_driver = None
        source_crs = None
        source_schema = None
        shp = None
        with fiona.open(sWetExtent, 'r') as source:
            source_driver = source.driver
            source_crs = source.crs
            source_schema = source.schema
            shp = [shape(pol['geometry']) for pol in source]

        wet = MultiPolygon(shp)
        centerline = shape(fiona.open(sCenterLine, 'r')[0]['geometry'])

        # Get seedpoints at 50cm increments
        # Good time to get tangents too AND make the cross sections
        # by shooting 50m line outwards.
        seedpoints = getSeeds(centerline)

        # Intersect the ta




        # WRITE THE FILE
        # ==========================================
        # schema = {'geometry': 'MultiLineString', 'properties': {'name': 'str'}}
        # with fiona.collection(sCenterline, "w", driver=source_driver, crs=source_crs, schema=schema) as output:
        #     output.write({
        #         'properties': {
        #             'name': 'centerline'
        #         },
        #         'geometry': mapping(centerline)
        #     })






        # --------------------------------------------------------
        # Do a little show and tell with plotting and whatnot
        # --------------------------------------------------------
        fig = plt.figure(1, figsize=(10, 10))
        ax = fig.gca()

        # plotShape(ax, bankshapes[0], '#DDCCCC', 1, 0)
        # plotShape(ax, bankshapes[1], '#AAAABB', 1, 0)
        # plotShape(ax, wetBounds, 'b', 1, 0)
        # plotShape(ax, wet.envelope, 'b', 0.2, 2)

        plotShape(ax, wet, '#AACCAA', 0.2, 5)
        plotShape(ax, centerline, '#FFAABB', 1, 20)

        plt.autoscale(enable=True)
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
    theRiver = River("sample/WettedExtent.shp", "sample/centerline.shp", "output/crosssection.shp")
    # vor = NARVoronoi(theRiver.wet.points)
    # vor.plot()

    print "done"

if __name__ == "__main__":
    main()

