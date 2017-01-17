import argparse
import sys

from logger import Logger
from shapefile_loader import *
import numpy as np

# There are various ways of summarizing the attributes of a dictionary:
# best - this is a way of picking one of the other three methods.
#       it's intended to be the version of the metric that other tools use.
#       For example, some metrics will use the "crew" version as the best metric
#       while others will use the "auto" filtered as the best.
# auto - includes cross sections that have a width that is within 4 StDev
#       of the mean width
# none - includes all cross sections
# crew - uses the IsValid flag on the original dictionary

def crosssection_metrics(args):

    # Build a dictionary of attributes that require metrics.
    # The key is the cross section ShapeFile attribute field name.
    # The value is the type of filtering that will be used to report
    # the "best" metrics (possible values are "crew", "auto", "none")
    dMetricTypes = {'WetWidth': 'crew', 'W2MxDepth': 'crew', 'W2AvDepth' :'crew'}

    # Save space by only loading the desired fields from the ShapeFile.
    # We also need the 'Channel' and 'IsValid' fields if they exist.
    desiredFields = dMetricTypes.keys()
    desiredFields.append('Channel')
    desiredFields.append('IsValid')

    # Open the cross section ShapeFile & build a list of all features with a dictionary of the desired fields
    clShp = Shapefile(args.crosssections.name)
    allFeatures = clShp.attributesToList(desiredFields)

    # For simple ShapeFiles, make every feature part of the main channel, and
    # set every feature as valid. This helps keep code below generic
    for x in allFeatures:
        if 'Channel' not in x:
            x['Channel'] = 'Main'

        if 'IsValid' not in x:
            x['IsValid'] = 1

    dMetrics = {}
    for channelName in ['Main', 'Side']:

        dMetrics[channelName] = {}

        # Filter the list of features to just those in this channel
        channelFeatures = [x for x in allFeatures if x['Channel'].lower() == channelName.lower()]

        # Filter the list of features to just those that the crew considered valid
        validFeatures = [x for x in channelFeatures if x['IsValid'] <> 0]

        # Filter the features to just those with a length that is within 4 standard deviations of mean wetted width
        channelStatistics = getStatistics(channelFeatures, 'WetWidth')
        wetWidthThreshold = channelStatistics['standard_deviation'] * 4
        autoFeatures = [x for x in channelFeatures if abs(x['WetWidth'] - channelStatistics['mean']) < wetWidthThreshold]

        # Loop over each desired metric and calculate the statistics for each filtering type
        for metricName, bestFiltering in dMetricTypes.iteritems():
            populateChannelStatistics(dMetrics[channelName], 'none', metricName, channelFeatures)
            populateChannelStatistics(dMetrics[channelName], 'crew', metricName, validFeatures)
            populateChannelStatistics(dMetrics[channelName], 'auto', metricName, autoFeatures)
            dMetrics[channelName]['best'] = dMetrics[channelName][bestFiltering]

    # The metrics for the whole channel are always the results for 'Main'.
    # For complex ShapeFiles this will be just the results for the main channel.
    # For simple, single threaded, ShapeFiles this will all cross sections.
    dMetrics['Channel'] = dMetrics['Main']

    return dMetrics

def populateChannelStatistics(dChannelMetrics, filteringName, metricName, featureList):

    if not filteringName in dChannelMetrics:
        dChannelMetrics[filteringName] = {}

    dChannelMetrics[filteringName][metricName] = getStatistics(featureList, metricName)

def getStatistics(lFeatures, sAttribute):

    lValues = [x[sAttribute] for x in lFeatures]
    dStatistics = {}

    fSum = sum(lValues)
    dStatistics['count'] = len(lValues)
    dStatistics['mean'] = np.mean(lValues)
    dStatistics['minimum'] = min(lValues)
    dStatistics['maximum'] = max(lValues)
    dStatistics['standard_deviation'] = np.std(lValues)
    dStatistics['coefficient_of_variation'] = dStatistics['standard_deviation'] / dStatistics['mean']

    return dStatistics

if __name__ == "__main__":

    log = Logger("Initializing")

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('crosssections',
                        help='Path to the cross section shapefile',
                        type=argparse.FileType('r'))
    args = parser.parse_args()

    if not args.crosssections:
        print "ERROR: Missing arguments"
        parser.print_help()
        exit(0)

    log = Logger("Program")

    try:
        dMetrics = crosssection_metrics(args)
        #crosssection_metrics_summary(dMetrics)

    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)
