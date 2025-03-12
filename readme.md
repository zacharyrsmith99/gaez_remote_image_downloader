# GAEZ Image Exporter for QGIS

This Python script allows you to download and visualize image data from the GAEZ (Global Agro-Ecological Zones) Image Server. The image is retrieved through an API call with specified parameters.

### Requirements

    Python 3.x
    Requests library (pip install requests)

### Usage
The package contains two main scripts:

1. main.py - This is the main script that allows you to download and visualize image data from the GAEZ Image Server.

## Troubleshooting

**Invalid Format Error in QGIS**: Ensure that the output_path file format is compatible with QGIS (e.g., .tif or .jpg). If there are issues with format compatibility, try converting the downloaded image using QGIS's processing tools or external utilities like GDAL.

**Parameter Errors**: If the server responds with a 400 error, check the parameters for mistakes or inconsistencies in the query string. The handle_error() function provides error messages for debugging.

### License

This project is licensed under the MIT License.