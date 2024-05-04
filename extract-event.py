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
    # sanitized_str = re.sub(r'<script\b[^>]*>(.*?)</script>', '', input_str, flags=re.IGNORECASE)
    clean_string = re.sub("[^0-9a-zA-Z\s]+", "", input_str)
    return clean_string.strip()

@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
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

    # return ("Hello World!", 200, headers)

    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'message' in request_json:
        name = sanitize_input(request_json['message'])
        tz = request_json['tz']
    else:
        return ('No event found', 204, headers)

    if name != "":
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            'gemini-pro',
            generation_config=genai.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.1,
            ))
        if tz != "":
            tz_info = "" # f" with a timezone of {tz}"
        else:
            tz_info = ""
        response = model.generate_content(f"Accurately extract event details in vcal format from the following text{tz_info}: {name}")
        # print(response.text)
    else:
        return ('No event found', 204, headers)

    # cal = Calendar(response.text)
    if "BEGIN:VCALENDAR" in response.text:
        qr = pyqrcode.create(response.text)
        buffer = io.BytesIO()
        qr.svg(buffer, scale=3.5, background="#fff", module_color="#0287d1", svgclass='qrcode', xmldecl=False)
        byte_str = buffer.getvalue()
        data = {'vcal': response.text, 'qr': byte_str.decode('UTF-8')}
        return (json.dumps(data), 201, headers)
    else:
        return ('No event found', 204, headers)
  
    # # elif request_args and 'message' in request_args:
    # #     name = request_args['message']
    # else:
    #     name = 'No event found'
    # return (f'Hello {name}', 200, headers)