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

"""
I added basic formatting to the where clause, but I believe it cares about string newlines.
So, I just put it all on one line. If you use more complex conditions, you can do so, but
be careful not to break the syntax. The error message is not very helpful if your mosaic where clause is incorrect.
"""
example_mosaic_rule = {
    "mosaicMethod": "esriMosaicNorthwest",
    "where": [
        "UPPER(sub_theme_name) = 'AGRO-ECOLOGICAL ATTAINABLE YIELD '", # this space at the end actually matters...
        "UPPER(variable) = 'AVERAGE ATTAINABLE YIELD OF BEST OCCURRING SUITABILITY CLASS IN GRID CELL'",
        "UPPER(crop) = 'WHEAT'",
        "UPPER(water_supply) = 'RAINFED'"
    ],
    "sortField": "",
    "ascending": True,
    "mosaicOperation": "MT_FIRST",
}

example_rendering_rule = {
    "rasterFunction": "Suitability and Attainable Yield Symbology",
}

default_theme_service = "res05"

whole_world_bbox = "-180,-90,180,90" # for 4326 spatial reference

max_size = "15000,4100"  # may distort the coordinates

# returns a list of unique crops
example_query_params = {
    "outFields": "crop",
    "returnGeometry": False,
    "returnDistinctValues": True,
    "returnCountOnly": False,
    "f": "json"
}

output_path = "gaez_wheat_yield.tif"
if not output_path:
    raise Exception("Need to input an output path!")


def handle_error(response: requests.Response):
    body = response.json()
    if "error" in body:
        error = body["error"]
        code = error["code"]
        message = ""
        if "message" in error:
            message = f" Message: {error['message']}"
        details = ""
        if "details" in error:
            details = f" Details: {error['details']}"
        if code == 400:
            raise Exception(
                f"Error code {code} encountered in processing your parameters"
                + message
                + details
            )
        raise Exception(
            f"Error code {code} encountered in processing your request."
            + message
            + details
        )


class GaezeImageClient:
    def __init__(self):
        self.base_url = (
            "https://gaez-services.fao.org/server/rest/services/"
            + default_theme_service
            + "/ImageServer"
        )
    
    def format_mosaic_where_clause(self, mosaic_rule):
        example_mosaic_rule = ""
        if "where" in mosaic_rule:
            for i, string in enumerate(mosaic_rule["where"]):
                if i == 0:
                    example_mosaic_rule += f"({string})"
                else:
                    example_mosaic_rule += f" AND ({string})"
        return example_mosaic_rule

    def construct_export_image_params(self, params):
        """
        Constructs the parameters for the export image request.

        Args:
            params (dict): The parameters for the export image request.
            params["format"] (str): The format of the image to export. Can be: jpgpng | png | png8 | png24 | jpg | bmp | gif | tiff | png32 | bip | bsq | lerc
            params["bbox"] (str): The bounding box of the image to export.
            params["size"] (str): The size of the image to export.
            params["renderingRule"] (dict): The rendering rule for the image to export.
            params["mosaicRule"] (dict): The mosaic rule for the image to export.
            params["bandIds"] (str): The band IDs to export.
            params["renderingRule"] (dict): The rendering rule for the image to export.
            params["mosaicRule"] (dict): The mosaic rule for the image to export.
            params["f"] (str): The format of the image to export. Can be: json | image | kmz | html
        Returns:
            dict: The parameters for the export image request.
        """
        export_params = {}
        if "renderingRule" in params:
            export_params["renderingRule"] = json.dumps(params["renderingRule"])
        if "mosaicRule" in params:
            mosaic_where_clause = self.format_mosaic_where_clause(params["mosaicRule"])
            params["mosaicRule"]["where"] = mosaic_where_clause
            export_params["mosaicRule"] = json.dumps(params["mosaicRule"])
        if "bandIds" in params:
            export_params["bandIds"] = params["bandIds"]
        if "imageSR" in params:
            export_params["imageSR"] = params["imageSR"]
        if "bboxSR" in params:
            export_params["bboxSR"] = params["bboxSR"]
        if "format" in params:
            export_params["format"] = params["format"]
        if "f" in params:
            export_params["f"] = params["f"]
        if "bbox" in params:
            export_params["bbox"] = params["bbox"]
        if "size" in params:
            export_params["size"] = params["size"]
        if "imageSR" in params:
            export_params["imageSR"] = params["imageSR"]
        if "bboxSR" in params:
            export_params["bboxSR"] = params["bboxSR"]
        return export_params

    def export_image(self, params):
        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{self.base_url}/exportImage?{encoded_params}"
        response = requests.get(full_url)

        if response.status_code == 200:
            print("Received valid response from GAEZ image server...")
            return response

        handle_error(response)
    
    def query(self, query_params):
        """
        Used to get data bout the image server.
        
        Fields:
            objectid ( type: esriFieldTypeOID, alias: OBJECTID )
            name ( type: esriFieldTypeString, alias: Name, length: 200 )
            category ( type: esriFieldTypeInteger, alias: Category , Coded Values: [0: Unknown] , [1: Primary] , [2: Overview] , ...6 more... )
            filepath ( type: esriFieldTypeString, alias: Path to File, length: 255 )
            sub_theme_name ( type: esriFieldTypeString, alias: Sub-Theme Name, length: 255 )
            variable ( type: esriFieldTypeString, alias: Variable Name, length: 255 )
            file_description ( type: esriFieldTypeString, alias: Description, length: 1000 )
            year ( type: esriFieldTypeString, alias: Time Period, length: 255 )
            model ( type: esriFieldTypeString, alias: Climate Model, length: 255 )
            rcp ( type: esriFieldTypeString, alias: RCP, length: 255 )
            crop ( type: esriFieldTypeString, alias: Crop, length: 255 )
            water_supply ( type: esriFieldTypeString, alias: Water Supply, length: 255 )
            input_level ( type: esriFieldTypeString, alias: Input Level, length: 255 )
            c02_fertilization ( type: esriFieldTypeString, alias: CO2 Fertilization, length: 255 )
            units ( type: esriFieldTypeString, alias: Data Units, length: 255 )
            renderer ( type: esriFieldTypeString, alias: Recommended Renderer, length: 255 )
            download_url ( type: esriFieldTypeString, alias: Download URL, length: 1000 )
            shape ( type: esriFieldTypeGeometry, alias: Shape )
            file_id ( type: esriFieldTypeString, alias: File Identifier, length: 255 )
        """
        
        query_url = f"{self.base_url}/query"
        response = requests.get(query_url, params=query_params)
        if response.status_code == 200:
            return response.json()
        handle_error(response)


