import sys, re, urllib
'''
Script to extract SUCCESSFULLY synchronised data from a hub log and index by source and unique ids.

Use as a basis for analysing hub delays as extracts UID's etc which other (older) scripts do not
'''


'''#grep  'successfully downloaded from' /srh/data/logs/dhus.log | grep S3B_SL_1_RBT  
| awk '{print $12}' | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" 
| sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}' | sort -u'''

log = sys.argv[1]

with open(log, 'r') as f:
    lines = [i.rstrip() for i in f.readlines()]

#index by source i.e. hub
successful_syncs = {}

uids = []
cnt = 0
bad_cnt = 0
for line in lines:
    if 'Products(' in line and 'successfully downloaded' in line and '.zip' in line:

        try:
            uid = re.findall("'([a-zA-Z0-9-]*)'", line)[0]
            product = re.findall("S[1-3][A-B].*\.zip", line)[0][0:12]
            hub = urllib.parse.urlparse(re.findall('https.*/Products', line)[0]).netloc

            #prime a data struct if needed
            if hub not in successful_syncs.keys():
                successful_syncs[hub] = {'uids':[], 'products':[]}

            if product not in successful_syncs[hub]['products']:
                successful_syncs[hub]['products'].append(product)

            if uid not in successful_syncs[hub]['uids']:
                successful_syncs[hub]['uids'].append(uid)
            cnt += 1

        except:
            #todo something wrong with the log parsing etc.  deal with it later
            bad_cnt +=1

#print (f"len: {len(lines)} num uids: {len(uids)} cnt:{cnt}")
print (f"Synchronised from {len(successful_syncs.keys())} Hubs")
for i in successful_syncs.keys():
    data_prods = [j for j in successful_syncs[i]['products']]
    print (f"Hub: {i} Products synchronised: {len(successful_syncs[i]['uids'])} Data products: {data_prods}")

print (f"Bad lines: {bad_cnt}")

#todo: summarise by acq date etc and run so can get publication delay using report publication delay.