#------------------------------------------------------------------------
#       Import Shapefile Admin (1.1)
#       Made for the C-MAP Minneapolis QC Team
#
#       Benjamin Gappa
#       5/22/17
#------------------------------------------------------------------------
#	V1.0 - 5/22/17
#		Imports a waterbody's polygon geometry from the Admin Site
#		Imports any non-reviewed trips' tracklines from the Admin Site
#		Does not fail under most circumstances
#			* Handles punctuation in waterbody names
#			* Skips GEOMETRYCOLLECTIONS
#
#		Scandinavian waterbodies are not supported
#
#-----------------------------------------------------------------------
#	V1.1 - 5/23/17 (CURRENT)
#		Filenames saved as waterbody ID's. This will circumvent waterbody
#		naming issues describe above. A future release may handle those
#		cases.
#
#-----------------------------------------------------------------------
import requests
import json
import arcpy
from arcpy import env

##
##	API Endpoint Interaction
##

# Parameters Form
username = str(arcpy.GetParameterAsText(0))
pw = str(arcpy.GetParameterAsText(1))
waterbody_id = int(arcpy.GetParameterAsText(2))
#API Variables
url = str("http://admin.digitalmarine.com/api/GisPlugin/WaterbodyExportWkt")
heads = {'Content-type': 'application/json'}

# Dictionary
p = {}
p["Id"] = waterbody_id
p["Username"] = username
p["Password"] = pw
p_json = json.dumps(p)

r = requests.post(url, data=p_json, headers=heads)
data = r.json()

# API Error Handling
if r.status_code == 401:
	arcpy.AddError(r.status_code)
	arcpy.AddError("Invalid Username or Password")
	quit()
elif r.status_code == 404:
	arcpy.AddError(r.status_code)
	arcpy.AddError("Invalid Waterbody ID")
	quit()
elif r.status_code != 200:
	arcpy.AddError(r.status_code)
	arcpy.AddError("Error in running the tool.")
	arcpy.AddError(arcpy.GetMessages())
	quit()


##
##	Mapping Environment and Variables
##

# Outputs
try:
	out_folder = arcpy.GetParameterAsText(3)
	# Polygon path
	out_name = str(data.get("Id"))
	out_fc = out_folder + "\\" + out_name + ".shp"
	# Polyline path
	out_name_line = out_name + " Tracklines"
	out_fc_line = out_folder + "\\" + out_name_line + ".shp"
except:
	arcpy.AddError("Invalid File Name or Path")
	arcpy.AddError(arcpy.GetMessages())

# Mapping Environment
try:
	# Set up workspace
	env.workspace = out_folder
	env.overwriteOutput = True
	# Map document
	mxd = arcpy.mapping.MapDocument("CURRENT")
	df = arcpy.mapping.ListDataFrames(mxd)[0]
	# Spatial Reference
	sr = arcpy.SpatialReference(4326) # Code for WGS 84
except:
	arcpy.AddError("Error in generating mapping environment.")
	arcpy.AddError(arcpy.GetMessages())

##
##	Polygon Generation
##

try:
	# Create Polygon Geometry Object from JSON
	wkt_polygon = data.get("WaterbodyWkt")
	polygon_object = arcpy.FromWKT(wkt_polygon, sr)

	# Create fc
	arcpy.CopyFeatures_management(polygon_object, out_fc)
	arcpy.RepairGeometry_management(out_fc)

	# Add polygon to the map
	new_layer = arcpy.mapping.Layer(out_fc)
	arcpy.mapping.AddLayer(df, new_layer)
except:
	arcpy.AddError("Error in generating polygon.")
	arcpy.AddError(arcpy.GetMessages())

##
##	Generate Non-reviewed Tracklines from Admin Site
##

try:
	# Create Polyline Geometry Object from JSON
	wkt_polyline = data.get("TracklinesWkt")

	# If there are non-reviewed trips make a new shapefile
	if not wkt_polyline == []:

		# Empty Polyline
		arcpy.CreateFeatureclass_management(out_folder, out_name_line, "POLYLINE", "", "", "", sr) # Always a polyline

		with arcpy.da.InsertCursor(out_fc_line, ("SHAPE@",)) as cursor:
			for line in wkt_polyline:
				if line.startswith("GEOMETRYCOLLECTION") == False:
					line_object = arcpy.FromWKT(line, sr)
					cursor.insertRow((line_object,))

		# Add polyline to the map
		new_layer_line = arcpy.mapping.Layer(out_fc_line)
		arcpy.mapping.AddLayer(df, new_layer_line)
except:
	arcpy.AddError("Error in generating Tracklines.")
	arcpy.AddError(arcpy.GetMessages())
