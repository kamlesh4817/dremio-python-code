########
# Copyright (C) 2019-2021 Dremio Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
########


from Dremio import Dremio
from DremioUtils import DremioUtils
import argparse
import getpass
import json
import logging
import os
import requests
import time
from six.moves.urllib.parse import quote

http_timeout = 90  # 10 second API timeout
utils = DremioUtils()


def read_all_pds(dremio):
    pds_list = []
    cached_schemas = {}
    entity_wanted_keys = ['id', 'type', 'entityType', 'path', 'format', 'accessControlList']
    # Retrieve PDS list from Dremio meta-schema
    sql = "SELECT TABLE_SCHEMA, TABLE_NAME FROM \"INFORMATION_SCHEMA\".\"TABLES\" WHERE TABLE_TYPE = 'TABLE' "
    sql = sql + generate_table_schema_filter()
    jobid = dremio.submit_sql(sql)
    # Wait for the job to complete. Should only take a moment
    while True:
        job_info = dremio.get_job_status(jobid)
        if job_info is None:
            logging.error("read_all_pds: unexpected error. Cannot get a list of PDS.")
            raise RuntimeError("Unexpected error. Cannot get a list of PDS.")
        if job_info["jobState"] in ['CANCELED', 'FAILED']:
            logging.error("read_all_pds: unexpected error, SQL job failed. Cannot get a list of PDS.")
            raise RuntimeError("Unexpected error, SQL job failed. Cannot get a list of PDS.")
        if job_info["jobState"] == 'COMPLETED':
            break
        time.sleep(1)
    # Retrieve list of PDS
    job_result = dremio.get_job_results(jobid)
    num_rows = int(job_result['rowCount'])
    logging.info("***** Number of PDS definitions found for processing: " + str(num_rows))
    if num_rows == 0:
        return pds_list
    # Page through the results, 100 rows per page
    limit = 100
    for i in range(0, int(num_rows / limit) + 1):
        job_result = dremio.get_job_results(jobid, limit * i, limit)
        if job_result and 'rows' in job_result:
            for row in job_result['rows']:
                # The schema (path) is denormalized: instead of abc/ab.c/abc it has abc.ab.c.abc, we need to recover it
                normalized_path = dremio._normalize_schema(row['TABLE_SCHEMA'])
                try:
                    entity = dremio.get_catalog_entity_by_path(normalized_path + row['TABLE_NAME'])
                    if entity is not None:
                        if 'format' in entity and 'type' in entity['format']:
                            if entity['format']['type'] in format_types_list:
                                logging.info("Adding PDS to processing list: {}".format(normalized_path + row['TABLE_NAME']))
                                entity = dict((k, entity[k]) for k in entity_wanted_keys)
                                pds_list.append(entity)
                            else:
                                logging.info("Skipping PDS - type {} not required: {}".format(entity['format']['type'],
                                                                                              normalized_path + row[
                                                                                                  'TABLE_NAME']))
                        else:
                            logging.info(
                                "Skipping PDS - no format details: {}".format(normalized_path + row['TABLE_NAME']))
                except:
                    logging.warning(
                        "Skipping PDS - exception finding entity: {}".format(normalized_path + row['TABLE_NAME']))
        else:
            logging.warning("jobs page for PDSs returned no results: " + (
                json.dumps(job_result) if job_result else "page is empty"))
    return pds_list


def generate_table_schema_filter():
    table_schema_filter = ''
    for filter_item in source_include_filter_list:
        table_schema_filter_value = filter_item.replace('/', '.')
        table_schema_filter = (table_schema_filter + " OR ") if table_schema_filter != '' else (
                    table_schema_filter + " AND ")
        table_schema_filter = table_schema_filter + "TABLE_SCHEMA = '" + table_schema_filter_value + "' OR TABLE_SCHEMA like '" + table_schema_filter_value + ".%'"
    return table_schema_filter


def read_entity_definition(dremio, entity):
    logging.debug("read_entity_definition: processing entity: " + utils.get_entity_desc(entity))
    if 'name' in entity:
        return dremio.get_catalog_entity_by_path(entity['name'])
    elif 'path' in entity:
        return dremio.get_catalog_entity_by_path(utils.normalize_path(entity['path']))
    else:
        logging.error("read_entity_definition: bad data: " + utils.get_entity_desc(entity))
        return None


