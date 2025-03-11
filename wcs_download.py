import requests
import json
from qgis.core import QgsRasterLayer, QgsProject
from urllib.error import HTTPError

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

#example mosaic ruleset
mosaic_rule = {
    "mosaicMethod": "esriMosaicNorthwest",
    "where": """
    (((UPPER(sub_theme_name) = 'AGRO-ECOLOGICAL ATTAINABLE YIELD ') 
    AND 
        (UPPER(variable) = 'AVERAGE ATTAINABLE YIELD OF BEST OCCURRING SUITABILITY CLASS IN GRID CELL') 
    AND 
        (UPPER(crop) = 'WHEAT') AND (UPPER(water_supply) = 'RAINFED')))""",
    "sortField": "",
    "ascending": True,
    "mosaicOperation": "MT_FIRST"
}

#example rendering rule
rendering_rule = {
    "rasterFunction": "Suitability and Attainable Yield Symbology",
}

WCS_URL = f"https://gaez-services.fao.org/server/services/{default_theme_service}/ImageServer/WCSServer"

COVERAGE_ID = f"{default_theme_service}_Suitability and Attainable Yield Symbology"

min_lon, min_lat, max_lon, max_lat = -179.99999999999997, -89.9999928, 179.9999856, 90

params = {
    "SERVICE": "WCS",
    "VERSION": "1.0.0",
    "REQUEST": "GetCoverage",
    "COVERAGE": COVERAGE_ID,
    "FORMAT": "GeoTIFF",
    "BBOX": f"{min_lon},{min_lat},{max_lon},{max_lat}",
    "CRS": "EPSG:4326",
    "RESOLUTION": "0.08333333", 
    "mosaicRule": json.dumps(mosaic_rule),
    "renderingRule": json.dumps(rendering_rule), 
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
    
    def send_wcs_request(self):
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            print('Received valid response from GAEZ WCS server...')
            return response
        
        raise HTTPError(code=response.status_code, message=f"Failed to send your request to WCS server")

def download_gaez_wcs():
    gaez_wcs_server = GaezWcsServer()
    response = gaez_wcs_server.send_wcs_request()
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

download_gaez_wcs()