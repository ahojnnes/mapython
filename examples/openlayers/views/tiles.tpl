<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="de" lang="de-de">
    <head>
        <title>mapython</title>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <script type="text/javascript" src="http://www.openlayers.org/api/OpenLayers.js"></script>
        <style type="text/css">
            html, body {
                background-color: #fff;
                height: 96%;
                width: 96%;
                margin: 2%;
            }
            #map {
                width: 100%;
                height: 94%;
                padding:3px;
                border: 1px solid #666;
            }
        </style>
        <script type="text/javascript">
            function init_map() {
                OpenLayers.Lang.setCode('de');
                map = new OpenLayers.Map('map', {
                    controls: [
                        new OpenLayers.Control.MouseDefaults(),
                        new OpenLayers.Control.LayerSwitcher(),
                        new OpenLayers.Control.PanZoomBar()],
                    maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34,
                        20037508.34, 20037508.34),
                });
                var mapython = new OpenLayers.Layer.OSM(
                    'mapython',
                    '/tile-data/${z}/${x}/${y}.png',
                    {
                        numZoomLevels: 19,
                        maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34,
                            20037508.34, 20037508.34),
                        transitionEffect: 'resize',
                        tileSize: new OpenLayers.Size(256, 256),
                    }
                );
                var mapnik = new OpenLayers.Layer.OSM('mapnik');
                map.addLayers([mapython, mapnik]);
                map.setCenter(new OpenLayers.LonLat(11.5, 48.5).transform(
                    new OpenLayers.Projection('EPSG:4326'),
                    new OpenLayers.Projection('EPSG:900913')
                ), 12);
            }
        </script>
    </head>
    <body onload="init_map();">
        <div id="map"></div>
    </body>
</html>