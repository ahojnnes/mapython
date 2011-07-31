# coding: utf-8
import sys
import math
import collections
import cairo
from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.ops import linemerge


def iter_pairs(iterable):
    '''
    Yields pairs in the form of ``(iterable[i], iterable[i-1])``.
    
    :param iterable: any iterable
    
    :yields: ``(elem1, elem2)`` tuple
    '''
    
    last = None
    for elem in iterable:
        if last is not None:
            yield last, elem
        last = elem

def translate_coords(coords, dx, dy):
    '''
    Yields all coordinates translated/shifted by dx and dy.
    
    :param coords: iterable in the form of ``((x1, y1), (x2, y2), ...)``
    :param dx: translation/shifting in x-direction
    :param dy: translation/shifting in y-direction
    
    :yields: (x, y) coordinate tuples
    '''
    
    for x, y in coords:
        yield x + dx, y + dy

def rotate_coords(coords, radians):
    '''
    Yields all coordinates rotated by radians around coordinate center (0, 0).

    :param coords: iterable in the form of ``((x1, y1), (x2, y2), ...)``
    :param radians: rotation given in radians

    :yields: (x, y) coordinate tuples
    '''
    
    matrix = cairo.Matrix()
    matrix.rotate(radians)
    for coord in coords:
        yield matrix.transform_point(*coord)
        
def coord_diffs(coords):
    '''
    Yields dx and dy for each pair of coordinates.
    
    :param coords: iterable in the form of ``((x1, y1), (x2, y2), ...)``
    
    :yields: (x, y) coordinate tuples
    '''
    
    for coord1, coord2 in iter_pairs(coords):
        dx = coord2[0] - coord1[0]
        dy = coord2[1] - coord1[1]
        yield dx, dy
        
def linestring_radians(coords):
    '''
    Yields radians of gradient for each segment of the linestring.
    
    :param coords: iterable in the form of ``((x1, y1), (x2, y2), ...)``
    
    :yields: radians as int or float
    '''
    
    for dx, dy in coord_diffs(coords):
        yield math.atan2(dy, dx)
        
def linestring_lengths(coords):
    '''
    Yields length of each segment of the linestring.
    
    :param coords: iterable in the form of ``((x1, y1), (x2, y2), ...)``
    
    :yields: length as int or float
    '''
    
    for dx, dy in coord_diffs(coords):
        yield math.sqrt(dx**2 + dy**2)
        
def point_radians(point1, point2):
    '''
    Returns radians of line between two points.
    
    :param point1: :class:`shapely.geometry.Point` object
    :param point2: :class:`shapely.geometry.Point` object
    
    :returns: radians [0, 2pi] as int or float
    '''
    
    rad = math.atan2(point1.y - point2.y, point1.x - point2.x)
    return rad if rad > 0 else rad + 2 * math.pi
    
def linestring_char_radians(line, length, width, bearing=0.5):
    '''
    Determines radians of gradient of linestring.

    :param line: :class:`shapely.geometry.LineString` object
    :param length: length indication the position on linestring as int or float
    :param width: width of character int or float
    :param bearing: int or float

    :returns: radians as int or float
    '''
    
    point1 = line.interpolate(length - bearing)
    point2 = line.interpolate(length + width + bearing)
    dx = point2.x - point1.x
    dy = point2.y - point1.y
    return math.atan2(dy, dx)
        
