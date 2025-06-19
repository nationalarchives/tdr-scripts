import json
import uuid

import requests
from datetime import datetime


add_files_mutation = """
        mutation addFilesAndMetadata($input: AddFileAndMetadataInput!) {
            addFilesAndMetadata(addFilesAndMetadataInput: $input) {
                fileId
                matchId
            }
        }
    """


update_consignment_status_mutation = """
        mutation updateConsignmentStatus($updateConsignmentStatusInput: ConsignmentStatusInput!) {
            updateConsignmentStatus(updateConsignmentStatusInput: $updateConsignmentStatusInput)
        }
    """


def validate_utf8(raw_metadata, bucket, key):
    try:
        raw_metadata.decode('utf-8')
    except UnicodeDecodeError as e:
        #save error file in S3
        raise RuntimeError(f'Non-UTF8 encoded metadata in {bucket} - {key}: { e.reason }')


def read_metadata(s3_client, metadata_source_bucket, metadata_key):
    s3_response_object = s3_client.get_object(Bucket=metadata_source_bucket, Key=metadata_key)
    object_content = s3_response_object['Body'].read()
    validate_utf8(raw_metadata=object_content, bucket=metadata_source_bucket, key=metadata_key)
    return json.loads(object_content.decode("utf-8"))


def get_token(client_id, client_secret):
    client_id = client_id
    auth_url = f'https://auth.tdr-staging.nationalarchives.gov.uk/realms/tdr/protocol/openid-connect/token'
    grant_type = {"grant_type": "client_credentials"}
    auth_response = requests.post(auth_url, data=grant_type, auth=(client_id, client_secret))
    if auth_response.status_code != 200:
        raise RuntimeError(f"Non 200 status from Keycloak {auth_response.status_code}")
    return auth_response.json()['access_token']


def api_request(query, variables, client_id, client_secret):
    headers = {'Authorization': f'Bearer {get_token(client_id, client_secret)}'}
    result = requests.post('https://api.tdr-staging.nationalarchives.gov.uk/graphql', json={'query': query, 'variables': variables}, headers=headers)
    return result


def convert_to_file_input(raw_metadata, match_id):
    date_format = '%Y-%m-%dT%H:%M:%S%z'
    date_obj = datetime.strptime(raw_metadata['Modified'], date_format)
    last_modified = int(round(datetime.timestamp(date_obj))) * 1000
    file_size = int(raw_metadata['Length'])
    return {
        'originalPath': raw_metadata['FileRef'],
        'checksum': raw_metadata['sha256ClientSideChecksum'],
        'lastModified': last_modified,
        'fileSize': file_size,
        'matchId': match_id
    }


def consignment_status_input(consignment_id, status_type, status_value, override_user_id):
    return {
        'consignmentId': consignment_id,
        'statusType': status_type,
        'statusValue': status_value,
        'userIdOverride': override_user_id
    }


def trigger_backend_checks(client, consignment_id, s3_source_bucket_prefix, state_machine_arn):
    name = f'transfer_service_{uuid.uuid4()}'
    execution_input = json.dumps({"consignmentId" : consignment_id, "s3SourceBucketPrefix" : s3_source_bucket_prefix})
    response = client.start_execution(
        stateMachineArn=state_machine_arn,
        name=name,
        input=execution_input
    )
    return response
