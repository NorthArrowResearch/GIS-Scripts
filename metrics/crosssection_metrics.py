import argparse
import sys

from logger import Logger
from shapes import *

# <bankfull_main_channel_width_to_avg_depth>
# <statistics>
# <filtering>none</filtering>
# <minimum>9.38902</minimum>
# <maximum>94.01464</maximum>
# <mean>33.61416</mean>
# <count>424.0</count>
# <standard_deviation>17.17037</standard_deviation>
# <coefficient_of_variation>0.51081</coefficient_of_variation>
# </statistics>
# <statistics>
# <filtering>auto</filtering>
# <minimum>9.38902</minimum>
# <maximum>94.01464</maximum>
# <mean>32.92049</mean>
# <count>418.0</count>
# <standard_deviation>16.28005</standard_deviation>
# <coefficient_of_variation>0.49453</coefficient_of_variation>
# </statistics>
# <statistics>
# <filtering>crew</filtering>
# <minimum>9.38902</minimum>
# <maximum>94.01464</maximum>
# <mean>31.17858</mean>
# <count>392.0</count>
# <standard_deviation>15.10823</standard_deviation>
# <coefficient_of_variation>0.48457</coefficient_of_variation>
# </statistics>
# <statistics>
# <filtering>best</filtering>
# <minimum>9.38902</minimum>
# <maximum>94.01464</maximum>
# <mean>31.17858</mean>
# <count>392.0</count>
# <standard_deviation>15.10823</standard_deviation>
# <coefficient_of_variation>0.48457</coefficient_of_variation>
# </statistics>
# </bankfull_main_channel_width_to_avg_depth>

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
    # We will need the 'Channel' and 'IsValid' fields if they exist
    desiredFields = dMetricTypes.keys()
    desiredFields.append('Channel')
    desiredFields.append('IsValid')

    # Open the cross section ShapeFile and build a list of all features and the desired fields
    clShp = Shapefile(args.crosssections.name)
    allFeatures = clShp.attributesToList(desiredFields)

    # Build a dictionary of the different channel types.
    # The 'Main' and 'Side' are simple attribute based filters.
    # For simple cross sections (no 'Channel' attribute) the 'Channel' type includes all features.
    # For complex cross sections ('Channel' attribute present) the 'Channel' type includes only 'Main'
    sAllChannel = 'Main'
    if allFeatures[0]['Channel'] == None:
        sAllChannel = None
    dChannelTypes = {'Main': 'Main', 'Side': 'Side', 'Channel': sAllChannel}

    dMetrics = {}
    for sChannelType, sValueFilter in dChannelTypes.iteritems():
        dMetrics[sChannelType] = {}

        # Filter the list of features to just those in this channel
        channelFeatures = []
        if sValueFilter is None:
            channelFeatures = allFeatures
        else:
            channelFeatures = [x for x in allFeatures if x['Channel'].lower() == sValueFilter.lower()]

        # Get the list of features in this channel that the crew consider valid
        validFeatures = [x for x in channelFeatures if x['IsValid'] <> 0]

        # The channel statistics for the wetted width are used to do 'auto' filtering
        channelStatistics = getStatistics(channelFeatures, 'WetWidth')

        # Get the list of features within x standard deviations of the mean
        # that will be used for auto filtering
        wetWidthThreshold = channelStatistics['standard_deviation'] * 4
        autoFeatures = [x for x in channelFeatures if abs(x['WetWidth'] - channelStatistics['mean']) < wetWidthThreshold]

        for aMetric in dMetricTypes:
            populateChannelStatistics(dMetrics[sChannelType], 'none', aMetric, channelFeatures)
            populateChannelStatistics(dMetrics[sChannelType], 'crew', aMetric, validFeatures)
            populateChannelStatistics(dMetrics[sChannelType], 'auto', aMetric, autoFeatures)
            dMetrics[sChannelType]['best'] = dMetrics[sChannelType]['crew']

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
    dStatistics['mean'] = fSum / float(dStatistics['count'])
    dStatistics['minimum'] = min(lValues)
    dStatistics['maximum'] = max(lValues)

    # Standard deviation is the average distance of each point from the mean
    sumOfDiff = 0
    for aVal in lValues:
        sumOfDiff += abs(aVal - dStatistics['mean'])
    dStatistics['standard_deviation'] = sumOfDiff / float(dStatistics['count'])

    # Coefficient of variation is the StDev / Mean
    dStatistics['coefficient_of_variation'] = dStatistics['standard_deviation'] / dStatistics['mean']

    return dStatistics

# def filterFeatures(sAttributeName, attributeValue, features):
#
#     dResult = [x for x in features if x[sAttributeName].lower() == attributeValue.lower()]
#     return dResult

# def crosssection_metrics_summary(dMetrics):



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
