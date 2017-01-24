import ogr
import json
from shapely.geometry import *
import matplotlib.pyplot as plt
import numpy as np

"""

    Tutorial 2: We're going to open a shape file then close it.

"""

sFilename = "inputs/Thalweg.shp"

driver = ogr.GetDriverByName("ESRI Shapefile")

dataSource = driver.Open(sFilename, 0)
layer = dataSource.GetLayer()
spatialRef = layer.GetSpatialRef()

rawfeatures = [feat for feat in layer]
features = []
for feat in rawfeatures:
    featobj = json.loads(feat.ExportToJson())

    fields = {}
    for f in fields:
        fields[f] = feat.GetField(f)

    features.append({
        'geometry': shape(featobj['geometry']),
        'fields': fields
    })

thalweg = features[0]['geometry']


thalweg2arr = np.array(thalweg.coords)
thalweg2arr[:,1] += 10
newthalweg = LineString(thalweg2arr)


# Some Plotting
fig = plt.figure(1, figsize=(10, 10))
ax = fig.gca()
ax.plot(*thalweg.xy, color='#FF0000', alpha=1, markersize=5, marker="o", zorder=10, label="Old Thalweg")
ax.plot(*newthalweg.xy, color='#00FF00', alpha=1, markersize=10, marker="o", zorder=10, label="New Thalweg")

plt.autoscale(enable=False)
plt.legend(loc='best')
plt.show()
plt.clf()
plt.close()

print "DONE"