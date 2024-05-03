import functions_framework
import os
import re
import pyqrcode
from io import BytesIO
import google.generativeai as genai
import json
from PIL import Image
import base64


key = os.environ.get("api_key", "")
# origin = '*'
origin = 'http://apps.videre.us'


@functions_framework.http
def hello_http(request):
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            f"Access-Control-Allow-Origin": f"{origin}",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type, x-api-key",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": f"{origin}", 'Content-Type': 'application/json'}

    content_type = request.headers["content-type"]
    print(content_type)
    if content_type == "application/json":
        request_json = request.get_json(silent=True)
        if request_json and "name" in request_json:
            name = request_json["name"]
        else:
            raise ValueError("JSON is invalid, or missing a 'name' property")
    elif content_type == "application/octet-stream":
        name = request.data
    elif content_type == "text/plain":
        name = request.data
    elif content_type == "application/x-www-form-urlencoded":
        name = request.form.get("name")
    elif content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        for field in data:
            print("Processed field: %s" % field)
            print(data[field])
            image_data = re.sub('^data:image/.+;base64,', '', data[field])
            imageBytes = Image.open(BytesIO(base64.b64decode(image_data)))
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-pro-vision')
            response = model.generate_content(["OCR image and Extract event details in vcal format from the image text", imageBytes], stream=True)
            response.resolve()
            print(response.text)

            if "BEGIN:VCALENDAR" in response.text:
                qr = pyqrcode.create(response.text)
                buffer = BytesIO()
                qr.svg(buffer, scale=3.5, background="#fff", module_color="#0287d1", svgclass='qrcode', xmldecl=False)
                byte_str = buffer.getvalue()
                data = {'vcal': response.text, 'qr': byte_str.decode('UTF-8'), 'txt': response.text}
                return (json.dumps(data), 201, headers)
            else:
                return ('No event found', 204, headers)
        return (response.text, 201, headers)
    else:
        raise ValueError(f"Unknown content type: {content_type}")
    return f"Hello {name}!"
    