gaez_image_client = GaezeImageClient()


def download_gaez_image():
    mosaic_rule = example_mosaic_rule  # set to your mosaic rule
    rendering_rule = example_rendering_rule  # set to your rendering rule
    bbox = whole_world_bbox  # set to your bbox
    size = "4000, 2000"  # set to your size
    format = "tiff"  # set to your format
    f = "image"  # set to your format
    imageSR = 4326  # set to your image spatial reference
    bboxSR = 4326  # set to your bbox spatial reference
    bandIds = ""  # set to your bandIds

    params = gaez_image_client.construct_export_image_params(
        {
            "mosaicRule": mosaic_rule,
            "renderingRule": rendering_rule,
            "bbox": bbox,
            "size": size,
            "format": format,
            "f": f,
            "bandIds": bandIds,
            "imageSR": imageSR,
            "bboxSR": bboxSR,
        }
    )

    response = gaez_image_client.export_image(params)
    if len(response.content) == 0:
        raise Exception("No content returned from server! Check your parameters.")
    elif len(response.content) < 1000:
        print(f"Bytes content is less than 1000, likely an error, checking... (please disable this check in the code if you are expecting a small response)")
        handle_error(response)

    """
    The image is exported as a TIFF file by default, however the format can be changed to PNG, JPG, etc.
    The "f" is also a formatter for the response - it determines how the server will send the image.
    If you select "image" it will stream the image to the client, however the image will not include metadata.
    If you want metadata, you need to select either json or html. 
    When you select json, the server will return a JSON object with the image metadata, including an href to the image. I have
    included a way to download the image using the href below.
    """
    if f == "image":
        try:
            with open(output_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"Error writing image to file: {e}")
        print(f"Image {output_path} saved successfully!")
        return
    elif f == "json":
        try:
            json_data = response.json()

            if "href" in json_data:
                image_url = json_data["href"]
                print(f"Image URL: {image_url}")

                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(image_response.content)
                    print(f"Image {output_path} saved successfully!")
                else:
                    print(
                        f"Failed to download image from URL: {image_response.status_code}"
                    )
            else:
                print("No 'href' field found in the JSON response")
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
    elif f == "html":
        print(response.content)
    else:
        raise Exception(f"Invalid format: {f}, please use 'image', 'json', or 'html'")


download_gaez_image()