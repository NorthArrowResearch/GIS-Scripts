import numpy as np

theArr = np.array([1, 2, 3, 4, 5])

maArr = np.ma.masked_greater_equal(theArr, 2)
print maArr
print "all: ", maArr.all()
print "count: ", np.ma.count_masked(maArr)
print "check: ", np.ma.count_masked(maArr) == maArr.size

maArr2 = np.ma.masked_greater_equal(theArr, 0)
print maArr2
print "all: ", maArr2.all()
print "count: ", np.ma.count_masked(maArr2)
print "check: ", np.ma.count_masked(maArr2) == maArr2.size

print maArr2.shape