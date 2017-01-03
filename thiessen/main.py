#!/usr/bin/env python
from ogrfunc import *
from vor import NARVoronoi
import numpy as np


class River:

    def __init__(self, sWetExtent, sThalweg):

        self.wetLayer = openlayer(sWetExtent)
        self.thalweg = openlayer(sThalweg)

        # Get our multipolygon shape
        feat = self.wetLayer.GetFeature(0)
        geom = feat.GetGeometryRef()

        # Add all the points (including islands) to the list
        self.riverPoints = []
        for idx in range(0, geom.GetGeometryCount()):
            ring = geom.GetGeometryRef(idx)
            for pt in ring.GetPoints():
                self.riverPoints.append(pt)

        self.extent = getEnvelope(self.wetLayer, 10)


def main():
    '''

    :return:
    '''

    # We're just iterating over a folder. Change this to something else if you want
    theRiver = River("sample/WettedExtent.shp", "sample/Thalweg.shp")
    vor = NARVoronoi(theRiver.riverPoints)
    vor.plot()

    print "done"

if __name__ == "__main__":
    main()


    #     AREA
# wkt = "POLYGON ((1162440.5712740074 672081.4332727483, 1162440.5712740074 647105.5431482664, 1195279.2416228633 647105.5431482664, 1195279.2416228633 672081.4332727483, 1162440.5712740074 672081.4332727483))"
# poly = ogr.CreateGeometryFromWkt(wkt)
# print "Area = %d" % poly.GetArea()
#
#
# wkts = [
#     "POINT (1198054.34 648493.09)",
#     "LINESTRING (1181866.263593049 615654.4222507705, 1205917.1207499576 623979.7189589312, 1227192.8790041457 643405.4112779726, 1224880.2965852122 665143.6860159477)",
#     "POLYGON ((1162440.5712740074 672081.4332727483, 1162440.5712740074 647105.5431482664, 1195279.2416228633 647105.5431482664, 1195279.2416228633 672081.4332727483, 1162440.5712740074 672081.4332727483))"
# ]
#
# for wkt in wkts:
#     geom = ogr.CreateGeometryFromWkt(wkt)
#     print geom.GetGeometryName()
#
#
# wkt1 = "POLYGON ((1208064.271243039 624154.6783778917, 1208064.271243039 601260.9785661874, 1231345.9998651114 601260.9785661874, 1231345.9998651114 624154.6783778917, 1208064.271243039 624154.6783778917))"
# wkt2 = "POLYGON ((1199915.6662253144 633079.3410163528, 1199915.6662253144 614453.958118695, 1219317.1067437078 614453.958118695, 1219317.1067437078 633079.3410163528, 1199915.6662253144 633079.3410163528)))"
#
# poly1 = ogr.CreateGeometryFromWkt(wkt1)
# poly2 = ogr.CreateGeometryFromWkt(wkt2)
#
# intersection = poly1.Intersection(poly2)
#
# print intersection.ExportToWkt()




# wkt1 = "POLYGON ((1208064.271243039 624154.6783778917, 1208064.271243039 601260.9785661874, 1231345.9998651114 601260.9785661874, 1231345.9998651114 624154.6783778917, 1208064.271243039 624154.6783778917))"
# wkt2 = "POLYGON ((1199915.6662253144 633079.3410163528, 1199915.6662253144 614453.958118695, 1219317.1067437078 614453.958118695, 1219317.1067437078 633079.3410163528, 1199915.6662253144 633079.3410163528)))"
#
# poly1 = ogr.CreateGeometryFromWkt(wkt1)
# poly2 = ogr.CreateGeometryFromWkt(wkt2)
#
# union = poly1.Union(poly2)
#
# print poly1
# print poly2
# print union.ExportToWkt()