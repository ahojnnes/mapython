************
Introduction
************

Dependencies
============

* pycairo
* numpy
* shapely
* geoalchemy
* pyproj
* pyyaml

Installation
============

to be continued

Usage
=====

Here is a short usage example of maptython:

    >>> import os
    >>> os.environ['MAPYTHON_DB_URL'] = 'postgresql://user:password@localhost/database'
    >>> from mapython.draw import Map
    >>> from mapython.render import Renderer
    >>> bbox = (170, 11, 171, 12)
    >>> mapobj = Map('map.png', bbox)
    >>> Renderer(mapobj).run()
    >>> mapobj.write()
    
For more details on how to use mapython, check out the
:ref:`Tutorial<tutorial>` or :ref:`Reference<reference>` sections.

Author
======

Johannes Schönberger

License
=======

mapython is released under the MIT License:

.. code-block:: text
    
    Copyright (C) 2011 by Johannes Schönberger

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
    