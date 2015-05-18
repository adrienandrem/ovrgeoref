#!/usr/bin/env python

# Programme Python georeferencant les imagettes
# de l export de scene Geostore (http://www.geo-airbusds.com)
#
# Creation date: 2015-05-15
# Author: Adrien Andre <adr.andre@laposte.net>
# Description: Creates a new export-geo.zip
#   with added overview image georeferencing files
#   (.wld and .auw.xml)


# To execute: open the OSGeo4W Shell, and type:
# C:\>python D:\ovrgeoref.py D:\geostore_export.zip

# TODO: Validation with Geostore KMZ export.
#   Get GroundOverlay bounds.


try:
    from osgeo import gdal
    from osgeo import osr
    from osgeo import ogr
except:
    import gdal
    import osr
    import ogr

import argparse
import os
import tempfile, shutil, zipfile

SHAPEFILE   = "Export.shp"
NAME_DRIVER = "ESRI Shapefile"
FIELD_ID = "footprint"

# Retrieve argument
parser = argparse.ArgumentParser()
parser.add_argument("archive", type=str,
                    help="Geostore zip archive of shapefile export")
args = parser.parse_args()
zip = args.archive

# Unzip archive in new temp directory
tempdir = tempfile.mkdtemp()
archive = zipfile.ZipFile(zip)
archive.extractall(tempdir)
archive.close()
targetdir = os.path.join(tempdir, "images", "geo")
os.mkdir(targetdir)

# Import vector shapefile
driver = ogr.GetDriverByName(NAME_DRIVER)
dataSource = driver.Open(os.path.join(tempdir, SHAPEFILE), 0)
layer = dataSource.GetLayer()

# Retrieve extents
features = {}
for feature in layer:
    geom = feature.GetGeometryRef()
    name = feature.GetField(FIELD_ID)
    extent = geom.GetEnvelope()

    features[name] = extent

# TODO: Compute extents intersection with AOI

# Georeference PNG overviews
# Notice: CRS is stored in .aux.xml files,
#   and coordinate information in .wld files
format = "-of PNG"
crs    = "-a_srs EPSG:4326"
option = "-co WORLDFILE=YES"
for name, (ulx, lrx, lry, uly) in features.items():
    bounds = "-a_ullr {0} {1} {2} {3}".format(ulx, uly, lrx, lry)
    source = os.path.join(tempdir, "images", "{0}.png".format(name))
    target = os.path.join(targetdir, "{0}.png".format(name))
    command = "gdal_translate {0} {1} {2} {3} {4} {5}".format(format, option, bounds, crs, source, target)
    os.system(command)
    os.remove(target) # We don't need the new PNG files

# Move georeferencing files next to original overviews
target = os.path.join(tempdir, "images")
for name in features.keys():
    source = os.path.join(tempdir, "images", "geo", "{0}.wld".format(name))
    shutil.move(source, target)
    source = os.path.join(tempdir, "images", "geo", "{0}.png.aux.xml".format(name))
    shutil.move(source, target)
os.rmdir(targetdir) # Remove GDAL target directory

# Create a new zip file
shutil.make_archive("{0}-geo".format(os.path.splitext(zip)[0]), "zip", tempdir)

# Remove temp directory
shutil.rmtree(tempdir, ignore_errors=True) # FIXME: Might not remove everything
