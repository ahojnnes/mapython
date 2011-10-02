# coding: utf-8
import unittest
import yaml
import StringIO
import cairo

from mapython import style


STYLESHEET = '''
ZOOMLEVELS:
    0: [0, 1]
    1: [1, 2]
    2: [2, 4]
    3: [4, 8]
    4: [8, 16]

MAP_BACKGROUND: 1 1 1 0
SEA_BACKGROUND: 1 0 1 0

POINT:
    place:
        city:
            - all:
                text: name
                text-color: 0 0 0
                font-size: 7
                text-halo-color: 1 1 1 0.88
                text-halo-width: 1.5
                z-index: 99
            - 2-3:
                font-weight: bold
                font-size: 12
            - 1, 2:
                font-size: 13
            - 0:
                text-color: 0 0 0
                font-size: 14

LINE:
    highway:
        motorway:
            - all:
                text: name
'''


class StyleTestCase(unittest.TestCase):

    def setUp(self):
        self.stylesheet = style.StyleSheet(StringIO.StringIO(STYLESHEET))

    def test_zoomlevels(self):
        self.assertEqual(len(self.stylesheet.zoomlevels), 5)
        self.assertEqual(self.stylesheet.get_level(0.5), 0)
        self.assertEqual(self.stylesheet.get_level(8), 4)
        self.assertIsNone(self.stylesheet.get_level(16))

    def test_background(self):
        self.assertListEqual(self.stylesheet.map_background, [1, 1, 1, 0])
        self.assertListEqual(self.stylesheet.sea_background, [1, 0, 1, 0])

    def test_get(self):
        self.assertEqual(
            self.stylesheet.get(0.5, 'point', {'place': 'city'})['font-size'],
            14
        )
        self.assertEqual(
            self.stylesheet.get(0.5, 'point', {'place': 'city'})['text'],
            'name'
        )
        self.assertEqual(
            self.stylesheet.get(4, 'point', {'place': 'city'})['font-weight'],
            cairo.FONT_WEIGHT_BOLD
        )
        self.assertEqual(self.stylesheet.get(10, 'line',
            {'highway': 'motorway'})['text'], 'name')
        self.assertIsNone(self.stylesheet.get(1000, 'line',
            {'highway': 'motorway'}))
        self.assertIsNone(self.stylesheet.get(10, 'line', {'foo': 'bar'}))

    def test_update(self):
        s = self.stylesheet.get(10, 'line', {'highway': 'motorway'})
        s['font-size'] = 15
        self.assertEqual(self.stylesheet.get(10, 'line',
            {'highway': 'motorway'})['font-size'], 15)
        s = style.Style('point', 0, {'place': 'town'},
            {'text-color': [0, 0, 0]})
        self.stylesheet.update(s)
        self.assertListEqual(self.stylesheet.get(0.5, 'point',
            {'place': 'town'})['text-color'], [0, 0, 0])
        s['font-size'] = 15
        self.stylesheet.update(s)
        self.assertEqual(
            self.stylesheet.get(0.5, 'point', {'place': 'town'})['font-size'],
            15
        )

    def test_iter(self):
        self.assertEqual(len(list(self.stylesheet.iter_styles(0, 'point'))), 1)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(StyleTestCase)
