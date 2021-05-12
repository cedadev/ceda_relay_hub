import sys, os
import requests
from requests.auth import HTTPBasicAuth
import configparser
import xml.etree.ElementTree as ET
import datetime

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ID_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Id'
LABEL_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Label'
STATUS_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Status'
LASTCREATIONDATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}LastCreationDate'
SERVICEURL_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}ServiceUrl'

ENTRY_XP = '{http://www.w3.org/2005/Atom}entry'
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

def get_evict_template():

    base_template = '''<a:entry>
        <a:id>Evictions('S1A_Evictor_30102020')</a:id>
        <a:title/>
        <a:summary/>
        <a:updated>2021-05-11T15:22:54Z</a:updated>
        <a:author>
        <a:name/>
        </a:author>
        <a:link rel="edit" href="Evictions('S1A_Evictor_30102020')"/>
        <a:category scheme="http://docs.oasis-open.org/odata/ns/scheme" term="#OData.DHuS.Eviction"/>
            <a:content type="application/xml">
                <m:properties>
                    <d:Name>D_NAME</d:Name>
                    <d:KeepPeriod m:type="Int32">D_KEEP_PERIOD</d:KeepPeriod>
                    <d:KeepPeriodUnit>D_KEEP_PERIOD_UNIT</d:KeepPeriodUnit>
                    <d:MaxEvictedProducts m:type="Int32">D_MAX_PRODUCTS</d:MaxEvictedProducts>
                    <d:Filter>D_FILTERPARAM</d:Filter>
                    <d:SoftEviction m:type="Boolean">D_SOFT_EVICTION</d:SoftEviction>
                    <d:Cron m:type="#OData.DHuS.Cron">
                        <d:Active m:type="Boolean">D_ACTIVE</d:Active>
                        <d:Schedule>D_SCHEDULE</d:Schedule>
                    </d:Cron>
                    </m:properties>
            </a:content>
        </a:entry>'''

    return base_template

def get_sync_template(geo = False, remote_incoming = False):

    base_template = '''<entry xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
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
                 D_REMOTEINCOMING
                 D_GEOFILTER
              </m:properties>
           </content>
        </entry>'''

    if remote_incoming:
        base_template = base_template.replace('D_REMOTEINCOMING','<d:RemoteIncoming>D_REMOTEINCOMING</d:RemoteIncoming>')

    else:
        base_template= base_template.replace('D_REMOTEINCOMING', '')

    if geo:
        base_template= base_template.replace('D_GEOFILTER', '<d:GeoFilter>D_GEOFILTER</d:GeoFilter>')

    else:
        base_template= base_template.replace('D_GEOFILTER', '')

    return base_template

def POST_to_hub(hub, hub_uname, hub_password, data, PUT = False, synchroniser_id = None ):

    header = {"Content-type": "application/atom+xml",
              "Accept": "application/atom+xml"}

    acceptable_dhus_return_codes = [200, 201, 202, 203, 204]

    hub = synchroniser_id_url(hub, id = synchroniser_id)

    # sys.exit()
    try:

        if not PUT:
            response = requests.post(hub, data = data, headers = header, auth = HTTPBasicAuth(hub_uname, hub_password), verify=False)

        else:
            response = requests.put(hub, data=data, headers=header, auth=HTTPBasicAuth(hub_uname, hub_password),verify=False)

        if response.status_code not in acceptable_dhus_return_codes:
            raise Exception(f"Incorrect response recieved (status: {response.status_code}; message: {response.content}")

        else:
            #print(f"\nSuccessfully posteded new synchronizer to {hub}")
            return response.content

    except Exception as ex:
        print(f"Unable to POST to SRH! ({ex})")
        return None

def GET_from_hub(hub_config, odata_stub=None):

    hub, hub_uname, hub_password = get_hub_creds(hub_config)

    #add stub if needed
    if odata_stub:
        hub = f"{hub}/{odata_stub}"

    return requests.get(hub, auth=HTTPBasicAuth(hub_uname, hub_password), verify=False)

def PUT_to_hub_DEP(hub_config, template):

    hub, hub_uname, hub_password = get_hub_creds(hub_config)

    return requests.put(url, auth=HTTPBasicAuth(hub_uname, hub_password))

def get_existing_details(content):

    # parse xml response to get sycnhroniser names
    try:
        return ET.fromstring(content)

    except Exception as ex:
        print(f'Error: couldnt extract response as xml ({ex})')
        sys.exit()

    #tree = parse_response(xml)

