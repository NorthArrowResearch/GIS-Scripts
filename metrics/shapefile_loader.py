import ogr
import json
from logger import Logger
from shapely.geometry import *

class Shapefile:

    def __init__(self, sFilename=None):
        self.driver = ogr.GetDriverByName("ESRI Shapefile")
        self.log = Logger('Shapefile')
        self.datasource = None
        if sFilename:
            self.load(sFilename)

    def load(self, sFilename):
        dataSource = self.driver.Open(sFilename, 0)
        self.layer = dataSource.GetLayer()
        self.spatialRef = self.layer.GetSpatialRef()

        self.getFieldDef()
        self.getFeatures()

    def getFieldDef(self):
        self.fields = {}
        lyrDefn = self.layer.GetLayerDefn()
        for i in range(lyrDefn.GetFieldCount()):
            fieldName = lyrDefn.GetFieldDefn(i).GetName()
            fieldTypeCode = lyrDefn.GetFieldDefn(i).GetType()
            fieldType = lyrDefn.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
            fieldWidth = lyrDefn.GetFieldDefn(i).GetWidth()
            GetPrecision = lyrDefn.GetFieldDefn(i).GetPrecision()

            self.fields[fieldName] = {
                'fieldName': fieldName,
                'fieldTypeCode': fieldTypeCode,
                'fieldType': fieldType,
                'fieldWidth': fieldWidth,
                'GetPrecision': GetPrecision
            }

    def attributesToList(self, desiredFields):
        if len(self.features) == 0:
            return

        feats = []
        for feat in self.features:
            fields = {}
            for aField in desiredFields:
                fields[aField] = feat.GetField(aField)

            feats.append(fields)
        return feats

    def getFeatures(self):

        self.features = []
        for feat in self.layer:
            self.features.append(feat)

    def featuresToShapely(self):
        if len(self.features) == 0:
            return

        feats = []
        for feat in self.features:
            featobj = json.loads(feat.ExportToJson())

            fields = {}
            for f in self.fields:
                fields[f] = feat.GetField(f)

            feats.append({
                'geometry': shape(featobj['geometry']),
                'fields': fields
            })
        return feats
