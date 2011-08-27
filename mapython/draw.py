# coding: utf-8
import math
import cairo
import numpy
from shapely.geometry import Point, LineString, Polygon, box
import projection
import utils


class Map(object):
    
    '''
    Creates drawable map object which can be rendered.
    
    :param fobj: a filename or writable file object
    :param bbox: iterable containing the max extents of the map in the
        following form: (minlon, minlat, maxlon, maxlat)
    :param max_size: max map width/height in pixel/point according to
        surface_type
    :param projection: projection function for drawing the map,
        should return (x, y) in metres. Some functions are predefined in
        :mod:`mapython.projection`
    :param surface_type: must be one of png, pdf, ps or svg
    '''
    
    SURFACE_TYPES = {
        # 'png':cairo.ImageSurface, => needs special treatment
        'pdf': cairo.PDFSurface,
        'ps': cairo.PSSurface,
        'svg': cairo.SVGSurface,
    }
    # margin around conflicting objects that may not overlap (text, icons etc.)
    CONFLICT_MARGIN = 3
    
    def __init__(
        self,
        fobj,
        bbox,
        max_size=800,
        proj=projection.mercator,
        surface_type='png',
    ):
        self.fobj = fobj
        self.bbox = box(*bbox)
        self.max_size = max_size
        self.surface_type = surface_type
        # projection can't be integrated in matrix because projection is not
        # necessarily linear
        self.projection = proj
        # inits: self.x_diff, self.y_diff, self.x0, self.y0
        self._init_coord_system()
        # inits: self.width, self.height, self.surface
        self._init_surface()
        # inits: self.m2unit_matrix, self.unit2m_matrix, self.scale
        self._init_transformation()
        self.context = cairo.Context(self.surface)
        self.map_area = box(0, 0, self.width, self.height)
        self.conflict_area = Polygon(
            # buffer around map where no text should be drawn
            self.map_area.buffer(99999).exterior,
            # map hole where text can be drawn
            [self.map_area.exterior]
        )
                
    def _init_coord_system(self):
        minlon, minlat, maxlon, maxlat = self.bbox.bounds
        #: convert to metres
        minx, miny = self.projection(minlon, minlat)
        maxx, maxy = self.projection(maxlon, maxlat)
        #: calculate map size in metres
        self.x_diff = abs(maxx - minx)
        self.y_diff = abs(maxy - miny)
        #: orientate coord system
        self.x0, self.y0 = minx, miny
        #: determine coordinate center x0 and y0
        if minx > maxx:
            self.x0 = maxx
        if miny < maxy:
            self.y0 = maxy
            
    def _init_surface(self):
        #: calculate surface size in unit
        if self.x_diff > self.y_diff:
            self.width = self.max_size
            self.height = int(math.ceil(self.max_size / self.x_diff *
                                         self.y_diff))
        else:
            self.width = int(math.ceil(self.max_size / self.y_diff *
                                        self.x_diff))
            self.height = self.max_size
        #: init surface object according to surface_type
        if self.SURFACE_TYPES.get(self.surface_type) is not None:
            surface_cls = self.SURFACE_TYPES.get(self.surface_type)
            self.surface = surface_cls(self.fobj, self.width, self.height)
        #: fall back to png as default type
        else:
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width,
                self.height)
                
    def _init_transformation(self):
        x_scale = self.width / self.x_diff # unit per metre
        y_scale = self.height / self.y_diff # unit per metre
        #: transformation matrix to convert from metres to unit
        self.m2unit_matrix = cairo.Matrix(xx=x_scale, yy=y_scale)
        #: transformation matrix to convert from unit to metres
        #: NOTE: copy.copy or copy.deepcopy of m2unit_matrix does not work
        self.unit2m_matrix = cairo.Matrix(xx=x_scale, yy=y_scale)
        self.unit2m_matrix.invert()
        #: determine average metres per px => scale
        dist = self.unit2m_matrix.transform_distance(math.sqrt(0.5),
            math.sqrt(0.5))
        self.scale = sum(dist) / 2
        
    def draw_background(self, color):
        '''
        Fills the whole map with color.
        
        :param color: ``(r, g, b[, a])``
        '''
        
        self.context.rectangle(0, 0, self.width, self.height)
        self.context.set_source_rgba(*color)
        self.context.fill()
        
    def draw_line(
        self,
        coords,
        color=(0, 0, 0),
        width=1,
        line_cap=cairo.LINE_CAP_ROUND,
        line_join=cairo.LINE_JOIN_ROUND,
        line_dash=None
    ):
        '''
        Draws a line.
        
        :param coords: iterable containing all coordinates as ``(lon, lat)``
        :param color: ``(r, g, b[, a])``
        :param width: line-width in unit (pixel/point)
        :param line_cap: one of :const:`cairo.LINE_CAP_*`
        :param line_join: one of :const:`cairo.LINE_JOIN_*`
        :param line_dash: list/tuple used by :meth:`cairo.Context.set_dash`
        '''
        
        #: move to first coords
        x, y = self.transform_coords(*coords[0])
        self.context.move_to(x, y)
        #: draw line to rest of coords
        for lon, lat in coords[1:]:
            x, y = self.transform_coords(lon, lat)
            self.context.line_to(x, y)
        #: fill line with color
        self.context.set_source_rgba(*color)
        self.context.set_line_width(width)
        self.context.set_line_cap(line_cap)
        self.context.set_line_join(line_join)
        self.context.set_dash(line_dash or tuple())
        self.context.stroke()
        
    def draw_polygon(
        self, 
        exterior,
        interiors=None,
        background_color=(0, 0, 0, 0),
        background_image=None,
        border_width=0,
        border_color=(1, 1, 1, 1),
        border_line_cap=cairo.LINE_CAP_ROUND,
        border_line_join=cairo.LINE_JOIN_ROUND,
        border_line_dash=None,
    ):
        '''
        Draws a polygon.
        
        :param exterior: iterable containing all exterior coordinates as
            ``(lon, lat)``
        :param interiors: list/tuple with separate iterables containing 
            coordinates of the holes of the polygon as ``(lon, lat)``
        :param background_color: ``(r, g, b[, a])``
        :param background_image: file object or path to image file
        :param border_width: border-width in unit (pixel/point)
        :param border_color: ``(r, g, b[, a])``
        :param border_line_cap: one of :const:`cairo.LINE_CAP_*`
        :param border_line_join: one of :const:`cairo.LINE_JOIN_*`
        :param border_line_dash: list/tuple used by
            :meth:`cairo.Context.set_dash`
        '''
        
        polygons = (exterior, )
        if interiors is not None:
            polygons += interiors
        for coords in polygons:
            #: move to first coords
            x, y = self.transform_coords(*coords[0])
            self.context.move_to(x, y)
            #: draw line to rest of coords
            for lon, lat in coords[1:]:
                x, y = self.transform_coords(lon, lat)
                self.context.line_to(x, y)
        #: fill polygon with color [and background]
        self.context.set_source_rgba(*background_color)
        if background_image is not None:
            self.context.fill_preserve()
            image = cairo.ImageSurface.create_from_png(background_image)
            pattern = cairo.SurfacePattern(image)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            self.context.set_source(pattern)
        self.context.fill_preserve()
        #: draw border
        self.context.set_source_rgba(*border_color)
        self.context.set_line_width(border_width)
        self.context.set_line_cap(border_line_cap)
        self.context.set_line_join(border_line_join)
        self.context.set_dash(border_line_dash or tuple())
        self.context.stroke()

    def draw_arc(
        self,
        coord,
        radius,
        angle1=0,
        angle2=2*math.pi,
        background_color=(0, 0, 0, 0),
        background_image=None,
        border_width=0,
        border_color=(1, 1, 1, 1),
        border_line_cap=cairo.LINE_CAP_ROUND,
        border_line_join=cairo.LINE_JOIN_ROUND,
        border_line_dash=None
    ):
        '''
        Draws an arc. Angles are counted from the positive X axis
        to the positive Y axis.
        
        :param coord: ``(lon, lat)``
        :param radius: as float in unit (pixel/point)
        :param angle1: start angle in radians [0, 2pi]
        :param angle2: end angle in radians [0, 2pi]
        :param background_color: ``(r, g, b[, a])``
        :param background_image: file object or path to image file
        :param border_width: border-width in unit (pixel/point)
        :param border_color: ``(r, g, b[, a])``
        :param border_line_cap: one of :const:`cairo.LINE_CAP_*`
        :param border_line_join: one of :const:`cairo.LINE_JOIN_*`
        :param border_line_dash: list/tuple used by
            :meth:`cairo.Context.set_dash`
        '''

        x, y = self.transform_coords(*coord)
        #: draw circle
        circle = (angle1 - angle2) % (2 * math.pi) == 0
        if not circle:
            self.context.move_to(x, y)
        self.context.arc(x, y, radius, angle1, angle2)
        if not circle:
            self.context.close_path()
        #: fill arc with color [and background]
        self.context.set_source_rgba(*background_color)
        if background_image is not None:
            self.context.fill_preserve()
            image = cairo.ImageSurface.create_from_png(background_image)
            pattern = cairo.SurfacePattern(image)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            self.context.set_source(pattern)
        self.context.fill_preserve()
        #: draw border
        self.context.set_source_rgba(*border_color)
        self.context.set_line_width(border_width)
        self.context.set_line_cap(border_line_cap)
        self.context.set_line_join(border_line_join)
        self.context.set_dash(border_line_dash or tuple())
        self.context.stroke()

    def draw_text(
        self,
        coord,
        text,
        color=(0, 0, 0),
        font_size=11,
        font_family='Tahoma',
        font_style=cairo.FONT_SLANT_NORMAL,
        font_weight=cairo.FONT_WEIGHT_NORMAL,
        text_halo_width=3,
        text_halo_color=(1, 1, 1),
        text_halo_line_cap=cairo.LINE_CAP_ROUND,
        text_halo_line_join=cairo.LINE_JOIN_ROUND,
        text_halo_line_dash=None,
        text_transform=None,
        image=None,
        image_margin=4
    ):
        '''
        Draws text either centered on coordinate or the image centered on
        coordinate and text on the right of the image.
        
        :param coord: ``(lon, lat)``
        :param text: text to be drawn
        :param color: ``(r, g, b[, a])``
        :param font_size: font-size in unit (pixel/point)
        :param font_family: font name
        :param font_style: ``cairo.FONT_SLANT_NORMAL``,
            ``cairo.FONT_SLANT_ITALIC`` or ``cairo.FONT_SLANT_OBLIQUE``
        :param font_weight: ``cairo.FONT_WEIGHT_NORMAL`` or 
            ``cairo.FONT_WEIGHT_BOLD``
        :param text_halo_width: border-width in unit (pixel/point)
        :param text_halo_color: ``(r, g, b[, a])``
        :param text_halo_line_cap: one of :const:`cairo.LINE_CAP_*`
        :param text_halo_line_join: one of :const:`cairo.LINE_JOIN_*`
        :param text_halo_line_dash: list/tuple used by
            :meth:`cairo.Context.set_dash`
        :param text_transform: one of ``'lowercase'``, ``'uppercase'`` or
            ``'capitalize'``
        :param image: file object or path to image file
        :param image_margin: space between text and image in int or float
        '''
        
        x, y = self.transform_coords(*coord)
        # abort if there are already too many text_paths in this area
        if self.conflict_density(x, y) > 1:
            self.context.new_path()
            return
        text = utils.text_transform(text, text_transform)
        #: draw spot name
        self.context.select_font_face(font_family, font_style, font_weight)
        self.context.set_font_size(font_size)
        width, height = self.context.text_extents(text)[2:4]
        if image is not None:
            image = cairo.ImageSurface.create_from_png(image)
            image_width, image_height = image.get_width(), image.get_height()
            text_area = box(
                x - image_width / 2.0,
                y - max(height, image_height) / 2.0,
                x + image_width + width + image_margin,
                y + max(height, image_height) / 2.0
            )
        else:
            # place text directly on coord
            x -= width / 2.0
            text_area = box(
                x - 2,
                y - height / 2. - 2,
                x + 2 + width,
                y + height / 2. + 2
            )
        try:
            newx, newy = self.find_free_position(text_area)
        except TypeError: # no free position found
            self.context.new_path()
            return
        if image is not None:
            y = newy + (max(height, image_height) - image_height) / 2.0
            self.context.set_source_surface(image, newx, y)
            self.context.paint()
            image_area = box(x, y, x + image_width, y + image_height)
            newx += image_width + image_margin
            newy += (image_height + height) / 2.0
        else:
            # find_free_position uses minx and miny as position but 
            # cairo uses bottom left corner
            newx, newy = newx, newy + height + 2
        # abort if new position is too far away from original position
        if Point(newx, newy).distance(Point(x, y)) > 0.1 * self.max_size:
            self.context.new_path()
            return
        # round positions for clear text rendering
        self.context.move_to(int(newx), int(newy))
        self.context.text_path(text)
        #: draw text halo
        self.context.set_line_cap(cairo.LINE_CAP_ROUND)
        self.context.set_source_rgba(*text_halo_color)
        self.context.set_line_width(2 * text_halo_width)
        self.context.set_line_cap(text_halo_line_cap)
        self.context.set_line_join(text_halo_line_join)
        self.context.set_dash(text_halo_line_dash or tuple())
        self.context.stroke_preserve()
        #: determine covered area by text
        area = box(*self.context.path_extents())
        if image is not None:
            area = area.union(image_area.buffer(self.CONFLICT_MARGIN, 1))
        try:
            self.conflict_area = self.conflict_area.union(
                area.buffer(self.CONFLICT_MARGIN, 1))
        except ValueError: # empty geometry
            pass
        #: fill characters with color
        self.context.set_source_rgba(*color)
        self.context.fill()
        
    def draw_text_on_line(
        self,
        coords,
        text,
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
    ):
        '''
        Draws text on a line. Tries to find a position with the least change
        in gradient and which is closest to the middle of the line.
        
        :param coords: iterable containing all coordinates as ``(lon, lat)``
        :param text: text to be drawn
        :param color: ``(r, g, b[, a])``
        :param font_size: font-size in unit (pixel/point)
        :param font_family: font name
        :param font_style: ``cairo.FONT_SLANT_NORMAL``,
            ``cairo.FONT_SLANT_ITALIC`` or ``cairo.FONT_SLANT_OBLIQUE``
        :param font_weight: ``cairo.FONT_WEIGHT_NORMAL`` or 
            ``cairo.FONT_WEIGHT_BOLD``
        :param text_halo_width: border-width in unit (pixel/point)
        :param text_halo_color: ``(r, g, b[, a])``
        :param text_halo_line_cap: one of :const:`cairo.LINE_CAP_*`
        :param text_halo_line_join: one of :const:`cairo.LINE_JOIN_*`
        :param text_halo_line_dash: list/tuple used by
            :meth:`cairo.Context.set_dash`
        :param text_transform: one of ``'lowercase'``, ``'uppercase'`` or
            ``'capitalize'``
        '''
        
        text = text.strip()
        if not text:
            return
        coords = map(lambda c: self.transform_coords(*c), coords)
        
        self.context.select_font_face(font_family, font_style, font_weight)
        self.context.set_font_size(font_size)
        text = utils.text_transform(text, text_transform)
        width, height = self.context.text_extents(text)[2:4]
        font_ascent, font_descent = self.context.font_extents()[0:2]
        self.context.new_path()
        #: make sure line does not intersect other conflict objects
        line = LineString(coords)
        line = line.difference(self.map_area.exterior.buffer(height))
        line = line.difference(self.conflict_area)
        #: check whether line is empty or is split into several different parts
        if line.geom_type == 'GeometryCollection':
            return
        elif line.geom_type == 'MultiLineString':
            longest = None
            min_len = width * 1.2
            for seg in line.geoms:
                seg_len = seg.length
                if seg_len > min_len:
                    longest = seg
                    min_len = seg_len
            if longest is None:
                return
            line = longest
        coords = tuple(line.coords)
        seg = utils.linestring_text_optimal_segment(coords, width)
        # line has either to much change in gradients or is too short
        if seg is None:
            return
        #: crop optimal segment of linestring
        start, end = seg
        coords = coords[start:end+1]
        #: make sure text is rendered from left to right
        if coords[-1][0] < coords[0][0]:
            coords = tuple(reversed(coords))
        # translate linestring so text is rendered vertically in the middle
        line = LineString(tuple(coords))
        offset = font_ascent / 2. - font_descent
        line = line.parallel_offset(offset, 'left', resolution=3)
        # make sure text is rendered centered on line
        start_len = (line.length - width) / 2.
        char_coords = None
        chars = utils.generate_char_geoms(self.context, text)
        #: draw all character paths
        for char in utils.iter_chars_on_line(chars, line, start_len):
            for geom in char.geoms:
                char_coords = iter(geom.coords)
                self.context.move_to(*char_coords.next())
                for lon, lat in char_coords:
                    self.context.line_to(lon, lat)
                self.context.close_path()
        #: only add line to reserved area if text was drawn
        if char_coords is not None:
            covered = line.buffer(height + self.CONFLICT_MARGIN)
            self.conflict_area = self.conflict_area.union(covered)
        #: draw border around characters
        self.context.set_line_cap(cairo.LINE_CAP_ROUND)
        self.context.set_source_rgba(*text_halo_color)
        self.context.set_line_width(2 * text_halo_width)
        self.context.set_line_cap(text_halo_line_cap)
        self.context.set_line_join(text_halo_line_join)
        self.context.set_dash(text_halo_line_dash or tuple())
        self.context.stroke_preserve()
        #: fill actual text
        self.context.set_source_rgba(*color)
        self.context.fill()
        
    def draw_image(self, coord, image):
        '''
        Draws an image at given position (centered). Only supports pngs so far.
        
        :param coord: ``(lon, lat)``
        :param image: file object or path to image file
        '''
        
        image = cairo.ImageSurface.create_from_png(image)
        x, y = self.transform_coords(*coord)
        width, height = image.get_width(), image.get_height()
        # display centered
        x -= width / 2.0
        y -= height / 2.0
        newpos = self.find_free_position(
            box(x - 2, y - 2, x + width + 2, y + height + 2)
        )
        if newpos is None:
            return
        self.context.set_source_surface(image, x, y)
        self.context.paint()
        self.conflict_area = self.conflict_area.union(
            box(x, y, x + width, y + height))
            
    def transform_coords(self, lon, lat):
        '''
        Transforms from ``(lon, lat)`` to ``(x, y)`` in unit (pixel or point).
        
        :param lon: longitude in degree
        :param lat: latitude in degree
        
        :returns: (x, y) tuple in unit (pixel or point)
        '''
        
        x, y = self.projection(lon, lat)
        x_rel, y_rel = x - self.x0, self.y0 - y
        return self.m2unit_matrix.transform_point(x_rel, y_rel)
        
    def transform_coords_inverse(self, x, y):
        '''
        Transforms from ``(x, y)`` in unit (pixel or point) to ``(lon, lat)``.
        
        :param x: in unit (pixel or point)
        :param y: in unit (pixel or point)
        
        :returns: (lon, lat) tuple in degrees
        '''
        
        x, y = self.unit2m_matrix.transform_point(x, y)
        x_abs, y_abs = x + self.x0, self.y0 - y
        return self.projection(x_abs, y_abs, inverse=True)
        
    def find_free_position(self, polygon, number=10, step=4):
        '''
        Checks for collisions with self.conflict_area and in case returns
        nearest x, y coord-tuple (minx, miny) where the given polygon does not
        collide with self.conflict_area. Only tries to move polygon a certain
        times and returns None if no free position could be found.
        
        :param polygon: :class:`shapely.geometry.Polygon`
        :param number: the number of movements as int or float
        :param step: int or float specifying the step which the polygon is moved
            at each iteration
        '''
        
        # minx, miny
        x, y = polygon.bounds[:2]
        # only try to shift text 10 times, otherwise it will be too far away
        # either
        shifts = ((step, 0), (0, step), (-step, 0), (0, -step))
        for _ in xrange(number):
            # only shift if cur area does not collide with self.area
            if not polygon.intersects(self.conflict_area):
                return x, y
            cur_area = polygon.intersection(self.conflict_area).area
            bestdx = bestdy = 0
            best_polygon = polygon
            #: shift polygon in all directions and search for min intersection
            for dx, dy in shifts:
                coords = utils.translate_coords(polygon.exterior.coords, dx, dy)
                shifted = Polygon(tuple(coords))
                shifted_area = shifted.intersection(self.conflict_area).area
                if shifted_area < cur_area:
                    best_polygon = shifted
                    cur_area = shifted_area
                    bestdx, bestdy = dx, dy
            polygon = best_polygon
            x += bestdx
            y += bestdy
        
    def conflict_density(self, x, y, radius=90):
        '''
        Counts all areas which intersect a certain area (defined by radius).
        
        :param x: x-position in unit (pixel/point)
        :param y: y-position in unit (pixel/point)
        :param radius: buffer size around point as int or float
        '''
        
        density_area = Point(x, y).buffer(radius)
        # only MultiPolygon and GeometryCollection have geoms-attribute
        if self.conflict_area.geom_type in ('MultiPolygon',
            'GeometryCollection'
        ):
            density = 0
            for area in self.conflict_area.geoms:
                if density_area.intersects(area):
                    density += 1
            return density
        # self.area.geom_type is Polygon
        elif self.conflict_area.intersects(density_area):
            return 1
        return 0
        
    def write(self):
        '''Writes surface to file object.'''
        
        if self.surface_type == 'png':
            self.surface.write_to_png(self.fobj)
        else:
            self.surface.finish()

