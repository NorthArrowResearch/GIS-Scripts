# Philip Bailey
# 25th July 2016
# Experimenting with NumPy to see how it can accomplish
# the array math for the GCMRC sandbar analysis
#########################################################################################

import numpy as np
import RasterAnalysis

#########################################################################################
# Section 1: Some simple proof of concept calculations

x = np.array([[0,1,2,3,4,5,6,7,8,9], \
	[1,2,3,4,5,6,7,8,9,0]])

nSum = np.sum(x)
print "Sum of all values in array {0}".format(nSum)

nConSum = np.sum(x[x > 5])
print "Sum of all values gt 5 is {0}".format(nConSum)

nConSum2 = np.sum(x[(x > 5) & (x < 7)])
print "Sum of all values gt 5 and lt 7 is {0}".format(nConSum2)

nCount = ((5 < x) & (x < 7)).sum()
print "Numer of cells greater than 5 and lt 7 is {0}".format(nCount)
#
#########################################################################################
# Below are two surfaces. One is mean to represent an elevation
# surface and the other a minimum surface.

aSurvey = np.array([ \
	[1,2,4,4,4,8,8,9,9,9], \
	[4,4,4,4,5,5,9,9,9,9]])

aMinSurf = np.array([ \
	[1,1,2,3,4,5,6,7,8,9], \
	[1,2,3,4,5,5,7,8,9,9]])

nSum2 = np.sum(aSurvey[aSurvey > aMinSurf] - aMinSurf[aSurvey > aMinSurf])
print "Sum of survery above minimum surface {0}".format(nSum2)

fAbsMin = np.nanmin(aMinSurf)
print "The absolute minimum elevation of the minimum surface is {0}".format(fAbsMin)

fSurveyMax = np.nanmax(aSurvey)
print "The maximum elevation of the survey is {0}".format(fSurveyMax)

nBinSize = 1
fCellSize = 0.2 ** 2

lElevs =[]
dVolumes = {}
dAreas = {}
dCounts = {}

for fElev in range(fAbsMin, fSurveyMax, nBinSize):
	lElevs.append(fElev)

	nBinSum = np.sum(aSurvey[aSurvey > fElev] - aMinSurf[aSurvey > fElev])
	dVolumes[fElev] = nBinSum
	dCounts[fElev] = (aSurvey > fElev).sum()
	dAreas[fElev] = dCounts[fElev] * fCellSize

print "The elevation bins being considered are: ", lElevs
print "The volumes are: ", dVolumes
print "The areas are: ", dAreas
print "The counts are: ", dCounts

aSurvey = np.array([ \
	[1.0,8.0,4.0,4.0,4.0,8.0,8.0,9.0,9.0,np.nan], \
	[4.0,4.0,4.0,4.0,5.0,5.0,9.0,9.0,9.0,9.0]])

aMinSurf = np.array([ \
	[1.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,np.nan], \
	[1.0,2.0,3.0,4.0,5.0,5.0,7.0,8.0,9.0,9.0]])

tAV = RasterAnalysis.getVolumeAndArea(aSurvey, aMinSurf, None, 7,1)
print tAV

