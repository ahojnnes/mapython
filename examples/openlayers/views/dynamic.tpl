<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="de" lang="de-de">
    <head>
        <title>mapython</title>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <script type="text/javascript" src="http://www.openlayers.org/api/OpenLayers.js"></script>
        <style type="text/css">
            html, body {
                background-color: #fff;
                height: 98%;
                width: 98%;
                margin: 1%;
            }
            #map {
                width: 700px;
                height: 600px;
                padding:3px;
                border: 1px solid #666;
            }
        </style>
        <script type="text/javascript">
            OpenLayers.Layer.mapython = OpenLayers.Class(OpenLayers.Layer.MapServer, {

                getURL: function (bounds) {
                    var res = this.map.getResolution();
                    var min = OpenLayers.Layer.SphericalMercator.inverseMercator(
                        bounds.left, bounds.bottom);
                    var max = OpenLayers.Layer.SphericalMercator.inverseMercator(
                        bounds.right, bounds.top);
                    var minextent = OpenLayers.Layer.SphericalMercator.inverseMercator(
                        this.maxExtent.left, this.maxExtent.bottom);
                    var maxextent = OpenLayers.Layer.SphericalMercator.inverseMercator(
                        this.maxExtent.right, this.maxExtent.top);
                    var path = '?' + 'width=' + this.tileSize.w + '&' + 'height=' + this.tileSize.h;
                    path += '&' + 'scale=' + res + '&' + 'left=' + min.lon
                        + '&' + 'top=' + max.lat + '&' + 'right=' + max.lon
                        + '&' + 'bottom=' + min.lat;
                    return this.url + path;
                },

                CLASS_NAME: "OpenLayers.Layer.mapython"
            });

            function init_map() {
                bbox = new Array(10, 47, 12, 49);

                var min = OpenLayers.Layer.SphericalMercator.forwardMercator(bbox[0], bbox[1]);
                var max = OpenLayers.Layer.SphericalMercator.forwardMercator(bbox[2], bbox[3]);
                var bounds = new OpenLayers.Bounds(min.lon, min.lat, max.lon, max.lat);
                var map = new OpenLayers.Map('map', {
                    controls: [
                        new OpenLayers.Control.MouseDefaults(),
                        new OpenLayers.Control.LayerSwitcher(),
                        new OpenLayers.Control.PanZoomBar()],
                    maxExtent: bounds,
                    numZoomLevels: 10,
                    maxResolution: 160,
                    units: 'meters',
                }, {
                    singleTile: true
                });
                var mapython_layer = new OpenLayers.Layer.mapython('mapython',
                    'http://localhost:8080/render/',
                    {}, {
                        singleTile: true,
                        maxExtent: bounds,
                        transitionEffect: 'resize',
                    }
                );
                map.addLayers([mapython_layer]);
                map.setCenter(bounds.centerLonLat, 4);
            }
            
        </script>
    </head>
    <body onload="init_map();">
        <div id="map"></div>
    </body>
</html>