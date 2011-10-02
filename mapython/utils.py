# coding: utf-8
import sys
import math
import collections
import cairo
from shapely.geometry import Point, Polygon, MultiPolygon
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

def azimuth(point1, point2):
    '''
    Returns azimuth of line between two points.

    :param point1: :class:`shapely.geometry.Point` object
    :param point2: :class:`shapely.geometry.Point` object

    :returns: radians [0, 2pi] as int or float
    '''

    rad = math.atan2(point2.x - point1.x, point2.y - point1.y)
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

def generate_char_geoms(ctx, text, spacing=0.6, space_width=3):
    '''
    Generates coordinates for each character in text. Each character is placed
    at (0, 0). Additionally the character width and spacing to
    previous character is determined.

    :param ctx: :class:`cairo.Context` object
    :param text: text as str or unicode
    :param spacing: spacing between characters as int or float
    :param space_width: width of one space character

    :returns: list containing (coordinate tuple, width, spacing) tuples
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
        geoms.append((paths, width, cur_spacing))
        ctx.new_path()
        cur_spacing = spacing
    ctx.restore()
    return geoms

def iter_chars_on_line(chars, line, start_len, step=0.6):
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
    text_geom = Polygon()
    for paths, width, spacing in chars:
        cur_len += spacing
        last_rad = None
        for _ in xrange(30):
            # get current position on line
            pos = line.interpolate(cur_len)
            # get radians of gradient
            rad = linestring_char_radians(line, cur_len, width)
            #: only rotate if radians changed
            if rad != last_rad:
                rot_coords = tuple(tuple(rotate_coords(geom, rad))
                    for geom in paths)
            last_rad = rad
            # move rotated char to current position
            rot = MultiPolygon(tuple(
                Polygon(tuple(translate_coords(c, pos.x, pos.y)))
                for c in rot_coords
            ))
            # check whether distance to previous characters is long enough
            if (
                text_geom.distance(rot) >= spacing
                or text_geom.geom_type == 'GeometryCollection'
            ):
                text_geom = text_geom.union(rot)
                cur_len += width
                yield rot
                break
            cur_len += step

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

def merge_lines(lines):
    '''
    Returns tuple of merged lines.

    :param lines: iterable of :class:`shapely.geometry.LineString`

    :returns: tuple :class:`shapely.geometry.LineString`
    '''

    merged = linemerge(lines)
    if merged.geom_type == 'LineString':
        merged = (merged, )
    else: # MultiLineString
        merged = tuple(merged)
    return merged

def close_coastlines(lines, bbox):
    '''
    Tries to close open coast-/shorelines. This algorithm assumes that water is
    always on the right side of the coastline (see
    http://wiki.openstreetmap.org/wiki/Tiles@home/Dev/Interim_Coastline_Support).
    Returns closed lines that contain water.

    :param lines: iterable of :class:`shapely.geometry.LineString` objects
    :param bbox: :class:`shapely.geometry.Polygon` object of map bbox

    :yields: closed :class:`shapely.geometry.LineString` objects
    '''

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
        line.angle = azimuth(centroid, Point(line.coords[0]))
    lines = list(sorted(lines, key=lambda l: l.angle))
    # list containing all closed lines
    coastlines = []
    #: close and merge lines with bounding box in clockwise direction
    while lines:
        coastline = []
        cur = lines.pop(0)
        coastline.extend(cur.coords)
        # end node of this coastline is first coordinate of first line
        end = Point(cur.coords[0])
        endangle = azimuth(centroid, end)
        prevend = Point(cur.coords[-1])
        # using deque because it can be rotated
        blines = collections.deque(blines_init)
        # rotate until bounding line intersects end of first line
        while not blines[0].intersects(prevend):
            blines.rotate(1)
        #: merge other lines and bounding lines until end of first
        #: line is reached
        while True:
            prevangle = azimuth(centroid, prevend)
            for bline in blines:
                if bline.intersects(prevend):
                    break
            next_line = False
            for line in lines:
                if (
                    bline.intersects(Point(line.coords[0]))
                    #: make sure line is on the right hand side
                    #: (clockwise rotation)
                    and line.angle >= prevangle
                    and abs(line.angle - prevangle) < math.pi
                    #: make sure we did not follow bounding lines more than
                    #: one complete time around (> 2pi)
                    and not (
                        (endangle < math.pi and prevangle > math.pi
                        and prevangle > line.angle > endangle)
                        or (line.angle > endangle > prevangle)
                    )
                ):
                    coastline.extend(line.coords)
                    prevend = Point(line.coords[-1])
                    lines.remove(line)
                    next_line = True
                    break
            if not next_line:
                if (
                    bline.intersects(end)
                    and
                    (
                        0 < (endangle - prevangle) < math.pi
                        or (endangle < math.pi and prevangle > math.pi)
                    )
                ):
                    coastlines.append(coastline)
                    break
                else:
                    prevend = Point(bline.coords[-1])
                    coastline.append(bline.coords[-1])
                    blines.rotate(-1)
    for coastline in coastlines:
        # make sure that coastline is a closed path by converting its
        # coordinates to a polygon
        yield Polygon(coastline).exterior

