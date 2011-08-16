# coding: utf-8
import os
from sqlalchemy import create_engine, MetaData, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import geoalchemy


DB_URL = os.environ['MAPYTHON_DB_URL']
DB_PREFIX = os.environ.get('MAPYTHON_DB_PREFIX', 'planet_osm')

engine = create_engine(DB_URL)
session = sessionmaker(bind=engine)()
metadata = MetaData(engine)
Base = declarative_base(metadata=metadata)
    
    
class OSMBase(object):
    
    access = Column('access', String)
    addr_housenumber = Column('addr:housenumber', String)
    addr_interpolation = Column('addr:interpolation', String)
    admin_level = Column('admin_level', String)
    aerialway = Column('aerialway', String)
    aeroway = Column('aeroway', String)
    amenity = Column('amenity', String)
    area = Column('area', String)
    barrier = Column('barrier', String)
    bicycle = Column('bicycle', String)
    boundary = Column('boundary', String)
    bridge = Column('bridge', String)
    building = Column('building', String)
    construction = Column('construction', String)
    cutting = Column('cutting', String)
    disused = Column('disused', String)
    embankment = Column('embankment', String)
    foot = Column('foot', String)
    highway = Column('highway', String)
    historic = Column('historic', String)
    horse = Column('horse', String)
    junction = Column('junction', String)
    landuse = Column('landuse', String)
    layer = Column('layer', String)
    leisure = Column('leisure', String)
    lock = Column('lock', String)
    man_made = Column('man_made', String)
    military = Column('military', String)
    motorcar = Column('motorcar', String)
    name = Column('name', String)
    natural = Column('natural', String)
    oneway = Column('oneway', String)
    operator = Column('operator', String)
    osm_id = Column('osm_id', Integer, primary_key=True)
    place = Column('place', String)
    power = Column('power', String)
    power_source = Column('power_source', String)
    railway = Column('railway', String)
    ref = Column('ref', String)
    religion = Column('religion', String)
    route = Column('route', String)
    service = Column('service', String)
    shop = Column('shop', String)
    sport = Column('sport', String)
    tourism = Column('tourism', String)
    # tracktype = Column('tracktype', String) - missing in OSMPoint
    tunnel = Column('tunnel', String)
    waterway = Column('waterway', String)
    # way_area = Column('way_area', Float) - missing in OSMPoint
    width = Column('width', String)
    wood = Column('wood', String)
    z_order = Column('z_order', Integer)
    
    
class OSMPoint(Base, OSMBase):
    
    '''This class represents the PREFIX_point table generated by osm2pgsql.'''
    
    __tablename__ = '%s_point' % DB_PREFIX
    
    geom = geoalchemy.GeometryColumn('way', geoalchemy.Point(2))
    

class OSMLine(Base, OSMBase):
    
    '''This class represents the PREFIX_line table generated by osm2pgsql.'''
    
    __tablename__ = '%s_line' % DB_PREFIX
    
    geom = geoalchemy.GeometryColumn('way', geoalchemy.LineString(2))
    tracktype = Column('tracktype', String)
    way_area = Column('way_area', Float)
    
    
class OSMPolygon(Base, OSMBase):
    
    '''This class represents the PREFIX_polygon table generated by osm2pgsql.'''
    
    __tablename__ = '%s_polygon' % DB_PREFIX
    
    geom = geoalchemy.GeometryColumn('way', geoalchemy.MultiPolygon(2))
    tracktype = Column('tracktype', String)
    way_area = Column('way_area', Float)
    
    
class OSMRoad(Base, OSMBase):
    
    '''This class represents the PREFIX_road table generated by osm2pgsql.'''
    
    __tablename__ = '%s_roads' % DB_PREFIX
    
    geom = geoalchemy.GeometryColumn('way', geoalchemy.LineString(2))
    tracktype = Column('tracktype', String)
    way_area = Column('way_area', Float)
    
    
geoalchemy.GeometryDDL(OSMPoint.__table__)
geoalchemy.GeometryDDL(OSMLine.__table__)
geoalchemy.GeometryDDL(OSMPolygon.__table__)
geoalchemy.GeometryDDL(OSMRoad.__table__)

