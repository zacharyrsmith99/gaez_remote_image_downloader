import requests
import json
import urllib.parse
import base64

# Themes To Services
themes_to_services = {
    "Theme 1: Land and Water Resources": "LR",
    "Theme 2: Agro-climatic Resources": "res01",
    "Theme 3: Agro-climatic Potential Yield": "res02",
    "Theme 4: Suitability and Attainable Yield": "res05",
    "Theme 5: Actual Yields and Production": "res06",
    "Theme 6: Yield and Production Gaps": "res07",
}

example_mosaic_rule = {
    "mosaicMethod": "esriMosaicNorthwest",
    "where": "(((UPPER(sub_theme_name) = 'AGRO-ECOLOGICAL ATTAINABLE YIELD ') AND (UPPER(variable) = 'AVERAGE ATTAINABLE YIELD OF BEST OCCURRING SUITABILITY CLASS IN GRID CELL') AND (UPPER(crop) = 'WHEAT') AND (UPPER(water_supply) = 'RAINFED')))",
    "sortField": "",
    "ascending": True,
    "mosaicOperation": "MT_FIRST"
}

example_rendering_rule = {
    "rasterFunction": "Suitability and Attainable Yield Symbology",
}

default_theme_service = "res05"

whole_world_bbox = "-180,-90,180,90"

max_size = "15000,4100"

output_path = ""
if not output_path:
    raise Exception('Need to input an output path!')

def handle_error(response: requests.Response):
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


class GaezeImageClient:
    def __init__(self):
        self.base_url = "https://gaez-services.fao.org/server/rest/services/" + default_theme_service + "/ImageServer"

    def construct_export_image_params(self, params):
        params = {
            "f": "json",
            "bandIds": "",
            "renderingRule": json.dumps(params["renderingRule"]),
            "mosaicRule": json.dumps(params["mosaicRule"]),
            "bbox": params["bbox"],
            "size": params["size"],
            "format": "tiff",
        }
        return params

    def export_image(self, params):
        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{self.base_url}/exportImage?{encoded_params}"
        response = requests.get(full_url)
        
        if response.status_code == 200:
            print('Received valid response from GAEZ image server...')
            return response
        
        handle_error(response)
    

gaez_image_client = GaezeImageClient()


def download_gaez_image():
    mosaic_rule = example_mosaic_rule # set to your mosaic rule
    rendering_rule = example_rendering_rule # set to your rendering rule
    bbox = whole_world_bbox # set to your bbox
    size = max_size # set to your size

    params = gaez_image_client.construct_export_image_params(
        {
            "mosaicRule": mosaic_rule, 
            "renderingRule": rendering_rule, 
            "bbox": bbox, 
            "size": size
        }
    )

    response = gaez_image_client.export_image(params)
    
    if response and response.status_code == 200:
        try:
            json_data = response.json()
            print(json_data)
            print("JSON response:", json_data)
            
            if 'href' in json_data:
                image_url = json_data['href']
                print(f"Image URL: {image_url}")
                
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(image_response.content)
                    print("Image saved successfully")
                else:
                    print(f"Failed to download image from URL: {image_response.status_code}")
            else:
                print("No 'href' field found in the JSON response")
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
    else:
        print("Failed to get response from server")

download_gaez_image()