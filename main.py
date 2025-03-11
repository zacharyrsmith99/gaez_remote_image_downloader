import requests
import urllib.parse
from qgis.core import QgsRasterLayer, QgsProject
from urllib.error import HTTPError
import json

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

#example: full coordinates of pseudo mercator projection
whole_world_bbox = "-20037508.3427892,-20037508.3427892,20037508.3427892,20037508.3427892"

#example: mosaic ruleset
mosaic_rule = {
    "mosaicMethod": "esriMosaicNorthwest",
    "where": "(((UPPER(sub_theme_name) = 'AGRO-ECOLOGICAL ATTAINABLE YIELD ') AND (UPPER(variable) = 'AVERAGE ATTAINABLE YIELD OF BEST OCCURRING SUITABILITY CLASS IN GRID CELL') AND (UPPER(crop) = 'WHEAT') AND (UPPER(water_supply) = 'RAINFED')))",
    "sortField": "",
    "ascending": True,
    "mosaicOperation": "MT_FIRST"
}

#example: rendering rule
rendering_rule = {
    "rasterFunction": "Suitability and Attainable Yield Symbology",
}

#example size, this is the max size
size = "15000,41100"

params = {
    "f": "image",
    "bandIds": "",
    "renderingRule": json.dumps(rendering_rule),
    "mosaicRule": json.dumps(mosaic_rule),
    "bbox": whole_world_bbox,
    "imageSR": "102100",
    "bboxSR": "102100",
    "size": size,
}

output_path = r""

if not output_path:
    raise Exception('Need to input an output path!')
    


class GaezImageServer:
    def __init__(self):
        self.base_url = "https://gaez-services.fao.org/server/rest/services/" + default_theme_service + "/ImageServer/exportImage"
    
    def send_image_download_request(self):
        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{self.base_url}?{encoded_params}"
        response = requests.get(full_url)

        if response.status_code == 200:
            print('Received valid response from GAEZ image server...')
            return response
        
        raise HTTPError(code=response.status_code, message=f"Failed to send your request to web image server")
            

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

def download_gaez_image():
    gaez_image_server = GaezImageServer()

    response = gaez_image_server.send_image_download_request()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    raster_layer = QgsRasterLayer(output_path, "Exported Image")
    
    """
    Adds the image as a layer directly to your QGIS instance (assuming you're running within the QGIS application)
    """
    if raster_layer.isValid():
        QgsProject.instance().addMapLayer(raster_layer)
        print("Raster layer successfully added to the map.")
    else:
        handle_error(response)


download_gaez_image()
