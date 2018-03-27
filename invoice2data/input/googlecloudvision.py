# -*- coding: utf-8 -*-
def to_text(path, API_KEY=""):
    """
    Wrapper around Google Cloud Vision API.
    https://cloud.google.com/vision/docs/
    """
    import base64
    import json
    import requests

    with open(path, 'rb') as image_file:
        img = base64.b64encode(image_file.read()).decode('UTF-8')

    url = "https://vision.googleapis.com/v1/images:annotate?key=%s" % API_KEY

    data = json.dumps({
        "requests": [
            {
                "image": {
                    "content": img
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ]
            }
        ]
    })

    headers = {
        'Content-Type': "application/json",
    }

    response = requests.request("POST", url, data=data, headers=headers)

    extracted_str = response.json()['responses'][0]['fullTextAnnotation']['text'].replace('\n', ' ').encode("utf-8")

    return extracted_str
