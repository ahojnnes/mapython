Render Maps with mapython
=========================

Here is a first basic example which requires the geometry data to be in
geographic latlon format (see :ref:`projections` if you already have
projected data):

.. code-block:: python
    
    import os
    os.environ['MAPYTHON_DB_URL'] = 'postgresql://user:password@localhost/database'
    from mapython.draw import Map
    from mapython.render import Renderer
    
    
    # bounding box of map (minlon, minlat, maxlon, maxlat)
    bbox = (170, 11, 171, 12)
    mapobj = Map('map.png', bbox)
    Renderer(mapobj).run()
    mapobj.write()
    
This will use the spherical mercator projection by default and uses the
default mapython style which can be found in ``mapython/styles/default.yml``.
The map graphic is written as png file by default. Note that you need to set
the ``MAPYTHON_DB_URL`` environment variable before importing the
:mod:`mapython.render` module.

Output formats
--------------

mapython supports several output formats for its maps through the cairo
graphics library. You can simply specify the format with an additional
argument:

.. code-block:: python
    
    mapobj = Map('map.pdf', bbox, surface_type='pdf')

Currently mapython supports the following formats: png, pdf, svg and ps

Map graphic size
----------------

You can set the ``max_size`` argument (in pixel or point, depending on the 
output format you chose) which mapython then uses to set the map height and
width based on the bbox extents. mapython automatically determines the
maximum extents of the map and then either sets the height or width to the
``max_size`` value:

.. code-block:: python
    
    mapobj = Map('map.png', bbox, max_size=1000)
    
.. _projections:
    
Projections
-----------

mapython uses the spherical mercator projection by default. There are some
additional projections predefined in :mod:`mapython.projection` which can
be easily applied to mapython maps:

.. code-block:: python
    
    mapobj = Map('map.png', bbox, proj=mapython.projection.plate_carree)
    
Additionally you can provide your own projection functions through the
pyproj library

.. code-block:: python
     
     import pyproj
     
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
     
     mapobj = Map('map.png', bbox, proj=cassini)

or by defining your own python functions:

.. code-block:: python
    
    import math
    
    EARTH_RADIUS = 6371000.175
    
    def mercator(lon, lat):
        x = math.radians(lon) * EARTH_RADIUS
        y = math.atanh(math.sin(math.radians(lat))) * EARTH_RADIUS
        return x, y
        
    mapobj = Map('map.png', bbox, proj=mercator)
    
This also allows you to use already projected geometry data in your database.
All you need to do is to provide the bbox in the projected format and to
define a dummy projection function which simply returns the original
coordinates:

.. code-block:: python
    
    minx, miny = mapython.projection.mercator(170, 11)
    maxx, maxy = mapython.projection.mercator(171, 12)
    bbox = (minx, miny, maxx, maxy)
    dummy = lambda x, y: x, y
    mapobj = Map('map.png', bbox, proj=dummy)
    