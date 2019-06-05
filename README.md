# admin-shapefile-editor

This python script is intended to be loaded into ArcGIS as a tool for my coworkers to quickly pull shapefiles from our database. It will pull the Shapefile from the database, create an empty shapefile in the output folder, write the geometry from the database to the shapefile, and add the file to the current map document.

First the script must be edited to add an API to the url variable.

Second, in ArcGIS, add a new Script Tool to a toolbox,

This tool takes four parameters:
Username as a String
Password as a Hidden String
WaterbodyID as an Integer
Output Folder as a Folder
