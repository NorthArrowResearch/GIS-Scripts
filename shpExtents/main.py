#!/usr/bin/env python

from osgeo import gdal, ogr
from os import path
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

def getExtents(feature):
    geometry = feature.GetGeometryRef()
    return geometry.GetEnvelope()

def union(oldExtents, newExtents):
    """
    Union two tuples representing a bounding triangle (x1, x2, y1, y2, n)
    n is the collected number of features in the extent (this is mostly for fun)
    :param oldExtents:
    :param newExtents:
    :return:
    """
    x1 = oldExtents[0] if oldExtents[0] < newExtents[0] else newExtents[0]
    x2 = oldExtents[1] if oldExtents[1] > newExtents[1] else newExtents[1]

    y1 = oldExtents[2] if oldExtents[2] < newExtents[2] else newExtents[2]
    y2 = oldExtents[3] if oldExtents[3] > newExtents[3] else newExtents[3]

    newN = oldExtents[4] + 1
    return (x1, x2, y1, y2, newN)

def getShapes(shpFile):
    """

    :param shpFile:
    :return:
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(shpFile, 0) # 0 means read-only. 1 means writeable.


    # Check to see if shapefile is found.
    if dataSource is None:
        print 'Could not open %s' % (shpFile)
        return

    print 'Opened %s' % (shpFile)
    layer = dataSource.GetLayer()

    print "Number of features in %s: %d" % (path.basename(shpFile), layer.GetFeatureCount())
    print "Number of layers in %s: %d" % (path.basename(shpFile), dataSource.GetLayerCount())

    layerDefinition = layer.GetLayerDefn()
    print "\nFields:\n---------------------------------"
    for i in range(layerDefinition.GetFieldCount()):
        print layerDefinition.GetFieldDefn(i).GetName()

    print "\nFeatures:\n---------------------------------"
    siteDict = {}
    for feat in layer:
        siteName = feat.GetField('Site')
        if siteName in siteDict:
            siteDict[siteName] = union(siteDict[siteName], getExtents(feat))
        else:
            siteDict[siteName] = getExtents(feat)
            # Tacking on a counter
            siteDict[siteName] = siteDict[siteName] + (1,)
        siteDict[siteName]

    print "Number of unique sites found: %d\n" % (len(siteDict))
    for site, extents in siteDict.iteritems():
        print "Site: %s, Features: %d, Extents: (%.2f,%.2f,%.2f,%.2f)" % (site, extents[4], extents[0], extents[1], extents[2], extents[3])

    return

def main():
    '''

    :return:
    '''
    # We're just iterating over a folder. Change this to something else if you want
    getShapes("ComputationExtents.shp")
    print "done"

if __name__ == "__main__":
    main()