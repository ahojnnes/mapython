# coding: utf-8
import unittest
import tempfile
import os
import StringIO
import cairo
from shapely.geometry import box

import mapython.draw


PLACES = 9

ICON = """iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAQAAADZc7J/AAAAAmJLR0QAAKqNIzIAAAAJcEhZcwAA
HK8AAByvAZ7yuRcAAAAJdnBBZwAAACAAAAAgAIf6nJ0AAAIeSURBVEjHrZVPaBNBFIe/2SSbxnpI
LbWISC0aG/G/B8FTEa2CiAoqCiJ4qQgiHrx78epFvApeerLmUJFKUZBe0lZEIwW9WJAKjfSgEtqk
ZLfzeug27mw3ic36HnPY3Xnf/N6btzOQZpACS+gNeonXDGDDXb6hkRbcYZx+xXd6aNUchhUa1TIA
ZqxI4dBuRQoHiQog7n9QNOMt1wckyXKULmINwh2KfGAGdz0gxVVukyVl1FS8obyhWeQTTxjFMQEW
p3hAL5qyIbKNZG3tCoKinZN0Ms+ECUhziZ0I73hBpaZB2MdNuoAyw4yjgQyD7OcCBSo+nZKRvIgs
yX2xjGbtkykREfkhZ7w3PZIXkRHpXpszZwHYtDXdLn9tUiSCRVRAgrNUAin0AtDJdXYgCLvZFcDF
/9bbop9jaN9KSa+IKa5xEQnVajRSjM11Ekj4RJv2f1pZG8JXrcw0X4hxiL3YzQAlfq4LH+ItW3EZ
5QrnAwmIr93iAPPkOMx235Qp3nCDLDDBc/ZwwAB0cIRt/GKW5VWAQw7NObq97RFGyJLhIVu4Q54c
fwL6LuPylWf8XtuFEkO8ZFMNUOYeLkUcQPOYpwZAYaGosuDNDvUTMikfZVrG5GCjk3lOIeHVTXKc
Aaq8ohByjNSsWBcAYCO+Pz8cEG/0tUpzi9qJymqUwj/YosVshHCH9zE0faRbup9cJnkEHdziM9UN
380LjHEaewVIlxj5M6YPzwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxMC0wMS0wNVQxOTozNDo0Ny0w
NzowMFcyxLQAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMTAtMDEtMDVUMTk6MzQ6NDctMDc6MDAmb3wI
AAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAABJRU5ErkJggg=="""


class MapTestCase(unittest.TestCase):

    def setUp(self):
        self.bbox = (11, 45.5, 11.232, 45.7)
        self.tempfile = tempfile.TemporaryFile()
        self.map = mapython.draw.Map(self.tempfile, self.bbox, 800)

    def tearDown(self):
        self.map.write()
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
        self.assertIsNone(self.map.find_free_position(new, step=1, number=5))
        new = box(30, 30, 50, 30)
        self.assertEqual(self.map.find_free_position(new, number=0), (30, 30))

    def test_draw(self):
        self.map.draw_background((0, 0, 0, 1))
        self.map.draw_line(
            coords=((11, 45.5), (11.1, 45.6), (11.2, 45.65)),
            color=(1, 1, 1, 0.5),
            width=3,
            line_cap=cairo.LINE_CAP_SQUARE,
            line_join=cairo.LINE_JOIN_ROUND,
            line_dash=(3, 4, 2)
        )
        self.map.draw_polygon(
            exterior=((11, 45.5), (11.1, 45.6), (11.2, 45.65), (11, 45.5)),
            interiors=(
                ((11.1, 45.6), (11.12, 45.6), (11.14, 45.65), (11.1, 45.6)),
            ),
            background_color=(1, 1, 1, 0.5),
            border_width=1,
            border_color=(1, 1, 1, 1),
            border_line_cap=cairo.LINE_CAP_ROUND,
            border_line_join=cairo.LINE_JOIN_ROUND,
            border_line_dash=None
        )
        self.map.draw_arc(
            coord=(11.2, 45.6),
            radius=20,
            angle1=1,
            angle2=3,
            background_color=(0, 0, 0, 0),
            background_image=None,
            border_width=0,
            border_color=(1, 1, 1, 1),
            border_line_cap=cairo.LINE_CAP_ROUND,
            border_line_join=cairo.LINE_JOIN_ROUND,
            border_line_dash=(3, 4, 2)
        )
        self.map.draw_text(
            coord=(11.2, 45.6),
            text='TEST',
            color=(0, 0, 0),
            font_size=11,
            font_family='Tahoma',
            font_style=cairo.FONT_SLANT_NORMAL,
            font_weight=cairo.FONT_WEIGHT_NORMAL,
            text_halo_width=4,
            text_halo_color=(1, 1, 1, 0.5),
            text_halo_line_cap=cairo.LINE_CAP_ROUND,
            text_halo_line_join=cairo.LINE_JOIN_ROUND,
            text_halo_line_dash=None,
            text_transform=None,
        )
        self.map.draw_text(
            coord=(11.2, 45.6),
            text='TEST',
            color=(0, 0, 0),
            font_size=11,
            font_family='Tahoma',
            font_style=cairo.FONT_SLANT_NORMAL,
            font_weight=cairo.FONT_WEIGHT_NORMAL,
            text_halo_width=4,
            text_halo_color=(1, 1, 1, 0.5),
            text_halo_line_cap=cairo.LINE_CAP_ROUND,
            text_halo_line_join=cairo.LINE_JOIN_ROUND,
            text_halo_line_dash=None,
            text_transform=None,
            image=StringIO.StringIO(ICON.decode('base64')),
            image_margin=4
        )
        self.map.draw_text_on_line(
            coords=((11, 45.5), (11.232, 45.7)),
            text='Test Street 123a',
            color=(0, 0, 0),
            font_size=10,
            font_family='Tahoma',
            font_style=cairo.FONT_SLANT_NORMAL,
            font_weight=cairo.FONT_WEIGHT_NORMAL,
            text_halo_width=1,
            text_halo_color=(1, 1, 1),
            text_halo_line_cap=cairo.LINE_CAP_ROUND,
            text_halo_line_join=cairo.LINE_JOIN_ROUND,
            text_halo_line_dash=None,
            text_transform=None,
        )
        self.map.draw_image((11.2, 45.6),
            StringIO.StringIO(ICON.decode('base64')))


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MapTestCase)
