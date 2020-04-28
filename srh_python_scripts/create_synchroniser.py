#Script to replace shell script for update of SRH sycnhronizers.
# SJD April 2020

import sys, os
import requests
from requests.auth import HTTPBasicAuth
import datetime
import configparser

def get_hub_creds(filename):
    user = None;
    password = None
    hub = None

    if os.path.exists(filename):

        try:
            config = configparser.RawConfigParser()
            config.read(filename)

        except Exception as ex:
            raise Exception("Could not extract configuration from %s (%s)" % (filename, ex))

        try:
            hub = config.get('default', 'hub')
        except:
            hub = None

        user = config.get('default', 'user')
        password = config.get('default', 'password')

        return hub, user, password

    else:
        raise Exception("No such file: %s" % filename)

#template based on typical ceda sycnhronizer
sync_template_orig='''<entry xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
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

sync_template='''<entry xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
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
        <d:GeoFilter>'Intersects(POLYGON((-12.6 49.8,2.1 49.8,2.1 61.3,-12.6 61.3,-12.6 49.8)))'</d:GeoFilter>
      </m:properties>
   </content>
</entry>'''

#-D_SERVICELOGIN='dhr_uk_stfc' -D_SERVICEPASSWORD='oS9y8SBZ'
#./createSynchronizer -D_LABEL='S1B_IW_SLC' -D_SERVICEURL='https://colhub2.copernicus.eu/dhus/odata/v1' -D_SCHEDULE='0 */1 * * * ?'
# -D_PAGESIZE='10' -D_COPYPRODUCT='true' -D_FILTERPARAM="startswith(Name,'S1B_IW_GRDH_')" -D_REQUEST='start'
# -D_GEOFILTER='Intersects(POLYGON((-12.6 49.8,2.1 49.8,2.1 61.3,-12.6 61.3,-12.6 49.8)))'  -D_LASTCREATIONDATE='2020-04-22T00:00:00'

if len(sys.argv) != 5:
    print (f"Usage: {os.path.basename(sys.argv[0])} <sync params file> <creds for hub the synchroniser will run ON> <creds for hub synchroninising FROM>  <last creation date.\
      Use 'None' and will set to 00:00:00 of todays date.  Note format YYYY-MM-DDTHH:MM:SS>")
    sys.exit()

params_file = sys.argv[1] # params file
this_hub_creds = sys.argv[2] #creds for hub synchroninising FROM
source_hub_creds = sys.argv[3] # creds for hub the synchroniser will run ON
lastcreationdate = sys.argv[4] #last creation date.  Use "None" and will set to 00:00:00 of todays date.  Note format YYYY-MM-DDTHH:MM:SS

#todo: NOTE- source url is already in s1b_iw_grdh_UKonly file
src_hub, src_uname, src_password = get_hub_creds(source_hub_creds)

#todo: NOTE- source url is already in s1b_iw_grdh_UKonly file
hub, hub_uname, hub_password = get_hub_creds(this_hub_creds)

if os.path.exists(params_file):

    with open(params_file, 'r') as reader:
        params = [i.strip() for i in reader.readlines()]

for line in params:
    hook=line.split("=")[0]
    value=line.split("=")[1]

    sync_template = sync_template.replace(hook,value)

#remove geofilter line if not needed
if 'D_GEOFILTER' not in params:
    sync_template = sync_template.replace('D_GEOFILTER', 'D_GEOFILTER_NULL')

#label
label=(f"{os.path.basename(params_file)}_{datetime.datetime.now().strftime('%d%m%YT%H%M%S')}")
sync_template = sync_template.replace('D_LABEL', label)

#source hub
sync_template = sync_template.replace('D_SERVICELOGIN', src_uname)
sync_template = sync_template.replace('D_SERVICEPASSWORD', src_password)

#last creation date
if lastcreationdate is None or lastcreationdate == 'None' or lastcreationdate == 'none':
    lcd = datetime.datetime.now().strftime('%Y-%m-%dT00:00:00')

else:
    lcd = lastcreationdate

sync_template = sync_template.replace('D_LASTCREATIONDATE', lcd)

print (sync_template)


#Now post to SRH hub.

header = {"Content-type": "application/atom+xml",
              "Accept": "application/atom+xml"}

#sys.exit()
try:
    response = requests.post(hub, data = sync_template, headers=header,  auth=HTTPBasicAuth(hub_uname, hub_password))

    if response.status_code != 200 or response.status_code != 201:
        raise Exception (f"Incorrect response recieved (status: {response.status_code}; message: {response.content}")

    else:
        print (f"\nSuccessfully posted new synchronizer ({params_file}) to {hub}")

        print (response.content)

except Exception as ex:
    print (f"Unable to POST synchronizer to SRH! ({ex})")
