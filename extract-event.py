import functions_framework
import os
import re
import pyqrcode
import io
import google.generativeai as genai
import json

key = os.environ.get("api_key", "")
# origin = '*'
origin = 'http://apps.videre.us'

def sanitize_input(input_str):
    # Regular expression to blocklist script tags
    clean_string = re.sub("[^0-9a-zA-Z\s]+", "", input_str)
    return clean_string.strip()

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

    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'message' in request_json:
        name = sanitize_input(request_json['message'])
        tz = request_json['tz']
    else:
        return ('No event found', 204, headers)

    if name != "":
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-pro')
        if tz != "":
            tz_info = "" # f" with a timezone of {tz}"
        else:
            tz_info = ""
        response = model.generate_content(f"Extract event details in vcal format from the following texts{tz_info}: {name}")
    else:
        return ('No event found', 204, headers)

    if "BEGIN:VCALENDAR" in response.text:
        qr = pyqrcode.create(response.text)
        buffer = io.BytesIO()
        qr.svg(buffer, scale=3.5, background="#fff", module_color="#0287d1", svgclass='qrcode', xmldecl=False)
        byte_str = buffer.getvalue()
        data = {'vcal': response.text, 'qr': byte_str.decode('UTF-8')}
        return (json.dumps(data), 201, headers)
    else:
        return ('No event found', 204, headers)
  