def promote_pds(dremio, entity):
    # logging.info("promote_pds: processing entity: " + utils.get_entity_desc(entity))
    # Clean up the definition
    if 'id' in entity:
        entity.pop("id")
    if 'tag' in entity:
        entity.pop("tag")
    if 'children' in entity:
        entity.pop("children")
    if 'createdAt' in entity:
        entity.pop("createdAt")
    # Read existing folder or file entity
    fs_entity = read_entity_definition(dremio, entity)
    if fs_entity is None:
        logging.error("promote_pds: Skipping PDS. Cannot find folder or file for PDS Entity: {}".format(
            utils.get_entity_desc(entity)))
        return False
    # Add Folder ID to PDS Entity	
    entity['id'] = fs_entity['id']
    # if 'accessControlList' in entity:
    #    entity.pop('accessControlList')
    logging.info("Promoting PDS: {}".format(utils.get_entity_desc(entity)))
    new_pds_entity = dremio.promote_pds(entity, False)
    if new_pds_entity is None:
        logging.error("promote_pds: Error promoting PDS: {}".format(utils.get_entity_desc(entity)))
        return False
    return True


def main():
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(message)s", level=logging.INFO)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(levelname)s:%(asctime)s:%(message)s"))
        logging.getLogger().addHandler(fh)

    if not tls_verify:
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    dremio = Dremio(dremio_url, user, password, http_timeout, tls_verify)

    logging.info("***** Format types specified: " + format_types_string)

    if dry_run == 1:
        logging.info("***** Dry run flag set to 1. PDS Un-promote and re-promote action will not be performed.")

    if input_file:
        logging.info("***** Input file specified. Getting PDS definitions from input-file.")
        logging.info("Reading PDS definitions from input file: {}".format(input_file))
        f = open(input_file, "r")
        pds_list = json.load(f)['pds']
        f.close()
        logging.info("Number of PDS found for processing: " + str(len(pds_list)))
    else:
        logging.info("***** No input file specified. Getting PDS definitions from information_schema.")
        pds_list = read_all_pds(dremio)

    if output_file:
        # dump all PDSs from file
        logging.info("Writing PDS definitions to output file: {}".format(output_file))
        if os.path.isfile(output_file):
            os.remove(output_file)
        f = open(output_file, "w")
        json.dump({'pds': pds_list}, f)
        f.close()

    if dry_run == 0:
        for pds in pds_list:
            # unpromote the pds
            logging.info("Unpromoting PDS: {}".format(utils.get_entity_desc(pds)))
            if input_file:
                dremio_path = utils.normalize_path(pds['path'])
                dremio_pds = dremio.get_catalog_entity_by_path(dremio_path)
                dremio.delete_catalog_entity(dremio_pds['id'], False)
            else:
                dremio.delete_catalog_entity(pds['id'], False)
            # re-promote the pds
            promote_pds(dremio, pds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to unpromote and re-promote all PDSs of a given format type')
    parser.add_argument('--url', type=str, help='Dremio url, example: https://localhost:9047/', required=True)
    parser.add_argument('--user', type=str, help='Dremio user', required=True)
    parser.add_argument('--password', type=str, help='Dremio user password', required=False)
    parser.add_argument('--tls-verify', action='store_true',
                        help='If provided, flag indicates tls-verification is required')
    parser.add_argument('--source-include-filter', type=str, help='Comma-separated list of sources to process',
                        required=False)
    parser.add_argument('--format-types', type=str, help='Valid format types - Parquet JSON CSV',
                        required=True)
    parser.add_argument('--input-file', type=str,
                        help='File with objects (PDS) that will be re-promoted. information_schema will not be queried.')
    parser.add_argument('--output-file', type=str,
                        help='List of matching objects in information_schema table. Cannot be used with input-file.')
    parser.add_argument('--log-file', type=str, help='Location of log file', required=False,
                        default='./dremio-source-switcher.log')
    parser.add_argument('--dry-run', type=int, help='Dry run flag. Output file will be created.',
                        default=1)

    args = parser.parse_args()
    dremio_url = args.url
    user = args.user
    password = args.password
    if password is None:
        password = getpass.getpass("Enter password:")
    tls_verify = args.tls_verify
    log_file = args.log_file
    source_include_filter_string = args.source_include_filter
    format_types_string = args.format_types
    input_file = args.input_file
    output_file = args.output_file
    dry_run = args.dry_run

    if input_file and output_file:
        raise RuntimeError(
            "Cannot specify both an input and output file parameters together.")

    source_include_filter_list = []
    if source_include_filter_string:
        source_include_filter_list = source_include_filter_string.split(',')

    format_types_list = []
    if format_types_string:
        format_types_list = format_types_string.split(',')

    main()
