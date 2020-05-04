import sys, os
import requests
from requests.auth import HTTPBasicAuth
import configparser
import xml.etree.ElementTree as ET

ID_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Id'
LABEL_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Label'
STATUS_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Status'

PROPERTIES_XP = '{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}content/{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties'

def get_config(filename):

    try:
        config = configparser.RawConfigParser()
        config.read(filename)

    except Exception as ex:
        raise Exception("Could not extract configuration from %s (%s)" % (filename, ex))

    return config

def get_hub_creds(filename):
    user = None;
    password = None
    hub = None

    if os.path.exists(filename):

        config = get_config(filename)

        try:
            hub = config.get('default', 'hub')
        except:
            hub = None

        user = config.get('default', 'user')
        password = config.get('default', 'password')

        return hub, user, password

    else:
        raise Exception("No such file: %s" % filename)

def get_sync_template(geo=False):

    if not geo:
        # template based on typical ceda sycnhronizer
        return '''<entry xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
            xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
            xmlns="http://www.w3.org/2005/Atom">
           <id>http://localhost:8080/odata/v1/Synchronizers(0L)</id>
           <title type="text">Synchronizer</title>
           <updated>2015-06-29T09:32:15.922Z</updated>
           <category term="DHuS.Synchronizer" scheme="http://schemas.microsoft.com/ado/2007/08/dataservices/scheme"/>
           <content type="application/xml">
              <m:properties>
                 <d:Schedule>D_SCHEDULE</d:Schedule>
                 <d:Request>D_REQUEST</d:Request>
                 <d:ServiceUrl>D_SERVICEURL</d:ServiceUrl>
                 <d:Label>D_LABEL</d:Label>
                 <d:ServiceLogin>D_SERVICELOGIN</d:ServiceLogin>
                 <d:ServicePassword>D_SERVICEPASSWORD</d:ServicePassword>
                 <d:PageSize>D_PAGESIZE</d:PageSize>
                 <d:LastCreationDate>D_LASTCREATIONDATE</d:LastCreationDate>
                 <d:CopyProduct>D_COPYPRODUCT</d:CopyProduct>
                 <d:FilterParam>D_FILTERPARAM</d:FilterParam>
              </m:properties>
           </content>
        </entry>'''

    else:
        return '''<entry xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
            xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
            xmlns="http://www.w3.org/2005/Atom">
           <id>http://localhost:8080/odata/v1/Synchronizers(0L)</id>
           <title type="text">Synchronizer</title>
           <updated>2015-06-29T09:32:15.922Z</updated>
           <category term="DHuS.Synchronizer" scheme="http://schemas.microsoft.com/ado/2007/08/dataservices/scheme"/>
           <content type="application/xml">
              <m:properties>
                 <d:Schedule>D_SCHEDULE</d:Schedule>
                 <d:Request>D_REQUEST</d:Request>
                 <d:ServiceUrl>D_SERVICEURL</d:ServiceUrl>
                 <d:Label>D_LABEL</d:Label>
                 <d:ServiceLogin>D_SERVICELOGIN</d:ServiceLogin>
                 <d:ServicePassword>D_SERVICEPASSWORD</d:ServicePassword>
                 <d:PageSize>D_PAGESIZE</d:PageSize>
                 <d:LastCreationDate>D_LASTCREATIONDATE</d:LastCreationDate>
                 <d:CopyProduct>D_COPYPRODUCT</d:CopyProduct>
                 <d:FilterParam>D_FILTERPARAM</d:FilterParam>
                <d:GeoFilter>D_GEOFILTER</d:GeoFilter>
              </m:properties>
           </content>
        </entry>'''

def post_to_hub(hub, hub_uname, hub_password, data, ):

    header = {"Content-type": "application/atom+xml",
              "Accept": "application/atom+xml"}

    # sys.exit()
    try:
        response = requests.post(hub, data = data, headers = header, auth = HTTPBasicAuth(hub_uname, hub_password))

        if response.status_code != 200 or response.status_code != 201:
            raise Exception(f"Incorrect response recieved (status: {response.status_code}; message: {response.content}")

        else:
            #print(f"\nSuccessfully posteded new synchronizer to {hub}")
            return response.content

    except Exception as ex:
        print(f"Unable to POST to SRH! ({ex})")
        return None

def get_synchronisers(hub_config):

    hub, hub_uname, hub_password = get_hub_creds(hub_config)

    response = requests.get(hub, auth=HTTPBasicAuth(hub_uname, hub_password))

    synchronisers = {}

    if response.status_code != 200:
        print(f"Incorrect response recieved (status: {response.status_code}; message: {response.content}")
        sys.exit()

    # parse xml response to get sycnhroniser names
    try:
        tree = ET.fromstring(response.content)

    except Exception as ex:
        print('Error: couldnt extract response as xml ({ex})')
        sys.exit()

    for sync in tree.findall(PROPERTIES_XP):
        id = sync.find(ID_XP).text
        label = sync.find(LABEL_XP).text
        status = sync.find(STATUS_XP).text

        synchronisers[label] = {'id': id, 'status': status}

    return synchronisers

def synchroniser_id_url(hub, id):
    return (f'{hub}({id})')