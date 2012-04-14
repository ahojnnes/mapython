Import OpenStreetMap data
=========================

First you need to download a OpenStreetMap XML dump file. A list of currently
available download servers can be found in the `OpenStreetMap wiki <http://wiki.openstreetmap.org/wiki/Planet.osm>`_.

mapython is based on the database schema produced by
`osm2pgsql <http://wiki.openstreetmap.org/wiki/Osm2pgsql>`_. There also exist
modifications of this tool for other database backends than PostgreSQL.

Sample import of a ``.osm`` file:

.. code-block:: bash
    
    osm2pgsql \
        --host localhost \
        --port 5432 \
        --username test \
        --password \
        --database mapython_db \
        --latlong \
        --slim \
        --keep-coastlines \
        dump.osm
        
For small OpenStreetMap dumps and enough memory you can leave out the
``--slim`` option, which imports the dump file much faster. By now mapython
relies on the coastlines provided by OpenStreetMap, so the
``--keep-coastlines`` option is obligatory. It is recommended to keep the geometry
data in geographic format (``--latlon`` option) because mapython can render
maps with different projections - although you can also use already projected
geometry data (more information about this in the :ref:`projections` section).

Note that this import process can take several hours depending on the size of
the dump file and cpu/memory/disk speed of your computer. (e.g. it took me
about 15min to import the data of a uncompressed 800MB dump file without the
``--slim`` option)

If you already have your data imported for mapnik with osm2pgsql you will be
fine unless you render maps with coastlines. osm2pgsql ignores the
``natural=coastline`` tag by default and thus you need to add the coastlines
with the ``--keep-coastlines`` option.
