# coding: utf-8
import os
import string
import functools
from collections import defaultdict
import yaml
import cairo
from mapython import utils


FONT_WEIGHT = {
    'normal': cairo.FONT_WEIGHT_NORMAL,
    'bold': cairo.FONT_WEIGHT_BOLD,
}
FONT_STYLE = {
    'normal': cairo.FONT_SLANT_NORMAL,
    'italic': cairo.FONT_SLANT_ITALIC,
    'oblique': cairo.FONT_SLANT_OBLIQUE,
}
LINE_CAP = {
    'butt': cairo.LINE_CAP_BUTT,
    'round': cairo.LINE_CAP_ROUND,
    'square': cairo.LINE_CAP_BUTT,
}
LINE_JOIN = {
    'miter': cairo.LINE_JOIN_MITER,
    'round': cairo.LINE_JOIN_ROUND,
    'bevel': cairo.LINE_JOIN_BEVEL,
}


def parse_yml(doc):
    zoomlevels = doc['ZOOMLEVELS']
    for geom_type in ('point', 'line', 'polygon'):
        tags = doc.get(geom_type.upper()) or {}
        for tag, settings in tags.iteritems():
            for value, setting in settings.iteritems():
                for tag_value in parse_tag_value(tag, value):
                    for style in parse_setting(
                        geom_type, tag_value, setting, zoomlevels
                    ):
                        yield style

def parse_setting(geom_type, tag_value, setting, zoomlevels):
    for level_setting in setting:
        raw_levels, raw_attrs = level_setting.iteritems().next()
        attrs = parse_attrs(raw_attrs)
        for level in parse_levels(raw_levels, zoomlevels):
            yield Style(geom_type, level, tag_value, attrs.copy())

def convert_bool(value):
    if value == 'True':
        return 'yes'
    elif value == 'False':
        return 'no'
    return value

def parse_tuple(value):
    return map(float, str(value).split())

def parse_tag_value(tag, value):
    values = map(string.strip, str(value).split(','))
    for value in values:
        value = value.split('[')
        tag_value = {tag:convert_bool(value.pop(0))}
        if value:
            exprs = map(string.strip, value[0][:-1].split('&'))
            exprs = map(functools.partial(string.split, sep='='), exprs)
            for tag, value in exprs:
                tag_value[tag] = convert_bool(value)
        yield tag_value

def parse_attrs(attrs):
    new_attrs = {}
    for key, value in attrs.iteritems():
        if 'color' in key or 'line-dash' in key:
            value = parse_tuple(value)
        elif key == 'font-weight':
            value = FONT_WEIGHT.get(value, value)
        elif key == 'font-style':
            value = FONT_STYLE.get(value, value)
        elif 'line-cap' in key:
            value = LINE_CAP.get(value, value)
        elif 'line-join' in key:
            value = LINE_JOIN.get(value, value)
        new_attrs[key] = value
    return new_attrs

def parse_levels(raw_levels, zoomlevels):
    raw_levels = map(string.strip, str(raw_levels).split(','))
    levels = set()
    for raw_level in raw_levels:
        new_levels = []
        if raw_level == 'all':
            new_levels = zoomlevels.iterkeys()
        elif '-' in raw_level:
            new_levels = map(int, raw_level.split('-'))
            new_levels = range(new_levels[0], new_levels[1] + 1)
        else:
            new_levels = map(int, raw_level)
        levels.update(set(new_levels))
    return levels


