Set up the database
===================

You need to install a database management system with spatial extensions
such as PostgreSQL with PostGIS, SQLite with spatialite, MySQL, Oracle, MSSQL
with spatial extensions etc.

Instructions:

* `PostgreSQL and PostGIS <http://postgis.refractions.net/docs/ch02.html>`_
* `SQLite and spatialite <http://postgis.refractions.net/docs/ch02.html>`_
* `MySQL and spatial extrensions <http://dev.mysql.com/doc/refman/5.1/en/spatial-extensions.html>`_

Sample for PostgreSQL und PostGIS:

.. code-block:: bash
    
    sudo su postgres
    createdb -E UNICODE gis
    createlang plpgsql gis
    psql -d gis -f /usr/share/postgresql-8.4-postgis/lwpostgis.sql
    psql -d gis -f /usr/share/postgresql-8.4-postgis/spatial_ref_sys.sql
    createuser -P gis
    psql gis
    grant all on database gis to "gis";
    grant all on spatial_ref_sys to "gis";
    grant all on geometry_columns to "gis";
    