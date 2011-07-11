Custom stylesheets
==================

The :class:`mapython.render.Renderer` uses the ``mapython/styles/default.yml``
stylesheet by default which might be a good starting point for creating
your own stylesheets. These stylesheet files are based on YAML and style
definitions are similar to those in CSS. mapython will only render objects you
added to your stylesheets and automatically determines which elements need to
be fetched from database.

Zoom levels
-----------

You must declare at least one zoom level in your stylesheet which is done as
follows:

.. code-block:: yaml
    
    ZOOMLEVELS:
        # zoom level name: [min scale, max scale]
        0: [0, 5]
        1: [5, 10]
        2: [10, 20]
        ...
        
The key is always the name of the zoom level which does not necessarily have
to be a number. Although it is recommended to use continous ranges because you
can define ranges in your style definitions. The scale value is declared as
metres per pixel or point (depending on the output format you chose).

Map background
--------------

The map background and sea color must be defined as well:

.. code-block:: yaml
    
    MAP_BACKGROUND_COLOR: 1 1 1 1
    SEA_BACKGROUND_COLOR: 0.3 0.3 0.3

As you can see colors are defined as rgb[a] tuples.

Style definitions
-----------------

The next step is to define your styles for specific objects of a certain
geometry type. This decides what objects are retrieved from the database
and how they look like on the map. Style definitions are only valid for
special zoom levels.

Example:

.. code-block:: yaml
    
    POINT: # geometry type, one of POINT, LINE or POLYGON
        place: # tag name
            city: # tag value
                - all: # zoom levels
                    text: name
                    text-color: 0.3 0.3 0.3
                    font-size: 12
                    font-weight: bold
    
    LINE: # geometry type, one of POINT, LINE or POLYGON
        highway: # tag name
            motorway: # tag value
                - 0, 1, 2: # zoom levels
                    color: 0 0 0
                    width: 2
                    z-index: 2
                    etc.
            primary: # tag value
                - 0, 1: # zoom levels
                    color: 0 0 0
                    width: 1
                    z-index: 1
                    
Explanation:

* this will render all objects in the ``*_point``-table which match
  ``place=city`` plus all objects in the ``*_line``-table which match 
  the ``highway=motorway`` or ``highway=primary`` condition
* cities will be rendered at all zoom levels, motorways at zoom levels 0, 1, 2
  and primary roads at 0, 1
* the text used for cities is fetched from the ``name`` column
* motorways will be rendered on top of primary roads (z-index)
* widths, sizes etc. are given in pixel or point (depending on the output
  format you chose)

Overwrite definitions
---------------------

Style definitions can only be overwritten within one tag condition:

.. code-block:: yaml
    
    POINT:
        place:
            city:
                - all:
                    text: name
                    text-color: 0.3 0.3 0.3
                    font-size: 12
                    font-weight: bold
                - 0, 1, 2:
                    font-size: 20
                    font-weight: normal
                    text-border-color: 1 1 1
                    text-border-width: 2

This is going to overwrite or add all definitions for zoom levels 0, 1 and 2.

Note that you can't overwrite complete tag styles, e.g. this does not work:

.. code-block:: yaml
    
    POINT:
        place:
            city:
                - all:
                    text: name
                    text-color: 0.3 0.3 0.3
                    font-size: 12
                    font-weight: bold
        place:
            city:
                - 0, 1, 2:
                    font-size: 20
                    font-weight: normal
                    text-border-color: 1 1 1
                    text-border-width: 2
                    
Define multiple conditions
--------------------------

Sometimes you want to define more than one condition for a style. For example,
if you want to render all objects that match ``boundary=administative`` and
``admin_level=1``. 

.. code-block:: yaml
    
    LINE:
        boundary:
            administrative[admin_level=1]:
                - all:
                    width: 1
                    color: 0 0 0
                    
You can also define more extra conditions:

.. code-block:: yaml
    
    LINE:
        boundary:
            administrative[admin_level=1, admin_level=2, admin_level=34]:
                - all:
                    width: 1
                    color: 0 0 0

Only objects that satisfy all these conditions are fetched from database
(connected by the ``AND`` operator).

Defining ranges
---------------

You can define ranges for zoom levels if you defined continuous levels:

.. code-block:: yaml
    
    ZOOMLEVELS:
        0: [0, 5]
        1: [5, 10]
        2: [10, 20]
        3: [20, 30]
        4: [30, 40]
        5: ...
        6: ...
        
    POINT:
        place:
            city:
                - all:
                    ...
                - 0-4:
                    ...
                - 0, 1:
                    ...

Available style attributes
--------------------------

* points:
    * **text**: column name of text
    * **text-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **text-border-width**: int or float in pixel or point
    * **text-border-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **text-border-line-cap**: butt, square, round
    * **text-border-line-join**: miter, round, bevel
    * **text-border-line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **text-transform**: uppercase, lowercase, capitalize
    * **font-size**: int or float in pixel or point
    * **font-weight**: ultra-light, light, normal, bold, ultra-bold, heavy
    * **font-style**: normal, oblique, italic
    * **font-stretch-style**: ultra-condensed, extra-condensed, condensed,
        semi-condensed, normal, semi-expanded, expanded, extra-expanded,
        ultra-expanded
    * **image**: relative path to image file
    * **z-index**: int
* lines:
    * **color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **width**: int or float in pixel or point
    * **border-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **border-width**: int or float in pixel or point
    * **outline-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **outline-width**: int or float in pixel or point
    * **line-cap**: butt, square, round
    * **line-join**: miter, round, bevel
    * **line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **border-line-cap**: butt, square, round
    * **border-line-join**: miter, round, bevel
    * **border-line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **outline-line-cap**: butt, square, round
    * **outline-line-join**: miter, round, bevel
    * **outline-line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **text**: column name of text
    * **text-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **text-border-width**: int or float in pixel or point
    * **text-border-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **text-border-line-cap**: butt, square, round
    * **text-border-line-join**: miter, round, bevel
    * **text-border-line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **text-transform**: uppercase, lowercase, capitalize
    * **font-size**: int or float in pixel or point
    * **font-weight**: ultra-light, light, normal, bold, ultra-bold, heavy
    * **font-style**: normal, oblique, italic
    * **font-stretch-style**: ultra-condensed, extra-condensed, condensed,
        semi-condensed, normal, semi-expanded, expanded, extra-expanded,
        ultra-expanded
    * **z-index**: int
* polygons:
    * **background-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **background-image**: relative path to image file
    * **border-width**: int or float in pixel or point
    * **border-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **border-line-cap**: butt, square, round
    * **border-line-join**: miter, round, bevel
    * **border-line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **text**: column name of text
    * **text-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **text-border-width**: int or float in pixel or point
    * **text-border-color**: rga[a] (e.g. 0 0 0 or 0 0 0 1)
    * **text-border-line-cap**: butt, square, round
    * **text-border-line-join**: miter, round, bevel
    * **text-border-line-dash**: tuple (e.g. 1 or 1 2 or 2.3 2 1)
    * **text-transform**: uppercase, lowercase, capitalize
    * **font-size**: int or float in pixel or point
    * **font-weight**: ultra-light, light, normal, bold, ultra-bold, heavy
    * **font-style**: normal, oblique, italic
    * **font-stretch-style**: ultra-condensed, extra-condensed, condensed,
        semi-condensed, normal, semi-expanded, expanded, extra-expanded,
        ultra-expanded
