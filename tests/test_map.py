# coding: utf-8
import unittest
import tempfile

from shapely.geometry import box

import mapython.draw


PLACES = 9


class MapTestCase(unittest.TestCase):

    def setUp(self):
        self.bbox = (11, 45.5, 11.232, 45.7)
        self.tempfile = tempfile.TemporaryFile()
        self.map = mapython.draw.Map(tempfile.TemporaryFile(), self.bbox, 800)

    def tearDown(self):
        self.tempfile.close()

    def test_projection(self):
        coord = (self.bbox[0], self.bbox[1])
        #: correct projection and inverse projection
        coord_proj = self.map.projection(*self.map.projection(*coord),
            inverse=True)
        self.assertAlmostEqual(coord[0], coord_proj[0], places=PLACES)
        self.assertAlmostEqual(coord[1], coord_proj[1], places=PLACES)
        #: correct transformation to pixel/point and vice versa
        coord_center = (self.bbox[0], self.bbox[3])
        self.assertEqual((0, 0), self.map.transform_coords(*coord_center))
        coord_transf = self.map.transform_coords_inverse(
            *self.map.transform_coords(*coord))
        self.assertAlmostEqual(coord[0], coord_transf[0], places=PLACES)
        self.assertAlmostEqual(coord[1], coord_transf[1], places=PLACES)
        # correct orientation of map coordinate system
        self.assertEqual((self.map.x0, self.map.y0),
            self.map.projection(self.bbox[0], self.bbox[3]))

    def test_conflicts(self):
        conflict = box(0, 0, 20, 20)
        self.map.conflict_union(conflict, margin=0)
        #: correct calculation of conflict density
        self.assertEqual(self.map.conflict_density(10, 10, radius=10), 1)
        self.assertEqual(self.map.conflict_density(50, 50, radius=10), 0)
        self.assertAlmostEqual(self.map.conflict_density(10, 20, radius=10),
            0.5, places=PLACES)
        #: test positioning
        new = box(10, 10, 50, 30)
        self.assertEqual(self.map.find_free_position(new, step=1, number=10),
            (10, 20))
        self.assertEqual(self.map.find_free_position(new, step=1, number=5),
            None)
        new = box(30, 30, 50, 30)
        self.assertEqual(self.map.find_free_position(new, number=0), (30, 30))


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MapTestCase)
