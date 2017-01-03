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

def openlayer(file):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(file, 0)  # 0 means read-only. 1 means writeable.

    print 'Opened %s' % (file)
    return dataSource.GetLayer()

def getEnvelope(layer, buffer=0):

    extent = layer.GetExtent()
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(extent[0], extent[2])
    ring.AddPoint(extent[1], extent[2])
    ring.AddPoint(extent[1], extent[3])
    ring.AddPoint(extent[0], extent[3])
    ring.AddPoint(extent[0], extent[2])
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return "hello"