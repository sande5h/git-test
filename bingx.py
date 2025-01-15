
import os
import hmac
from hashlib import sha256
import requests
import time
from dotenv import load_dotenv
load_dotenv()


API_URL = "https://open-api-vst.bingx.com"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    # print("sign=" + signature)
    return signature


def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (API_URL, path, urlpa, get_sign(API_SECRET, urlpa))
    headers = {
        'X-BX-APIKEY': API_KEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    if response.status_code != 200:
        print(response.status_code , response.text)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "":
     return paramsStr+"&timestamp="+str(int(time.time() * 1000))
    else:
     return paramsStr+"timestamp="+str(int(time.time() * 1000))


def call_bingx( payload : dict , path : str , method : str , paramsMap : dict ):
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload)
