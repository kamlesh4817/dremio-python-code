#!/usr/bin/python3
import json
import sys

#get file name from command line
name = sys.argv[1]

# open input file & create output file
i_file = open(name, 'r')
o_file = open('new' + name, 'w+')
if not (i_file.readline()):
    sys.exit()
data = json.load(i_file)
idx = list(data.keys())[0]
id_count = 1
for i in data[idx]:
    o_file.write(f'{{ "index" : {{ "_index": "{idx}", "_id" : "{id_count}" }} }}\n')
    id_count += 1
    o_file.write(json.dumps(i) + '\n')