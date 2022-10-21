import json
import boto3
import requests
from requests.auth import HTTPBasicAuth
from boto3.dynamodb.conditions import Key, Attr


def es_search(event):
    host = 'https://search-concierge-chatbot-es-c6lzeo2nxgfqfl4q3rkpbotmva.us-east-1.es.amazonaws.com'
    index = 'restaurants'
    url = host + '/' + index + '/_search'
    '''
    query = {
        "size": 5,
        "query": {
            "multi_match": {
                "query": "french",
                "fields": ["categories.alias", "cuisine"]
            }
        }
    }
    '''
    # Elasticsearch 6.x requires an explicit Content-Type header
    headers = {"Content-Type": "application/json"}
    # r = requests.get(host, auth = HTTPBasicAuth('user', 'password'))
    r = requests.get(url, auth=HTTPBasicAuth('user', 'password'), headers=headers, data=json.dumps(event))
    result = json.loads(r.content)
    result_restaurants = result['hits']['hits']
    response = {
        "statusCode": 200,
        "data": []
    }
    for restaurant in result_restaurants:
        nes_info = {
            "id": restaurant["_source"]["id"],
            "cuisine": restaurant["_source"]["cuisine"]
        }
        response["data"].append(nes_info)
    return response


def lambda_handler(event, context):
    # access sqs
    sqs_client = boto3.client('sqs')
    try:
        # polls a message from the SQS queue
        response = sqs_client.receive_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/303721311054/Concierge_queue',
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=1
        )

        sqs_client.delete_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/303721311054/Concierge_queue',
            ReceiptHandle=response['Messages'][0]['ReceiptHandle']
        )
    except KeyError:
        return {
            'statusCode': 404,
            'body': "Empty SQS Queue."
        }

    # data needed
    restaurant_requirements = response['Messages'][0]['MessageAttributes']
    cuisine_type = restaurant_requirements['Cuisine']['StringValue'].lower()
    people_number = restaurant_requirements["NumberOfPeople"]["StringValue"]
    time = restaurant_requirements["DiningTime"]["StringValue"]
    email_id = restaurant_requirements["Email"]["StringValue"]

    # search in es
    query = {
        "size": 3,
        "query": {
            "multi_match": {
                "query": cuisine_type,
                "fields": ["categories.alias", "cuisine"]
            }
        }
    }
    query_result = es_search(query)

    # search in dynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    restaurant_data = []
    for restaurant in query_result['data']:
        res_id = restaurant['id']
        res_details = table.scan(
            FilterExpression=Attr('id').eq(str(res_id))
        )
        restaurant_data.append(res_details['Items'][0])

    email = "Hello! Here are my " + cuisine_type + " restaurant suggestions for "
    email += people_number + " people for today at " + time + ":\n"

    for r in restaurant_data:
        name = r['name']
        address = r['location']['display_address'][0]
        rating = r['rating']
        review_count = r['review_count']
        email += name + ",\n rating: " + str(rating) + ", review count: " + str(
            review_count) + ",\n located at " + address + "\n"
        email += '\n'
    email += "Enjoy your meal!"

    sns_client = boto3.client('ses')

    response = sns_client.send_email(
        Destination={
            'ToAddresses': [
                email_id,
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": 'UTF-8',
                    "Data": email
                }
            },
            "Subject": {
                "Charset": 'UTF-8',
                "Data": "Dining Suggestion from group Sihan Wang and Nishi Taneja",
            },
        },
        Source=email_id,
    )

    print(response)

    return {
        'statusCode': 200,
        'body': email
    }