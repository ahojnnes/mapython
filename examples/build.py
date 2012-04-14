# coding: utf-8
import os

os.environ['MAPYTHON_DB_URL'] = 'postgresql://user:password@localhost/database'
from mapython.render import Renderer
from mapython.draw import Map
from mapython.projection import mercator
from mapython.style import StyleSheet, Style


bbox = (11.4, 48.3, 11.9, 48.6)


mapobj = Map('map.png', bbox, max_size=900)
renderer = Renderer(mapobj)
renderer.run()
mapobj.write()


sty = StyleSheet('path-to-style-or-None')
sty.add(Style('line', 3,
    {'highway': 'motorway'},
    {'color': (1, 1, 1, 0.3)}
))
mapobj = Map('map.pdf', bbox, max_size=300, surface_type='pdf')
renderer = Renderer(mapobj, sty)
renderer.run()
mapobj.write()
