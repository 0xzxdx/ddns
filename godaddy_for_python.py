import json
import re
import os
from sys import exit
from urllib import request
from urllib.error import HTTPError

# Begin settings
# Get the Production API key/secret from https://developer.godaddy.com/keys/.
# Ensure it's for "Production" as first time it's created for "Test".
KEY = None  # <API production key>
SECRET = None  # <API secret>

# set call API header
HEADERS = {
    "Accept": "application/json",
    'Content-type': 'application/json',
    'Authorization': 'sso-key {}:{}'.format(KEY, SECRET)
}

# Domain to update.
DOMAIN = None  # <domain name>

# Advanced settings - change only if you know what you're doing :-)
# Record type, as seen in the DNS setup page, default A.
TYPE = 'A'

# Record name, as seen in the DNS setup page, default @.
NAME = '@'

# Time To Live in seconds, minimum default 600 (10mins).
# If your public IP seldom changes, set it to 3600 (1hr) or more for DNS servers cache performance.
TTL = 600

# godaddy API URL
GOD_ADDY_API_URL = "https://api.godaddy.com/v1/domains/{}/records/{}/{}".format(DOMAIN, TYPE, NAME)

# Writable path to last known Public IP record cached. Best to place in tmpfs.
CACHED_IP_FILE = '/tmp/current_ip'
CACHED_IP = None
if os.path.isfile(CACHED_IP_FILE):
    CACHED_IP = open(CACHED_IP_FILE, mode="r", encoding="utf-8").read()

# External URL to check for current Public IP, must contain only a single plain text IP.
# Default http://api.ipify.org.
CHECK_URL = 'http://api.ipify.org'

if not KEY or not SECRET:
    print("Error: Requires API 'Key/Secret' value.")
    exit(1)

if not DOMAIN:
    print("Error: Requires 'Domain' value.")
    exit(1)

# Get Host Public IP
PUBLIC_IP = request.urlopen(CHECK_URL).read().decode('utf-8')
regex = r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$"
if re.search(regex, PUBLIC_IP):
    print("Get Public IP: {}".format(PUBLIC_IP))
else:
    print("Fail! Public IP: {}".format(PUBLIC_IP))
    exit(1)

# Check if the IP needs to be updated
if CACHED_IP != PUBLIC_IP:
    req = request.Request(GOD_ADDY_API_URL, headers=HEADERS)
    try:
        with request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            NAME_BIND_IP = data[0]["data"] if data else None
    except HTTPError as e:
        if e.code in (422, 404):
            NAME_BIND_IP = None
    if NAME_BIND_IP == PUBLIC_IP:
        print("unchanged! Current 'Public IP' matches 'GoDaddy' records. No update required!")
    else:
        print("changed! Updating '{}.{}', {} to {}".format(NAME, DOMAIN, NAME_BIND_IP, PUBLIC_IP))
        data = json.dumps([{"data": PUBLIC_IP, "name": NAME, "ttl": TTL, "type": TYPE}]).encode('utf-8')
        req = request.Request(GOD_ADDY_API_URL, data=data, headers=HEADERS, method='PUT')
        with request.urlopen(req) as response:
            print("Success!" if not response.read().decode('utf-8') else "Success!")
            open('/tmp/current_ip', mode="w", encoding="utf-8").write(PUBLIC_IP)
else:
    print("Current 'Public IP' matches 'Cached IP' recorded. No update required!")
