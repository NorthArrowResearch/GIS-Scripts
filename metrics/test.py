import unittest


class crosssection_test(unittest.TestCase):

    def test_crosssection_getStatistics(self):
        from crosssection_metrics import getStatistics

        lFeatures = []
        lFeatures.append({'WetWidth': 0  , 'W2MxDepth' : 0, 'W2AvDepth' : 0 })
        lFeatures.append({'WetWidth': 2.0, 'W2MxDepth' : 2.0, 'W2AvDepth' : 2.0 })
        dMetrics = getStatistics(lFeatures, 'WetWidth')

        self.assertEqual(dMetrics['mean'], 1.0)



