import boto3
from load_utils import convert_to_file_input, consignment_status_input, read_metadata, api_request, \
    add_files_mutation, update_consignment_status_mutation, trigger_backend_checks


s3_client = boto3.client('s3')
sf_client = boto3.client('stepfunctions')


def load(event, context):
    source_bucket = event['metadataSourceBucket']
    object_prefix = event['objectKeyPrefix']
    consignment_id = event['consignmentId']
    client_id = event['clientId']
    client_secret = event['clientSecret']
    backend_checks_sfn_arn = event['backendChecksSfnArn']
    user_id = object_prefix.split("/")[0]
    metadata_key_prefix = f'{object_prefix}/metadata'
    records_key_prefix = f'{object_prefix}/records'

    # get list of all metadata sidecar bucket keys for consignment
    try:
        list_object_paginator = s3_client.get_paginator('list_objects_v2')
        operation_parameters = {'Bucket': source_bucket,
                                'Prefix': metadata_key_prefix}
        page_iterator = list_object_paginator.paginate(**operation_parameters)
        object_keys = []
        for page in page_iterator:
            for obj in page['Contents']:
                size = obj['Size']
                if size > 0:
                    key = obj['Key']
                    object_keys.append(key)
    except Exception as e:
        print(f"Error: {e}")
        raise e

    file_entries = []
    # iterate of metadata sidecar object keys
    # read object json and convert to graphql mutations
    for object_key in object_keys:
        md = read_metadata(s3_client, source_bucket, object_key)
        original_match_id = md['matchId']
        converted = convert_to_file_input(md, original_match_id)
        file_entries.append(converted)

    md_input = {
        'consignmentId': consignment_id,
        'metadataInput': file_entries,
        'userIdOverride': user_id,
        'emptyDirectories': []
    }

    add_files_mutation_variables = { 'input': md_input }
    # send consignment api request to add file entries to DB
    result = api_request(add_files_mutation, add_files_mutation_variables, client_id, client_secret)
    data = result.json()['data']['addFilesAndMetadata']
    consignment_upload_status = 'Completed'
    if 'errors' in data:
        consignment_upload_status = 'CompletedWithIssues'
    upload_status_input = consignment_status_input(consignment_id, 'Upload', consignment_upload_status, user_id)
    update_status_variables = {'addConsignmentStatusInput' : upload_status_input}
    # send consignment api request to update consignment status in DB
    api_request(update_consignment_status_mutation, update_status_variables, client_id, client_secret)
    # trigger backend checks
    trigger_backend_checks(sf_client, consignment_id, records_key_prefix, backend_checks_sfn_arn)