def synchroniser_summary(tree):
    #summarise whats in the sync hub response response

    synchronisers = {}

    for sync in tree.findall(PROPERTIES_XP):
        id = sync.find(ID_XP).text
        label = sync.find(LABEL_XP).text
        status = sync.find(STATUS_XP).text
        last_creation_date = sync.find(LASTCREATIONDATE_XP).text
        service_url = sync.find(SERVICEURL_XP).text

        synchronisers[label] = {'id': id, 'status': status, 'lcd': last_creation_date, 'url': service_url}

    return synchronisers

def generate_element_xml(idval, operation):
    #Method to generate a new xml element snippet to submit to the synchroniser as ElementTree remove is crap.

    '''
    <ns0:entry xmlns:ns0="http://www.w3.org/2005/Atom"
    xmlns:ns1="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
    xmlns:ns2="http://schemas.microsoft.com/ado/2007/08/dataservices">
    <ns0:id>http://localhost:8080/odata/v1/Synchronizers(3)</ns0:id>
    <ns0:title type="text">Synchronizer</ns0:title>
    <ns0:updated>2020-05-06T09:28:08.871Z</ns0:updated>
    <ns0:category scheme="http://schemas.microsoft.com/ado/2007/08/dataservices/scheme"
        term="DHuS.Synchronizer"/>
    <ns0:content type="application/xml">
        <ns1:properties>
            <ns2:Request>start</ns2:Request>
        </ns1:properties>
    </ns0:content>
</ns0:entry>

    '''

    root = ET.Element('{http://www.w3.org/2005/Atom}entry')
    id = ET.SubElement(root, "{http://www.w3.org/2005/Atom}id")
    id.text = f"http://localhost:8080/odata/v1/Synchronizers({idval})"

    title = ET.SubElement(root, "{http://www.w3.org/2005/Atom}title", type='text')
    title.text = 'Synchronizer'

    updated = ET.SubElement(root, "{http://www.w3.org/2005/Atom}updated")
    updated.text = datetime.datetime.now().strftime('%Y-%m-%dT%H%M%SZ')

    category = ET.SubElement(root, "{http://www.w3.org/2005/Atom}category", attrib={'scheme':'http://schemas.microsoft.com/ado/2007/08/dataservices/scheme', 'term':'DHuS.Synchronizer'})

    content = ET.SubElement(root, "{http://www.w3.org/2005/Atom}content", attrib={"type":"application/xml"})

    properties = ET.SubElement(content, "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties")

    request = ET.SubElement(properties , "{http://schemas.microsoft.com/ado/2007/08/dataservices}Request")

    request.text = operation

    return root

def synchroniser_entries_request(tree, request = 'stop'):
    #Method to extract entries and return sub element with appropriate request value changed and link elements removed so appropriate for submission to hub
    #returns as a dict of series of xml snippets with keys relevant synchrohiser id.

    entries = {}

    #REQUEST_XP = '{http://www.w3.org/2005/Atom}content/{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}Request'
    REQUEST_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices}Request'
    LINK_XP = '{http://www.w3.org/2005/Atom}link'

    props_xp = '{http://www.w3.org/2005/Atom}content/{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties'
    id_xp = f"{props_xp}/{ID_XP}"
    req_xp = f"{props_xp}/{REQUEST_XP}"

    props_xp_subel = f"{props_xp}/*"

    #remove all content apart from request - works without this
    for el in tree.findall(f"{ENTRY_XP}"):
        id = el.find(id_xp).text

        '''
        #thisel_xp = f"{PROPERTIES_XP}/{el.tag}"
        #el.text = request
        el.find(req_xp).text = request

        for subel in el.find(props_xp).getchildren():
            if subel.tag != REQUEST_XP:
                el.remove(subel)

            else:
                print ("here")                
        '''
        #easier to just damn well create your own
        content = generate_element_xml(id, request)

        #NOTE - need to deal with bug where et tostring returns bytestring
        #content = ET.tostring(el, encoding='UTF-8')
        dcontent = ET.tostring(content, encoding='UTF-8')

        entries[id] = str(dcontent)[2:-1]

    return entries

def get_synchronisers(hub_config):
    #get full response from hub on all synchronisers

    response = GET_from_hub(hub_config, odata_stub='Synchronizers')

    if response.status_code not in [200,202]:
        raise Exception (f"Problem accessing hub (error {response.status_code})")

    return get_existing_details(response.content)

def synchroniser_id_url(hub, id=None):

    #make sure that the hub url includes the synchronusers endpoint
    if os.path.basename(hub) != 'Synchronizers':
        hub = f'{hub}/Synchronizers'

    if id:
        return (f'{hub}({id})')
    else:
        return hub