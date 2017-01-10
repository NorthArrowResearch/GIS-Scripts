---
title: Cross Section Metrics
---

This document describes the methods used to calculate cross section metrics. These metrics provide several common measurements that describe individual cross sections. These metrics can then be aggregated for an entire reach to provide summary metrics of the channel.

The history of these metrics is relevant because it has influenced both the list of metrics that are generated as well as the methods used.

Generating the metrics requires a channel polygon layer as a way of referencing the extent of the chnannel. Any polygon can be provided such that different water extents can be measured. 

In the case of the original cross section code, the channel polygon layer used to calculate metrics typically represented bankfull. Cross sections could extend beyond the channel polygon out onto the floodplain. Bankfull elevation was assumed to the average elevation of the two points where the cross sections intersected the channel polygon.

With the introduction of the [CHaMP](http://champmonitoring.org) in 2011, in 2011 the intent of the channel polygon was extended. CHaMP generates two sets of cross sections.

1. The first extend set of cross sections extend to the water extent observed during the topographic survey. This is referred to as the *wetted extent polygon* and the associated cross sections as the *wetted extent cross sections*.
2. The second set extend to a *bankfull polygon* that is a polygon layer derived by crews that best represents the bankfull extent of the channel. The cross sections derived from this polygon layer are called the "bankfull extent cross sections".

The following metric calculation methodologies should therefore be interpreted based on which polygon extent layer was used to derive the cross sections and whether the cross sections extend beyond the input channel polygon layer. In the case of CHaMP, the cross sections never extend beyond the channel polygon layer. Finally, each metric is calculated for an individual cross section. You should refer to the CHaMP metric documentation if you are interested in how these individual cross section methods are summarised for an entire reach.

![channel![channel](D:\Code\pyGISExperiments\crosssections\docs\channel.png)]



## Cross Section Length (`XSLength`)

The cross section length is the total length of the cross section line from the first point to the last. This value is the horizontal length and ignores elevation changes. It also ignores wet and dry patches.

* Data type is single
* Minimum value is zero.
* No maximum value.

## Dry Width (`Dry Width`)

This is the length of the cross section that passes over dry patches in the channel polygon. Dry patches are represented as donuts or holes in the polygon layer.

The dry length is the sum of all dry patches. It represents the horizontal length and ignores elevation changes.

* Data type is single.
* Minimum value is zero.
* No maximum value.

## Wetted Width (`WetWidth`)

This is the width of the channel that is within the channel polygon and not within a dry patch (island). It is the sum of the "wet" parts of the cross section. It represents the horizontal length and ignores elevation.

- Data type is single.
- Minimum value is zero.
- No maximum value.

## Max Depth (`MaxDepth`)

The max depth of the cross section represents the lowest point along the cross section. It is calculated by finding the average elevation of the end points of the cross section (i.e. the water surface elevation) and then subtracting the elevation of the lowest point along the cross section:

`MaxDepth = (IPoint1Elev + IPoint2Elev) / 2 - Min(StationElev)`

Where:

* `IPoint1Elev` = the absolute elevation of the point  where the start of the cross section touches the channel polygon.
* IPoint2Elev = the absolute elevation of the point where the end of the cross section touches the channel polygon.
* StationElev = the list of absolute elevations at user-specified increments along the cross section line.

## Width to Max Depth Ratio (`W2MxDepth`)

## Width to Average Depth Ratio (`W2AvDepth`)

## 

## 

## Mean Depth (`MeanDepth`)

## Wetted Perimeter (`WetPerim`)

## 

## IsValid (`IsValid`)

## Channel Type (`Channel`)

# CHaMP Related

## Elevation

## Sequence

## Distance

## Gradiant (`grad`)

# Older MetaData Attributes 

## Date (`Date`)

## Name (`Name`)

## Centerline (`CLine`)

## Digital Elevation Model (`DEM`)

## River Banks (`Banks`)

## Lateral Extension (`Extension`)

## Station Separation (`StatSep`)

## Number of Stations (`NumStat`)

## Bankfull Elevation (`BFElev`)

## Bankfull Area (`BFArea`)

## Hydraulic Radius (`HRadius`)


