import numpy as np

arSurvey = np.array([1,2,3,4,5,6,7,8,9, np.nan, 11, 12, -9999, 13])
arMinimu = np.array([1,1,3,1,np.nan,1,1,7,9, 9, np.nan,9, 12, -9999])

# Mask the survey and min surface where they are NaN
maSurvey = np.ma.masked_invalid(arSurvey)
maMinimu = np.ma.masked_invalid(arMinimu)

# Mask the survey and minimum surface where they are negative (-9999 used for raster NoData)
maSurvey = np.ma.masked_less(maSurvey, 0)
maMinimu = np.ma.masked_less(maMinimu, 0)

# Update each mask with the other's mask
maSurvey = np.ma.masked_array(maSurvey, maMinimu.mask)
maMinimu = np.ma.masked_array(maMinimu, maSurvey.mask)

# Calculation
maDiff = maSurvey - maMinimu
print "Survey: {0}".format(maSurvey)
print "Min   : {0}".format(maMinimu)
print "Diff  : {0}".format(maDiff)

print "Sum {0}, count = {1}".format(maDiff.sum(), maDiff.count())

