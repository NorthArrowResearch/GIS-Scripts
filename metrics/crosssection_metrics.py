import argparse
import sys

from logger import Logger
from shapes import *

def crosssection_metrics(args):

    clShp = Shapefile(args.crosssections.name)
    clList = clShp.featuresToShapely()

    dMetrics = {}

    return dMetrics

def crosssection_metrics_summary(dMetrics):



if __name__ == "__main__":

    log = Logger("Initializing")

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('crosssections',
                        help='Path to the cross section shapefile',
                        type=argparse.FileType('r'))
    args = parser.parse_args()

    if not args.centerline:
        print "ERROR: Missing arguments"
        parser.print_help()
        exit(0)

    log = Logger("Program")

    try:
        dMetrics = crosssection_metrics(args)
        crosssection_metrics_summary(dMetrics)

    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)
