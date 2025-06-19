import load_handler

user_id = 'place_holder'
consignment_id = 'place_holder'
source_bucket = 'place_holder'
object_key_prefix = f'{user_id}/sharepoint/{consignment_id}'
client_id = 'place_holder'
client_secret = 'place_holder'
backend_checks_sfn_arn = 'place_holder'
event = {
    'metadataSourceBucket': source_bucket,
    'objectKeyPrefix': object_key_prefix,
    'consignmentId': consignment_id,
    'clientId': client_id,
    'clientSecret': client_secret,
    'backendChecksSfnArn': backend_checks_sfn_arn
}
load_handler.load(event, None)