def linestring_text_optimal_segment(coords, width, max_rad=4.5):
    '''
    Tries to find a segment of the linestring which has the least change in
    gradients and is in the middle of the linestring.
    
    :param coords: iterable in the form of ``((x1, y1), (x2, y2), ...)``
    :param width: width of the text as int or float
    :param max_rad: maximum change in gradients as radians
    
    :returns: (start, end) indexes of optimal segment or None
    '''
    
    seg_lens =  tuple(linestring_lengths(coords))
    #: calculate absolute diff of radians of gradient at each node
    rad_diffs = [0]
    for rad1, rad2 in iter_pairs(linestring_radians(coords)):
        rad_diffs.append(abs(rad2 - rad1))
    rad_diffs.append(0)
    # (start, end): sum of radians
    rad_sums = {}
    # if sum of radians is more than max_rad, None is returned
    min_rad = max_rad
    #: find minimal sum of radians and add to rad_sums
    for start in xrange(len(seg_lens)):
        cur_len = 0
        end = None
        #: determine end node
        for i, seg_len in enumerate(seg_lens[start:]):
            cur_len += seg_len
            # width * 1.2 because text needs more space when rendered
            # on a line
            if cur_len >= width * 1.2:
                end = start + i + 1
                break
        #: add to rad_sums if rad <= current minimal rad_sum
        if end is not None:
            rad = sum(rad_diffs[start+1:end])
            if rad < min_rad:
                rad_sums = {(start, end): rad}
                min_rad = rad
            elif rad == min_rad:
                rad_sums[(start, end)] = rad
    #: find midmost element (if multiple elements in rad_sums)
    mindiff = sys.maxint
    midmost = None
    for (start, end), rad in rad_sums.iteritems():
        # distance to start - distance to end
        diff = abs(sum(seg_lens[:start]) - sum(seg_lens[end:]))
        if diff < mindiff:
            mindiff = diff
            midmost = (start, end)
    return midmost
    
def generate_char_geoms(ctx, text, spacing=0.8, space_width=3):
    '''
    Generates geometries for each character in text. Each character is placed
    at (0, 0). Additionally the character width and spacing to
    previous character is determined.
    
    :param ctx: :class:`cairo.Context` object
    :param ctx_pango: :class:`pangocairo.CairoContext` object
    :param text: text as str or unicode
    :param font_desc: :class:`pango.FontDescription` object for this text
    :param spacing: spacing between characters as int or float
    :param space_width: width of one space character
    
    :returns: list containing (geometry, width, spacing) tuples
    '''
    
    ctx.save()
    # list containing geometries and info for each character as a tuple:
    # (geometry, width, height, spacing)
    geoms = []
    cur_spacing = spacing
    for char in text:
        #: character is a space increase spacing
        if char == ' ':
            cur_spacing += space_width
            continue
        #: get path of current character
        ctx.move_to(0, 0)
        ctx.text_path(char)
        paths = []
        coords = []
        for path_type, point in ctx.copy_path_flat():
            if path_type == cairo.PATH_CLOSE_PATH:
                paths.append(coords)
                coords = []
            else: # cairo.PATH_MOVE_TO or cairo.PATH_LINE_TO
                coords.append(point)
        width = ctx.text_extents(char)[2]
        geoms.append((MultiLineString(paths), width, cur_spacing))
        ctx.new_path()
        cur_spacing = spacing
    ctx.restore()
    return geoms
    
def iter_chars_on_line(chars, line, start_len, step=0.85):
    '''
    Yields single character geometries placed on line.
    
    :param chars: iterable generated by ``generate_char_geoms``
    :param line: :class:`shapely.geometry.LineString`
    :param start_len: length or start position on line as int or float
    :param step: distance a character is moved on line at each iteration
        (decrease for more accuracy and increase for faster rendering)
        
    :yields: character geometries as :class:`shapely.geometry.MultiLineString`
    '''
    
    # make sure first character is not rendered directly at the edge of the line
    cur_len = max(start_len, 1)
    # geometry containing path of all rotated characters
    text_geom = LineString()
    for char, width, spacing in chars:
        cur_len += spacing
        last_rad = None
        for _ in xrange(30):
            # get current position on line
            pos = line.interpolate(cur_len)
            # get radians of gradient
            rad = linestring_char_radians(line, cur_len, width)
            #: only rotate if radians changed
            if rad != last_rad:
                rot_coords = tuple(tuple(rotate_coords(geom.coords, rad))
                    for geom in char)
            last_rad = rad
            # move rotated char to current position
            coords = (tuple(translate_coords(c, pos.x, pos.y))
                for c in rot_coords)
            rot = MultiLineString(tuple(coords))
            cur_len += step
            # check whether distance to previous characters is long enough
            if (
                text_geom.distance(rot) > spacing
                or text_geom.geom_type == 'GeometryCollection'
            ):
                text_geom = text_geom.union(rot)
                yield rot
                break
                
def dict2key(d):
    '''
    Returns tuple which can be used as key for another dict.
    
    :param d: dict
    
    :returns: 2-dimensional tuple with keys and values
    '''
    
    return tuple(sorted(d.iteritems()))
    
