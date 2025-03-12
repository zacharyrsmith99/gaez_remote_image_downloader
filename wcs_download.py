import requests
from qgis.core import QgsRasterLayer, QgsProject
import xml.dom.minidom

# Themes To Services
themes_to_services = {
    "Theme 1: Land and Water Resources": "LR",
    "Theme 2: Agro-climatic Resources": "res01",
    "Theme 3: Agro-climatic Potential Yield": "res02",
    "Theme 4: Suitability and Attainable Yield": "res05",
    "Theme 5: Actual Yields and Production": "res06",
    "Theme 6: Yield and Production Gaps": "res07",
}
default_theme_service = "res05"

WCS_URL = f"https://gaez-services.fao.org/server/services/{default_theme_service}/ImageServer/WCSServer"

COVERAGE_ID = f"{default_theme_service}_Suitability and Attainable Yield Symbology"

min_lon, min_lat, max_lon, max_lat = -179.99999999999997, -89.9999928, 179.9999856, 90

base_params = {
    "SERVICE": "WCS",
    "VERSION": "1.0.0",
    "COVERAGE": COVERAGE_ID,
}

output_path = r""
if not output_path:
    raise Exception('Need to input an output path!')

def handle_error(response):
    body = response.json()
    if 'error' in body:
        error = body['error']
        code = error['code']
        message = ''
        if 'message' in error:
            message = f" Message: {error['message']}"
        details = ''
        if 'details' in error:
            details = f" Details: {error['details']}"
        if code == 400:
            raise Exception(f"Error code {code} encountered in processing your parameters" + message + details)
        raise Exception(f"Error code {code} encountered in processing your request." + message + details)

class GaezWcsServer:
    def __init__(self):
        self.base_url = WCS_URL
    
    def send_wcs_request(self, params):
        response = requests.get(self.base_url, params)
        if response.status_code == 200:
            print('Received valid response from GAEZ WCS server...')
            return response
        raise Exception(f"Failed to send your request to WCS server. Received code: ({response.status_code}), {response.content}")

gaez_wcs_server = GaezWcsServer()

def describe_gaez_coverage():
    params = {
        **base_params,
        "REQUEST": "DescribeCoverage",
    }
    
    response = gaez_wcs_server.send_wcs_request(params)
    xml_str = response.content.decode("utf-8")
    pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    print(pretty_xml)

def get_gaez_capabilities():
    params = {
        **base_params,
        "REQUEST": "GetCapabilities",
    }
    
    response = gaez_wcs_server.send_wcs_request(params)
    xml_str = response.content.decode("utf-8")
    pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    print(pretty_xml)

def download_image():
    """
    Mosaic rules are IGNORED in WCS!
    """
    params = {
        **base_params,
        "REQUEST": "GetCoverage",
        "FORMAT": "GeoTIFF",
        "BBOX": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "CRS": "EPSG:4326",
        "RESOLUTION": "0.08333333",
    }
    response = gaez_wcs_server.send_wcs_request(params)
    with open(output_path, 'wb') as f:
        f.write(response.content)
    raster_layer = QgsRasterLayer(output_path, "WCS Coverage")
    
    """
    Adds the WCS coverage as a layer directly to your QGIS instance
    """
    if raster_layer.isValid():
        QgsProject.instance().addMapLayer(raster_layer)
        print("WCS raster layer successfully added to the map.")
    else:
        print("Invalid raster layer. Checking for error message...")
        try:
            handle_error(response)
        except:
            # Might be a binary response with error
            print(f"Failed to add WCS layer. Response content type: {response.headers.get('Content-Type')}")
            print(f"First 100 bytes: {response.content[:100]}")

download_image()