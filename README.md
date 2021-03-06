mapython is a toolkit for rendering maps based on OpenStreetMap data. It is released under the MIT license and is entirely written in Python.

Usage
=====

    import os
    os.environ['MAPYTHON_DB_URL'] = \
        'postgresql://user:password@localhost/database'
    from mapython.render import Renderer
    from mapython.draw import Map

    bbox = (11.4, 48.3, 11.9, 48.6)

    mapobj = Map('map.png', bbox)
    renderer = Renderer(mapobj)
    renderer.run()
    mapobj.write()

Contribute
==========

If you have ideas for improving mapython or found a bug, check out mapython's GitHub repository. mapython is under active development and any contribution is welcome.

Features
========

* simple and intuitive style definitions in YAML
* pure Python code base (with fast underlying C/C++ libraries)
* easily extensible and customizable
* bitmap and vector graphics as output format
* support for custom map projections

Limitations
===========

mapython is under active development and comparatively new, therefore it still has some limitations.

* there is only limited support for rendering bridges and tunnels correctly
* only the data format provided by "osm2pgsql" is supported
