# coding: utf-8
import pyproj


mercator = pyproj.Proj('''
+proj=merc
    +a=6378137
    +b=6378137
    +lat_ts=0
    +lon_0=0
    +x_0=0
    +y_0=0
    +k=1
    +units=m
    +nadgrids=@null
    +no_defs
''')
'''Spherical mercator projection, see http://spatialreference.org/ref/epsg/3785/'''


plate_carree = pyproj.Proj('''
+proj=eqc
    +a=6378137
    +b=6378137
    +lat_ts=0
    +lon_0=0
    +x_0=0
    +y_0=0
    +k=1
    +units=m
    +nadgrids=@null
    +no_defs
''')
'''Plate Carreé projection, see http://spatialreference.org/ref/esri/53001/'''


cassini = pyproj.Proj('''
+proj=cass
    +a=6378137
    +b=6378137
    +lat_0=0
    +lon_0=0
    +x_0=0
    +y_0=0
    +k=1
    +units=m
    +nadgrids=@null
    +no_defs
''')
'''Cassini projection, see http://spatialreference.org/ref/esri/53028/'''
    