class Style(object):

    '''
    Creates a new style object which can be applied to a
    :class:`mapython.style.StyleSheet`.

    :param geom_type: one of 'point', 'line' or 'polygon'
    :param level: level-name
    :param tag_value: dict specifying the tags and values of the style,
        e.g. ``{'highway':'motorway', ...}``
    :param attrs: dict containing all style settings,
        e.g. ``{'color': (1, 1, 1), 'font-size': 12, ...}``
    '''

    def __init__(self, geom_type, level, tag_value, attrs):
        self.geom_type = geom_type
        self.level = level
        self.tag_value = tag_value
        self.attrs = attrs

    def __getitem__(self, key):
        return self.attrs[key]

    def __setitem__(self, key, value):
        self.attrs[key] = value

    def __getattr__(self, name):
        print name
        if name == 'tags':
            return self.__dict__[name]
        try:
            return self.attrs[name.replace('_', '-')]
        except KeyError:
            raise AttributeError('this attribute is not specified')

    def get(self, key, default=None):
        '''
        Returns style attribute value or default.

        :param key: style attribute key
        :param default: default value if no attribute is found

        :returns: attribute value
        '''

        try:
            return self[key]
        except KeyError:
            return default


class StyleSheet(object):

    '''
    Creates a new stylesheet which is used by the
    :class:`mapython.render.Renderer` to render a
    :class:`mapython.draw.Map` object.

    :param path: path to YAML stylesheet or None
    '''

    MAX_Z_INDEX = 999

    def __init__(self, stylesheet=None):
        self._last_scale = self._last_level = None
        # dict structure: styles[level][geom_type][(tag=name,)] = Style
        self.styles = defaultdict(lambda: defaultdict(dict))
        self.zoomlevels = {}
        self.dirname = None
        if stylesheet is not None:
            if (
                (isinstance(stylesheet, str) or isinstance(stylesheet, unicode))
                and os.path.isfile(stylesheet)
            ):
                self.dirname = os.path.dirname(os.path.abspath(stylesheet))
                with open(stylesheet, 'r') as fobj:
                    doc = yaml.load(fobj)
            else:
                doc = yaml.load(stylesheet)
            self.zoomlevels = doc['ZOOMLEVELS']
            self.map_background = parse_tuple(doc['MAP_BACKGROUND'])
            self.sea_background = parse_tuple(doc['SEA_BACKGROUND'])
            for style in parse_yml(doc):
                self.update(style)

    def get(self, scale, geom_type, tag_value, default=None):
        '''
        Returns style or default for given settings.

        :param scale: metres per pixel or point
        :param geom_type: one of ``'point'``, ``'line'`` or ``'polygon'``
        :param tag_value: dict specifying the tags and values of the style,
            e.g. ``{'highway':'motorway', ...}``
        :param default: default value if no style is found

        :returns: :class:`mapython.style.Style` or default
        '''

        level = self.get_level(scale)
        try:
            return self.styles[level][geom_type][utils.dict2key(tag_value)]
        except KeyError:
            return default

    def get_level(self, scale, default=None):
        '''
        Returns the level according to the scale.

        :param scale: metres per pixel or point
        :param default: default value if no level is found

        :returns: level name
        '''

        # use cached result
        if scale == self._last_scale:
            return self._last_level
        #: determine level for scale
        for level, scales in self.zoomlevels.iteritems():
            if scales[0] <= scale < scales[1]:
                self._last_scale = scale
                self._last_level = level
                return level
        return default

    def update(self, style):
        '''
        Adds style or overwrites existing style with new attributes.

        :param style: :class:`mapython.style.Style` object
        '''

        #: overwrite if style is already set for this level
        existing = self.get(self.zoomlevels[style.level][0], style.geom_type,
            style.tag_value)
        if existing is not None:
            existing.attrs.update(style.attrs)
        else: # style not set for this level
            self.styles[style.level][style.geom_type] \
                [utils.dict2key(style.tag_value)] = style

    def iter_styles(self, scale, geom_type):
        '''
        Returns generator which yields all styles set for this scale and
        geom_type.

        :param scale: metres per pixel or point
        :param geom_type: one of ``'point'``, ``'line'`` or ``'polygon'``

        :yields: :class:`mapython.style.Style`
        '''

        level = self.get_level(scale)
        for style in self.styles[level][geom_type].itervalues():
            yield style

