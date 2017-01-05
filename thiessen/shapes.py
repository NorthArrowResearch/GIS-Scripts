import math
import numpy as np
from shapely.geometry import *

def getBufferedBounds(shape, buffer):
    """
    Get the bounds of a shape and extend them by some arbitrary buffer
    :param shape:
    :param buffer:
    :return:
    """
    newExtent = (shape.bounds[0] - buffer, shape.bounds[1] - buffer, shape.bounds[2] + buffer, shape.bounds[3] + buffer)

    return Polygon([
        (newExtent[0], newExtent[1]),
        (newExtent[2], newExtent[1]),
        (newExtent[2], newExtent[3]),
        (newExtent[0], newExtent[3]),
        (newExtent[0], newExtent[1])
    ])

def getDiag(rect):
    """
    return the biggest possible distance inside a rectangle (the diagonal)
    :param rect: rectangle polygon
    :return:
    """
    return math.sqrt(
        math.pow((rect.bounds[3] - rect.bounds[1]), 2) +
        math.pow((rect.bounds[2] - rect.bounds[0]), 2))

def rectIntersect(line, poly):
    """
    Return the intersection point between a line segment and a polygon
    :param line: Note, the direction is important so we use a list of tuples
    :param poly:
    :return:
    """
    diag = getDiag(poly)
    longLine = getExtrapoledLine(line, diag)
    return poly.intersection(longLine)


def getExtrapoledLine(line, length):
    """
    Creates a line extrapoled in p1->p2 direction' by an arbitrary length
    :param line:
    :param length:
    :return:
    """
    p1 = line.coords[0]
    p2 = line.coords[1]

    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    k = length / math.sqrt(1 + math.pow(m, 2))

    if  (p2[1] - p1[1]) < 0 and  (p2[0] - p1[0]) < 0:
        k = k * -1

    # It could be +/- k so we have to try both
    newX = p1[0] + k
    newY = p1[1] + k*m

    test = LineString([p2, (newX, newY)])
    test1 = LineString([p1, (newX, newY)])

    return LineString([p2, (newX, newY)])

def splitClockwise(rect, thalweg):
    """
    Work clockwise around a rectangle and create two shapes that represent left and right bank
    :param rect:
    :param thalweg:
    :return:
    """
    # The thalweg has two points we care about:
    thalwegStart = thalweg.coords[0]
    thalwegEnd = thalweg.coords[-1]

    coordsorter = list(rect.exterior.coords)
    coordsorter.append(thalwegStart)
    coordsorter.append(thalwegEnd)

    # Sort the points clockwise
    def algo(pt):
        return math.atan2(pt[0] - rect.centroid.coords[0][0], pt[1] - rect.centroid.coords[0][1]);
    coordsorter.sort(key=algo)

    shape1 = []
    shape2 = []
    shape1idx = 0
    shape2idx = 0

    firstshape = True

    # Calculate shape 1 and shape 2 by traversal
    for idx, pt in enumerate(coordsorter):
        if pt == thalwegStart:
            shape1idx = len(shape1)
            shape2idx = len(shape2)
            firstshape = not firstshape
        elif pt == thalwegEnd:
            firstshape = not firstshape

        elif firstshape:
            shape1.append(pt)
        elif not firstshape:
            shape2.append(pt)

    shape1[shape1idx:shape1idx] = reversed(list(thalweg.coords))
    shape2[shape2idx:shape2idx] = list(thalweg.coords)
    return MultiPolygon([Polygon(shape1) , Polygon(shape2)])