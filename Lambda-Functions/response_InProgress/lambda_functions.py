import json
import boto3


def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    user_id = '2345'
    event_dic = json.loads(event['body'])
    response = client.post_text(
        botName='Concierge_chatbot',
        botAlias='Concierge_chatbot',
        userId=user_id,
        inputText=event_dic["messages"][0]['unstructured']['text'],
    )

    message_string = {
        "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": "string",
                    "text": response["message"],
                    "timestamp": "string"
                }
            }
        ]
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps(message_string)
    }

