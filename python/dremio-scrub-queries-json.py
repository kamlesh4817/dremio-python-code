import json
import os
import sys

if len(sys.argv) < 3:
    print('This script is used to scrub the queries*.json files in a folder to truncate'
          'the queryText field to a maximum length of 32000 characters, this is the maximum '
          'string field length permitted in Dremio. This is to ensure the resulting queries.json file '
          'can be used as a data source in Dremio and analysis can be made upon it via VDSs. '
          'It require two input parameters, the first is the full path to the Dremio logs directory and the second is '
          'the full path to the directory where we want to place the scrubbed files\n\n'
          'USAGE: python scrub-queries-json.py <full_path_to_dremio_log_dir> <full_path_to_scrubbed_dir>')
    sys.exit(1)

for queriesFile in os.listdir(sys.argv[1]):
    if queriesFile.endswith(".json"):
        queriesFileName = os.path.basename(queriesFile)
        queriesPath = os.path.join(sys.argv[1], queriesFile)
        queriesScrubbedPath = os.path.join(sys.argv[2], 'scrubbed.' + queriesFileName)

        data = [json.loads(line) for line in open(queriesPath, 'r')]
        outfile = open(queriesScrubbedPath, 'a')
        for item in data:
            queryText = item['queryText'];
            if len(queryText) > 32000:
                item['queryText'] = queryText[0:31999]

            outfile.write(json.dumps(item) + '\n')