def text_transform(text, transformation):
    '''
    Transforms text according to a transformation type.
    
    :param text: str or unicode object
    :param transformation: one of ``'lowercase'``, ``'uppercase'`` or
        ``'capitalize'``
        
    :returns: transformed text
    '''
    
    if transformation is not None:
        transformation = transformation.lower()
        if transformation == 'lowercase':
            return text.lower()
        elif transformation == 'uppercase':
            return text.upper()
        elif transformation == 'capitalize':
            new = []
            for word in text.split():
                new.append(word[0].upper() + word[1:])
            return ' '.join(new)
    return text
    
def close_coastlines(lines, bbox):
    '''
    Tries to close open coastlines. This algorithm assumes that water is
    always on the right side of the coastline (see
    http://wiki.openstreetmap.org/wiki/Tiles@home/Dev/Interim_Coastline_Support).
    Therefore it first merges the coastlines and then tries to merge
    them with the bounding box of the map in clockwise direction
    (because we want to fill land mass with the map background and water is on
    the right side of the coastline).
    
    :param lines: iterable of :class:`shapely.geometry.LineString` objects
    :param bbox: :class:`shapely.geometry.Polygon` object of map bbox
    
    :yields: closed :class:`shapely.geometry.LineString` objects
    '''
    
    #: merge lines
    merged = linemerge(lines)
    if merged.geom_type == 'LineString':
        merged = (merged, )
    else: # MultiLineString
        merged = tuple(merged)
    lines = []
    for line in merged:
        # yield if line is already a closed polygon
        if line.is_ring:
            yield line
        else:
            inter = line.intersection(bbox)
            points = line.intersection(bbox.exterior)
            #: only add line to closing process if number of intersections
            #: with bbox is even. Otherwise we have a incomplete coastline
            #: which ends in the visible map
            if points.geom_type == 'MultiPoint' and len(points) % 2 == 0:
                if inter.geom_type == 'LineString':
                    lines.append(inter)
                else:
                    lines.extend(inter)
    #: close open lines
    minx, miny, maxx, maxy = bbox.bounds
    # bounds of the map as lines (beginning at the left top corner)
    blines_init = [
        LineString(((minx, maxy), (maxx, maxy))),
        LineString(((maxx, maxy), (maxx, miny))),
        LineString(((maxx, miny), (minx, miny))),
        LineString(((minx, miny), (minx, maxy))),
    ]
    centroid = bbox.centroid
    #: sort the coastlines according to their position of their first
    #: intersection with the bounding box in clockwise direction
    for line in lines:
        line.angle = point_radians(Point(line.coords[0]), centroid)
    lines = list(sorted(lines, key=lambda l: l.angle, reverse=True))
    # list containing all closed lines
    areas = []
    #: close and merge lines with bounding box in clockwise direction
    while lines:
        area = []
        cur = lines.pop()
        area.extend(reversed(cur.coords))
        #: end node is last coordinate of first line
        end = Point(cur.coords[-1])
        endrad = point_radians(end, centroid)
        # end of line is always the first coordinate because we are merging
        # in clockwise direction
        prevend = Point(cur.coords[0])
        # using deque because it can be rotated
        blines = collections.deque(blines_init)
        while True:
            prevrad = point_radians(prevend, centroid)
            for bline in blines:
                if bline.intersects(prevend):
                    break
            lnext = False
            #: search for coastline that is next to previos line end and
            #: on the same bounding box line
            for line in lines:
                lp = Point(line.coords[-1])
                if bline.intersects(lp) and prevrad >= point_radians(lp, centroid):
                    area.extend(reversed(line.coords))
                    prevend = Point(line.coords[0])
                    lines.remove(line)
                    lnext = True
                    break
            if bline.intersects(end) and endrad <= prevrad:
                areas.append(area)
                break
            #: if there is no coastline next to previous line add corner of
            #: current bounding box line to area
            if not lnext:
                area.append(bline.coords[-1])
                prevend = Point(bline.coords[-1])
                blines.rotate(-1)
    for area in areas:
        # make sure that coastline is a closed path by converting it to
        # a polygon
        yield Polygon(area).exterior
        