import numpy as np
from RasterAnalysis import getVolumeAndArea

# Imagine the survey array below represents a single survey point in time.
# The minimum array is the minimum surface across all surveys to a site.

Elev8k = 4
CellSize = 2

rawSurvey = np.array([1,2,3,4,5,6,7,8,9, np.nan, 11, 12, -9999, 13])
rawMin = np.array([1,1,3,1,np.nan,1,1,7,9, 9, np.nan,9, 12, -9999])

# prepare the two arrays

aSurveyBF = rawSurvey[~(np.isnan(rawSurvey) | np.isnan(rawMin))]
theMinBF = rawMin[~(np.isnan(rawSurvey) | np.isnan(rawMin))]

# print "Prep {0} values {1}".format(aSurveyBF.size, aSurveyBF)
# print "PMin {0} values {1}".format(theMinBF.size, theMinBF)

aSurvey = aSurveyBF[(aSurveyBF > 0) & (theMinBF > 0)]
theMin = theMinBF[(aSurveyBF > 0) & (theMinBF > 0)]

# print "Prep {0} values {1}".format(aSurvey.size, aSurvey)
# print "PMin {0} values {1}".format(theMin.size, theMin)

# Set any elevations above the 8k elevation to the 8k elevation itself
aSurvey[aSurvey > Elev8k] = Elev8k
theMin[theMin > Elev8k] = Elev8k

print "Capped suvey: {0}".format(aSurvey)
print "Capped min surface: {0}".format(theMin)

diff = aSurvey - theMin
print "Difference: {0}".format(diff)

fdiff = diff.sum()
fVol = fdiff * CellSize**2
print "Sum is {0} and volume is {1}".format(fdiff, fVol)

nCount = diff[diff > 0].size
fArea = nCount * CellSize**2
print "Count is {0} and area is {1}".format(nCount, fArea)

tAreaVol = getVolumeAndArea(rawSurvey, rawMin, None, 4, 2)
print "Area {0} Vol {1}".format(tAreaVol[0], tAreaVol[1])