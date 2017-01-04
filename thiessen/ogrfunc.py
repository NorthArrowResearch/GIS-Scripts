from osgeo import gdal, ogr, osr

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()
ogr.UseExceptions()
class pt:

    def __init__(self, pt):
        self.pt = pt
        self.angle = 0
        print "hello"

def ptInShape(point, polygon):
    """
    This is kind of rough but it's the right idea
    :param point:
    :param polygon:
    :return:
    """
    spatialReference = osr.SpatialReference()
    spatialReference.SetWellKnownGeogCS("WGS84")
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.AssignSpatialReference()
    return pt.Within(polygon)


class ShapeFile:

    def __init__(self, file):
        driver = ogr.GetDriverByName('ESRI Shapefile')
        dataSource = driver.Open(file, 0)  # 0 means read-only. 1 means writeable.

        print 'Opened %s' % (file)

        # Get our multipolygon shape and some useful objects
        self.layer = dataSource.GetLayer()
        self.feature = self.layer.GetFeature(0)
        self.geometry = self.feature.GetGeometryRef()
        self.extent = self.layer.GetExtent()
        self.geocount = self.geometry.GetGeometryCount()

        # Add all the points (including islands) to the list
        self.points = []

        # Make a handy array of points
        for idx in range(0, self.geocount):
            ring = self.geometry.GetGeometryRef(idx)
            for pt in ring.GetPoints():
                self.points.append(pt)

def getEnvelope(extent, buffer=0):

    newExtent = (extent[0] -buffer, extent[1] + buffer, extent[2] - buffer, extent[3] + buffer)

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(newExtent[0], newExtent[2])
    ring.AddPoint(newExtent[1], newExtent[2])
    ring.AddPoint(newExtent[1], newExtent[3])
    ring.AddPoint(newExtent[0], newExtent[3])
    ring.AddPoint(newExtent[0], newExtent[2])

    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly