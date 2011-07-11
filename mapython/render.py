# coding: utf-8
import os
import sys
import math
import functools
import collections
import cairo
import numpy
from sqlalchemy import and_
from sqlalchemy.exc import InternalError
from shapely import wkb
from shapely.geometry import box
from shapely.ops import linemerge
import utils
from database import session, OSMPoint, OSMLine, OSMPolygon
from style import StyleSheet


GEOM_TYPES = {
    'point': OSMPoint,
    'line': OSMLine,
    'polygon': OSMPolygon
}
# style attributes that can access column values
COLUMN_ATTRS = ('text', )
DEFAULT_STYLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    'styles/default.yml')


class Renderer(object):
    
    '''
    Fetches data from database and renders a map.
    
    :param mapobj: :class:`mapython.draw.Map`
    :param stylesheet: :class:`mapython.style.StyleSheet`
    :param quiet: specify whether some status information is printed
    '''
    
    def __init__(
        self,
        mapobj,
        stylesheet=StyleSheet(DEFAULT_STYLE),
        quiet=False
    ):
        self.mapobj = mapobj
        self.stylesheet = stylesheet
        self.quiet = quiet
        self.conflict_list = []
        #: add a buffer of 0.05 % around actual bbox so every element
        #: is rendered - e.g. if it actually is outside of bbox but its width is
        #: big enough to intersect the visible map
        minx, miny, maxx, maxy = self.mapobj.bbox.bounds
        diffx = maxx - minx
        diffy = maxy - miny
        dilation = 0.0005 * math.sqrt(diffx ** 2 + diffy ** 2)
        self.bbox = self.mapobj.bbox.buffer(dilation, 1)
        self.verbose_print(
            'Zoomlevel:',
            self.stylesheet.get_level(self.mapobj.scale)
        )
                
    def run(self):
        '''
        Runs all rendering methods in the correct order and draws a complete
        map.
        '''
        self.mapobj.draw_background(self.stylesheet.map_background)
        self.coastlines()
        self.polygons()
        self.lines()
        self.points()
        self.conflicts()
        
    def verbose_print(self, *args):
        if not self.quiet:
            for msg in args:
                print msg,
            print
        
    def coastlines(self):
        '''Draws coastlines on the map.'''
        
        bbox_condition = """
            (%s.way && SetSRID('BOX3D(%s %s, %s %s)'::box3d, 4326))
        """
        coastlines = session.query(OSMLine).filter(and_(
            bbox_condition % ((OSMLine.__table__, ) + self.bbox.bounds),
            OSMLine.natural=='coastline'
        )).all()
        coastpolygons = session.query(OSMPolygon).filter(and_(
            bbox_condition % ((OSMPolygon.__table__, ) + self.bbox.bounds),
            OSMPolygon.natural=='coastline'
        )).all()
        if coastlines or coastpolygons:
            #: fill whole map with sea color
            self.mapobj.draw_background(self.stylesheet.sea_color)
            #: merge OSMLine's
            lines = []
            for cl in coastlines:
                lines.append(wkb.loads(str(cl.geom.geom_wkb)))
            merged = linemerge(lines)
            if merged.geom_type == 'LineString':
                merged = (merged, )
            else: # MultiLineString
                merged = tuple(merged)
            #: draw merged OSMLine's
            for cl in merged:
                self.mapobj.draw_polygon(
                    numpy.array(cl),
                    self.stylesheet.map_background
                )
            #: draw OSMPolygon's
            for cl in coastpolygons:
                self.mapobj.draw_polygon(
                    numpy.array(wkb.loads(str(cl.geom.geom_wkb)).exterior),
                    self.stylesheet.map_background
                )

    def polygons(self):
        '''Draws polygons on the map.'''
        
        results = self.query_objects('polygon')
        for polygons in results:
            for polygon in polygons:
                geom = wkb.loads(str(polygon.geom.geom_wkb))
                background_image = None
                if polygon.style.get('background-image') is not None:
                    background_image = os.path.join(self.stylesheet.dirname,
                        polygon.style.get('background-image'))
                self.mapobj.draw_polygon(
                    exterior=numpy.array(geom.exterior),
                    interiors=tuple(numpy.array(i) for i in geom.interiors),
                    background_color=polygon.style.get('background-color',
                        (0, 0, 0, 0)),
                    background_image=background_image,
                    border_width=polygon.style.get('border-width', 0),
                    border_color=polygon.style.get('border-color',
                        (0, 0, 0, 0)),
                    border_line_cap=polygon.style.get('border-line-cap',
                        cairo.LINE_CAP_ROUND),
                    border_line_join=polygon.style.get('border-line-join',
                        cairo.LINE_JOIN_ROUND),
                    border_line_dash=polygon.style.get('border-line-dash'),
                )
                if polygon.style.get('text') is not None:
                    self.conflict_list.append(polygon)

    def lines(self):
        '''Draws lines on the map.'''
        
        results = self.query_objects('line')
        for lines in results:
            #: draw outline
            for line in lines:
                # convert WKB to coordinate tuple once for all lines
                line.coords = numpy.array(wkb.loads(str(line.geom.geom_wkb)))
                if line.style.get('outline-width') is not None:
                    self.mapobj.draw_line(
                        coords=line.coords,
                        color=line.style.outline_color,
                        width=line.style.width + 2 * line.style.border_width \
                            + 2 * line.style.outline_width,
                        line_cap=line.style.get('outline-line-cap',
                            cairo.LINE_CAP_ROUND),
                        line_join=line.style.get('outline-line-join',
                            cairo.LINE_JOIN_ROUND),
                        line_dash=line.style.get('outline-line-dash')
                    )
            #: draw border as background so border-lines do not overlap
            for line in lines:
                if line.style.get('border-width') is not None:
                    self.mapobj.draw_line(
                        coords=line.coords,
                        color=line.style.border_color,
                        width=line.style.width + 2 * line.style.border_width,
                        line_cap=line.style.get('border-line-cap',
                            cairo.LINE_CAP_ROUND),
                        line_join=line.style.get('border-line-join',
                            cairo.LINE_JOIN_ROUND),
                        line_dash=line.style.get('border-line-dash')
                    )
            #: draw actual line
            for line in lines:
                self.mapobj.draw_line(
                    coords=line.coords,
                    color=line.style.color,
                    width=line.style.width,
                    line_cap=line.style.get('line-cap', cairo.LINE_CAP_ROUND),
                    line_join=line.style.get('line-join', cairo.LINE_JOIN_ROUND),
                    line_dash=line.style.get('line-dash')
                )
        #: draws line names in reversed order so lines with higher z-index will
        #: be rendered first
        for lines in reversed(results):
            for line in lines:
                if line.style.get('text') is not None:
                    self.conflict_list.append(line)
                
    def points(self):
        '''Draws points on the map.'''
        
        results = self.query_objects('point')
        for points in results:
            for point in points:
                if (
                    point.style.get('text') is not None
                    or point.style.get('image') is not None
                ):
                    self.conflict_list.append(point)
                    
    def conflicts(self):
        '''
        Draws all conflicting objects on the map. Conflicting objects are all
        objects which should not overlap in the final output, such as text or
        images. These objects are rendered in reverse order so objects with
        higher z-index are more likely drawn.
        '''
        # render text in reversed order so points are rendered before
        # lines before polygons
        for obj in reversed(self.conflict_list):
            geom = wkb.loads(str(obj.geom.geom_wkb))
            func = None
            if geom.geom_type == 'Point':
                if (
                    obj.style.get('text') is not None
                    and obj.style.get('image') is not None
                ):
                    func = functools.partial(
                        self.mapobj.draw_text,
                        coord=numpy.array(geom),
                        image=os.path.join(self.stylesheet.dirname,
                            obj.style.get('image')),
                        image_margin=obj.style.get('image-margin', 4)
                    )
                elif obj.style.get('text') is not None:
                    func = functools.partial(
                        self.mapobj.draw_text,
                        coord=numpy.array(geom)
                    )
                elif obj.style.get('image') is not None:
                    self.mapobj.draw_image(
                        numpy.array(geom),
                        os.path.join(self.stylesheet.dirname,
                            obj.style.get('image'))
                    )
            elif geom.geom_type == 'LineString':
                func = functools.partial(
                    self.mapobj.draw_text_on_line,
                    coords=numpy.array(geom)
                )
            else: # Polygon
                try:
                    func = functools.partial(
                        self.mapobj.draw_text,
                        coord=numpy.array(geom.representative_point())
                    )
                except ValueError: # geometry may be null value?
                    pass
            if func is not None:
                func(
                    text=getattr(obj, obj.style.text) or '',
                    color=obj.style.get('text-color', (0, 0, 0)),
                    font_size=obj.style.get('font-size', 10),
                    font_family=obj.style.get('font-family',
                        'Tahoma'),
                    font_style=obj.style.get('font-style', 'normal'),
                    font_stretch_style=obj.style.get('font-stretch-style',
                        'normal'),
                    font_weight=obj.style.get('font-weight', 'normal'),
                    text_border_width=obj.style.get('text-border-width', 1.5),
                    text_border_color=obj.style.get('text-border-color',
                        (0, 0, 0, 0)),
                    text_border_line_cap=obj.style.get('text-border-line-cap',
                        cairo.LINE_CAP_ROUND),
                    text_border_line_join=obj.style.get('text-border-line-join',
                        cairo.LINE_JOIN_ROUND),
                    text_border_line_dash=obj.style.get('text-border-line-dash'),
                    text_transform=obj.style.get('text-transform'),
                )
                
    def query_objects(self, geom_type):
        '''
        Returns all objects for current scale/geom_type as a 2-dimensional
        sorted list (according to z-index specified in stylesheet) and sets
        style as attribute to db objects.
        
        :param geom_type: one of ``'point'``, ``'line'`` or ``'polygon'``
        
        :returns: 2-dimensional list containing sorted objects
        '''
        # create 2-dimensional list so objects can be sorted (may be too many
        # sublists as there probably won't be as many z-index's defined as
        # MAX_Z_INDEX)
        results = [list() for _ in xrange(self.stylesheet.MAX_Z_INDEX)]
        # determine database model class
        db_class = GEOM_TYPES[geom_type]
        counter = 0
        # iterate over all visible tags and names
        for tags, columns, conditions in self.iter_query_conditions(geom_type):
            # simple st_intersects() does not work because this operation
            # raises an InternalError exception because of invalid geometries
            # in the OSM database
            bbox_condition = """
                (%s.way && SetSRID('BOX3D(%s %s, %s %s)'::box3d, 4326))
            """ % ((db_class.__table__, ) + self.bbox.bounds)
            objects = session.query(
                # only get necessary columns to save memory and reduce cpu usage
                db_class.geom,
                *[getattr(db_class, c) for c in tuple(tags) + tuple(columns)]
            ).filter(and_(bbox_condition, *conditions)).all()
            #: set style attr to obj and sort according to z-index
            for obj in objects:
                counter += 1
                tag_value = dict((tag, getattr(obj, tag)) for tag in tags)
                obj.style = self.stylesheet.get(self.mapobj.scale, geom_type,
                    tag_value)
                results[obj.style.get('z-index', 0)].append(obj)
        self.verbose_print('>  %s %ss' % (counter, geom_type))
        return results
        
    def iter_query_conditions(self, geom_type):
        '''
        Yields tags, columns and conditions for the current scale.
        
        :param geom_type: one of ``'point'``, ``'line'`` or ``'polygon'``
        
        :yields: ``[tags,]``, ``[columns,]``,
            ``[sqlalchemy binary expressions,]``
        '''
        db_class = GEOM_TYPES[geom_type]
        # only one condition so it can be combined with others to get better
        # performance
        simple_conds = collections.defaultdict(list)
        # multiple contitions
        complex_conds = []
        # columns which need to be fetched from database
        columns = collections.defaultdict(set)
        for style in self.stylesheet.iter_styles(self.mapobj.scale, geom_type):
            if len(style.tag_value) == 1:
                tag, value = style.tag_value.iteritems().next()
                simple_conds[tag].append(value)
                column_key = tag
            else:
                complex_conds.append(style.tag_value)
                column_key = utils.dict2key(style.tag_value)
            #: search for additional columns which need to be fetched from
            #: from database
            for attr in COLUMN_ATTRS:
                if style.get(attr) in db_class.__dict__:
                    columns[column_key].add(style.get(attr))
        for tag, names in simple_conds.iteritems():
            yield [tag], columns[tag], [getattr(db_class, tag).in_(names)]
        for conds in complex_conds:
            tags = []
            query_conds = []
            for key, value in conds.iteritems():
                tags.append(key)
                query_conds.append(getattr(db_class, key)==value)
            yield tags, columns[utils.dict2key(conds)], query_conds
            
