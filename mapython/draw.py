# coding: utf-8
import math
import cairo
import pango
import pangocairo
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
        self.ctx = cairo.Context(self.surface)
        self.ctx_pango = pangocairo.CairoContext(self.ctx)
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
            self.height = int(math.ceil(self.max_size / self.x_diff * self.y_diff))
        else:
            self.width = int(math.ceil(self.max_size / self.y_diff * self.x_diff))
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
        
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.set_source_rgba(*color)
        self.ctx.fill()
        
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
        self.ctx.move_to(x, y)
        #: draw line to rest of coords
        for lon, lat in coords[1:]:
            x, y = self.transform_coords(lon, lat)
            self.ctx.line_to(x, y)
        #: fill line with color
        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(width)
        self.ctx.set_line_cap(line_cap)
        self.ctx.set_line_join(line_join)
        self.ctx.set_dash(line_dash or tuple())
        self.ctx.stroke()
        
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
        :param border_line_dash: list/tuple used by :meth:`cairo.Context.set_dash`
        '''
        
        polygons = (exterior, )
        if interiors is not None:
            polygons += interiors
        for coords in polygons:
            #: move to first coords
            x, y = self.transform_coords(*coords[0])
            self.ctx.move_to(x, y)
            #: draw line to rest of coords
            for lon, lat in coords[1:]:
                x, y = self.transform_coords(lon, lat)
                self.ctx.line_to(x, y)
        #: draw border
        self.ctx.set_source_rgba(*border_color)
        self.ctx.set_line_width(border_width)
        self.ctx.set_line_cap(border_line_cap)
        self.ctx.set_line_join(border_line_join)
        self.ctx.set_dash(border_line_dash or tuple())
        self.ctx.stroke_preserve()
        #: fill polygon with color
        self.ctx.set_source_rgba(*background_color)
        if background_image is not None:
            self.ctx.fill_preserve()
            image = cairo.ImageSurface.create_from_png(background_image)
            pattern = cairo.SurfacePattern(image)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            self.ctx.set_source(pattern)
        self.ctx.fill()
        
    def draw_text(
            self,
            coord,
            text,
            color=(0, 0, 0),
            font_size=11,
            font_family='Arial',
            font_style='normal',
            font_stretch_style='normal',
            font_weight='normal',
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
        :param font_style: one of :const:`cairo.FONT_SLANT_*`
        :param font_weight: one of :const:`cairo.FONT_WEIGHT_*`
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
        # abort if there are already too many texts in this area
        if self.conflict_density(x, y) > 1:
            self.ctx.new_path()
            return
        text = utils.text_transform(text, text_transform)
        layout = self.ctx_pango.create_layout()
        font_desc = pango.FontDescription(' '.join(
            (font_family, font_weight, font_style, font_stretch_style,
            str(font_size))
        ))
        layout.set_font_description(font_desc)
        layout.set_text(text)
        width, height = layout.get_pixel_size()
        # place text vertically centered
        y -= height / 2.0
        if image is not None:
            #: if image is used it is centered on x, y and text is placed
            #: right next to it
            image = cairo.ImageSurface.create_from_png(image)
            image_width, image_height = image.get_width(), image.get_height()
            # place text right next to the image
            text_area = box(
                x - image_width / 2.0,
                y,
                x + image_width + width + image_margin,
                y + max(height, image_height) / 2.0
            )
        else:
            #: place text horizontally centered
            x -= width / 2.0
            text_area = box(x, y + height, x + width, y)
        newpos = self.find_free_position(text_area)
        # abort if no free position is found
        if newpos is None:
            self.ctx.new_path()
            return
        newx, newy = newpos
        # abort if new position is too far away from original position
        if Point(newx, newy).distance(Point(x, y)) > 0.1 * self.max_size:
            self.ctx.new_path()
            return
        if image is not None:
            #: include image
            y = newy + (max(height, image_height) - image_height) / 2.0
            self.ctx.set_source_surface(image, newx, y)
            self.ctx.paint()
            image_area = box(x, y, x + image_width, y + image_height)
            newx += image_width + image_margin
            newy += (image_height + height) / 2.0
        # using integer value because otherwise the text will be blurry
        self.ctx.move_to(int(newx), int(newy))
        # copy pango path to cairo context
        self.ctx_pango.layout_path(layout)
        #: draw white background behind name
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.set_source_rgba(*text_halo_color)
        self.ctx.set_line_width(2 * text_halo_width)
        self.ctx.set_line_cap(text_halo_line_cap)
        self.ctx.set_line_join(text_halo_line_join)
        self.ctx.set_dash(text_halo_line_dash or tuple())
        self.ctx.stroke_preserve()
        #: fill font line
        self.ctx.set_source_rgba(*color)
        # not using ctx_pango.show_layout because text halo is not rendered
        # correctly
        self.ctx.fill()
        #: add text area to conflict_area
        area = box(newx, newy + height, newx + width, newy)
        if image is not None:
            area = area.union(image_area.buffer(self.CONFLICT_MARGIN, 1))
        try:
            self.conflict_area = self.conflict_area.union(
                area.buffer(self.CONFLICT_MARGIN, 1))
        except ValueError: # Empty GeometryCollection
            pass
        
    def draw_text_on_line(
            self,
            coords,
            text,
            color=(0, 0, 0),
            font_size=10,
            font_family='Arial',
            font_style='normal',
            font_stretch_style='normal',
            font_weight='normal',
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
        :param font_style: one of :const:`cairo.FONT_SLANT_*`
        :param font_weight: one of :const:`cairo.FONT_WEIGHT_*`
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
        
        text = utils.text_transform(text, text_transform)
        font_desc = pango.FontDescription(' '.join(
            (font_family, font_weight, font_style, font_stretch_style,
            str(font_size))
        ))
        layout = self.ctx_pango.create_layout()
        layout.set_font_description(font_desc)
        layout.set_text(text)
        logical_extents, ink_extents = layout.get_pixel_extents()
        width = logical_extents[2] - logical_extents[0]
        layout_height = ink_extents[3] - ink_extents[1]
        self.ctx.new_path()
        #: make sure line does not intersect other conflict objects
        line = LineString(coords)
        line = line.difference(self.map_area.exterior.buffer(layout_height))
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
        offset = layout_height / 2. + logical_extents[1] / 2.
        line = line.parallel_offset(offset, 'right', resolution=3)
        line = LineString(tuple(reversed(line.coords)))
        # make sure text is rendered centered on line
        start_len = (line.length - width) / 2.
        char_coords = None
        chars = utils.generate_char_geoms(self.ctx, self.ctx_pango, text,
            font_desc)
        #: draw all character paths
        for char in utils.iter_chars_on_line(chars, line, start_len):
            for geom in char.geoms:
                char_coords = iter(geom.coords)
                self.ctx.move_to(*char_coords.next())
                for lon, lat in char_coords:
                    self.ctx.line_to(lon, lat)
                self.ctx.close_path()
        #: only add line to reserved area if text was drawn
        if char_coords is not None:
            covered = line.buffer(layout_height + self.CONFLICT_MARGIN)
            self.conflict_area = self.conflict_area.union(covered)
        #: draw border around characters
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.set_source_rgba(*text_halo_color)
        self.ctx.set_line_width(2 * text_halo_width)
        self.ctx.set_line_cap(text_halo_line_cap)
        self.ctx.set_line_join(text_halo_line_join)
        self.ctx.set_dash(text_halo_line_dash or tuple())
        self.ctx.stroke_preserve()
        #: fill actual text
        self.ctx.set_source_rgba(*color)
        self.ctx.fill()
        
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
        self.ctx.set_source_surface(image, x, y)
        self.ctx.paint()
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
            
