import argparse
import sys

from logger import Logger
from shapefile_loader import *

"""
<centerline>
    <parts>
        <part>
        <id>1</id>
        <type>Main</type>
        <length>214.73</length>
        <sinuosity>1.30</sinuosity>
        </part>
    </parts>
    <summary>
        <channel_count units="0.0####">1</channel_count>
        <mainstem_count units="0.0####">1</mainstem_count>
        <mainstem_length>214.72919</mainstem_length>
        <total_channel_length>214.72919</total_channel_length>
        <average_side_channel_length></average_side_channel_length>
        <channel_type>complex</channel_type>
        <side_channel_count units="0.0####">0</side_channel_count>
        <side_channel_length>0.0</side_channel_length>
        <braidedness>1.0</braidedness>
    </summary>
</centerline>
"""

def centerline_metrics(args):

    clShp = Shapefile(args.centerline.name)
    clList = clShp.featuresToShapely()

    dMetrics = {}

    for aLine in clList:

        lineID = aLine['fields']["ID"]
        curvedLength = aLine['geometry'].length
        firstPoint = Point(aLine['geometry'].coords[0])
        lastPoint = Point(aLine['geometry'].coords[-1])
        straightLength = firstPoint.distance(lastPoint)

        dMetrics[lineID] = {}
        dMetrics[lineID]['type'] = aLine['fields']['Channel']
        dMetrics[lineID]['length'] = curvedLength
        dMetrics[lineID]['sinuosity'] = curvedLength / straightLength

    return dMetrics

def centerline_summary_metrics(dMetrics):

    lMainParts = [x for x in dMetrics.itervalues() if x['type'] == 'Main']
    lSideParts = [x for x in dMetrics.itervalues() if x['type'] != 'Main']

    dSummary = {}
    dSummary['channel_count'] = len([x for x in dMetrics.itervalues()])
    dSummary['mainstem_count']= len(lMainParts)
    dSummary['side_channel_count'] = len(lSideParts)
    dSummary['mainstem_length'] = sum([fLen['length'] for fLen in lMainParts])
    dSummary['side_channel_length'] = sum([fLen['length'] for fLen in lSideParts])
    dSummary['total_channel_length'] = dSummary['mainstem_length'] + dSummary['side_channel_length']
    dSummary['average_side_channel_length'] = dSummary['total_channel_length']  / dSummary['channel_count']

    dSummary['braidedness'] = (dSummary['mainstem_length'] + dSummary['side_channel_length']) / dSummary['mainstem_length']

    if len(dMetrics) > 1:
        dSummary['channel_type'] = 'complex'
    else:
        dSummary['channel_type'] = 'simple'

if __name__ == "__main__":

    log = Logger("Initializing")

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('centerline',
                        help='Path to the centerline shapefile',
                        type=argparse.FileType('r'))
    args = parser.parse_args()

    if not args.centerline:
        print "ERROR: Missing arguments"
        parser.print_help()
        exit(0)

    log = Logger("Program")

    try:
        dMetrics = centerline_metrics(args)
        centerline_summary_metrics(dMetrics)

    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)
