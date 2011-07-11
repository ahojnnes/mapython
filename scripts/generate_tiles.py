# coding: utf-8
import Queue
import multiprocessing
import os
import sys
import optparse
import string
from shapely.geometry import box


# global bbox of spherical mercator projection (-180, -85.501, 180, 85.501)
MERC_GLOBAL_BBOX = (-20037508.34, -20037508.34, 20037508.34, 20037508.34)


class Generator(multiprocessing.Process):
    
    queue = multiprocessing.JoinableQueue()
    stop = multiprocessing.Event()
    
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.renderer = Renderer
    
    def run(self):
        while not self.stop.is_set():
            try:
                map_info = self.queue.get(False, 1)
            except Queue.Empty:
                pass
            else:
                map_obj = Map(*map_info)
                renderer = self.renderer(map_obj, quiet=True)
                renderer.run()
                map_obj.write()
                self.queue.task_done()
                print 'Built %s' % str(map_obj.fobj)
                
                
def iter_tile_maps(bbox, path, level, width, height):
    try:
        os.mkdir(os.path.join(path, str(level)))
    except OSError:
        pass # path already exists
    glminx, glminy, glmaxx, glmaxy = MERC_GLOBAL_BBOX
    #: global size in metres
    diffx = glmaxx - glminx
    diffy = glmaxy - glminy
    #: tile size in metres
    tilesizex = diffx / float(2 ** level) * width / 256
    tilesizey = diffy / float(2 ** level) * height / 256
    #: bbox bounds
    minx, miny, maxx, maxy = bbox.bounds
    minx, miny = mercator(minx, miny)
    maxx, maxy = mercator(maxx, maxy)
    #: index / coord of first tile to be rendered
    #: coord center is upper left corner of global map
    startindexx = int((minx - glminx) / tilesizex)
    startindexy = int(abs(maxy - glmaxy) / tilesizey)
    endindexx = int((maxx - glminx) / tilesizex) + 1
    endindexy = int(abs(miny - glmaxy) / tilesizey) + 1
    for indexx in xrange(startindexx, endindexx):
        for indexy in xrange(startindexy, endindexy):
            tilemin = mercator(
                glminx + indexx * tilesizex,
                glmaxy - (indexy + 1) * tilesizey,
                inverse=True
            )
            tilemax = mercator(
                glminx + (indexx + 1) * tilesizex,
                glmaxy - indexy * tilesizey,
                inverse=True
            )
            tilebbox = tilemin + tilemax
            try:
                os.mkdir(os.path.join(path, str(level), str(indexx)))
            except OSError:
                pass # path already exists
            tilepath = os.path.join(path, str(level), str(indexx),
                str(indexy) + '.png')
            yield tilepath, tilebbox, max(width, height)
            
def build_tiles(bbox, path, level, width=256, height=256, process_number=3):
    '''
    Builds and renders map tiles.

    :param bbox: bounding box for whole map area
    :param path: path to directory where tiles are saved
    :param level: zoom level
    :param size: tile width as int
    '''
    Generator.stop.clear()
    generators = [Generator() for _ in xrange(process_number)]
    for generator in generators:
        generator.start()
    for map_info in iter_tile_maps(bbox, path, level, width, height):
        Generator.queue.put(map_info)
    generator.queue.join()
    Generator.stop.set()
    # wait until all processes terminate
    for generator in generators:
        generator.join()
        
def parse_options():
    parser = optparse.OptionParser()
    parser.add_option('--path', dest='path',
        help='path to output directory for tiles')
    parser.add_option('--left', dest='left', type='float',
        help='left coordinate of bbox')
    parser.add_option('--top', dest='top', type='float',
        help='top coordinate of bbox')
    parser.add_option('--right', dest='right', type='float',
        help='right coordinate of bbox')
    parser.add_option('--bottom', dest='bottom', type='float',
        help='bottom coordinate of bbox')
    parser.add_option('--zoomlevels', dest='zoomlevels',
        help='comma separated list of zoom levels')
    parser.add_option('--width', dest='width', type='int',
        help='tile width in pixel', default=256)
    parser.add_option('--height', dest='height', type='int',
        help='tile height in pixel', default=256)
    parser.add_option('--process_number', dest='process_number', type='int',
        help='number of parallel render processes', default=3)
    parser.add_option('--database', dest='database',
        help='database url (postgresql://user:password@localhost/database)')
    options, _ = parser.parse_args()
    #: check if all options are set
    option_list = []
    for opt in parser.option_list:
        try:
            option_list.append(getattr(options, str(opt.dest)))
        except AttributeError:
            pass
    if all(option_list):
        options.zoomlevels = map(int, map(string.strip,
            options.zoomlevels.split(',')))
        return options
    print 'usage error: missing arguments, see ``-h | --help``'
    
        
if __name__ == '__main__':
    options = parse_options()
    if options is not None:
        os.environ['MAPYTHON_DB_URL'] = options.database
        from mapython.projection import mercator
        from mapython.draw import Map
        from mapython.render import Renderer
        bbox = box(
            options.left,
            options.top,
            options.right,
            options.bottom
        )
        for level in options.zoomlevels:
            build_tiles(bbox, options.path, level, options.width,
                options.height, options.process_number)
        