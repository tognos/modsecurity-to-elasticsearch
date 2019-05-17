#!/usr/bin/env python
#
# .====================================================.
# | ModSecurity Audit Log to Elasticsearch             |
# | ---------------------------------------            |
# | Author: Andrea (theMiddle) Menin                   |
# | Twitter: https://twitter.com/Menin_TheMiddle       |
# | GitHub: https://github.com/theMiddleBlue           |
# '===================================================='
#

import sys, os, getopt, json, time
from datetime import datetime,date
from elasticsearch import Elasticsearch

# Please, check the elasticsearch URL below:
es = Elasticsearch([os.environ.get('ES_URL')])

# parse arguments
opts, args = getopt.getopt(sys.argv[1:],"hd:",["help","log-directory="])
for i in opts:
    if i[0] == "-d" or i[0] == "--log-directory":
        basedir = i[1]

# set headers name to lowercase
def renameKeys(iterable):
    if type(iterable) is dict:
        for key in iterable.keys():
            iterable[key.lower()] = iterable.pop(key)
            if type(iterable[key.lower()]) is dict or type(iterable[key.lower()]) is list:
                iterable[key.lower()] = renameKeys(iterable[key.lower()])
    elif type(iterable) is list:
        for item in iterable:
            item = renameKeys(item)
    return iterable

# parsing...
def parseLogFile(file):
	# define the index mapping
	settings = {
		"settings": {
			"number_of_shards": 1,
			"number_of_replicas": 0
		},
		"mappings": {
				"properties": {
					"unixts": { "type": "date" },
                                        "client_ip": { "type": "ip" },
                                        "host_ip": { "type": "ip" },
                                        "request": { "properties": {
                                            "headers":{ "properties": {
                                                "x-forwarded-for": { "type": "ip" },
                                                "x-real-ip": { "type": "ip" }
                                                } }
                                            } },
                                        "response": { "properties": {
                                            "headers": { "properties": {
                                                "http_code": {"type": "keyword"}
                                            } }
                                        } }
                                        
				}
		}
	}

	# set all dict keys to lower
	d = renameKeys(json.load(open(file)))

	# create a unixts field as a timestamp field
	d['transaction']['unixts'] = int(d['transaction']['unique_id'][0:14].replace('.',''))

	# create 1 index per day... you could change it
	# if you need to store all logs in a single index:
	index = 'modsecurity_' + str(date.today()).replace('-','')

	# because objects in array are not well supported,
	# redefine all "messages" params and values in "msg"
	new_messages = []
	new_ruleid = []
	new_tags = []
	new_file = []
	new_linenumber = []
	new_data = []
	new_match = []
	new_severity = []

	d['transaction']['msg'] = {}

	for i in d['transaction']['messages']:
		new_messages.append(i['message'])
		new_ruleid.append(i['details']['ruleid'])

		for tag in i['details']['tags']:
			if tag not in new_tags:
				new_tags.append(tag)

		new_file.append(i['details']['file'])
		new_linenumber.append(i['details']['linenumber'])
		new_data.append(i['details']['data'])
		new_match.append(i['details']['match'])
		new_severity.append(i['details']['severity'])

	d['transaction']['msg']['message'] = new_messages
	d['transaction']['msg']['ruleid'] = new_ruleid
	d['transaction']['msg']['tags'] = new_tags
	d['transaction']['msg']['file'] = new_file
	d['transaction']['msg']['linenumber'] = new_linenumber
	d['transaction']['msg']['data'] = new_data
	d['transaction']['msg']['match'] = new_match
	d['transaction']['msg']['severity'] = new_severity

	# remove old messages list
	del d['transaction']['messages']

	# if index exists noop, else create it with mapping
	if es.indices.exists(index):
		indexexists=True
	else:
		es.indices.create(index=index, ignore=400, body=settings)

	# write the log
	res = es.index(index=index, body=d['transaction'])

	# check if log has been created
	if res['result'] == 'created':		
		os.remove(file)
		print("Parsed "+str(file))
	else:
		print("Warning: log not created:")
		print(res)
while True:
	for root, subFolders, files in os.walk(basedir):
		for file in files:
			logfile = os.path.join(root, file)
			parseLogFile(file=logfile)

	print("Sleeping for a while...")
	time.sleep(5)
