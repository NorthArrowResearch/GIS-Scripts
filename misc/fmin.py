import numpy as np

arr1 = np.array([1, 2, 9, 4, 5])
arr2 = np.array([2, 3, 4, 5, 6])

arr3 = np.fmin(arr1, arr2)
print arr3

arr4 = np.array([1, 2, 9, np.nan, 5])
arr5 = np.fmin(arr2, arr4)
print arr5
