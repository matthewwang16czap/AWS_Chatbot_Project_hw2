import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_dinning_suggestion(Location, Cuisine, DiningTime, NumberOfPeople, PhoneNumber, Email):
    if DiningTime is not None:
        if not isvalid_date(DiningTime):
            return build_validation_result(False, 'DiningTime',
                                           'I did not understand that, what date would you like to dine in?')
        elif datetime.datetime.strptime(DiningTime, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'DiningTime',
                                           'You can have a suggestion at least in today. What date would you like to dine in?')
    if NumberOfPeople is not None:
        if not NumberOfPeople.isnumeric():
            return build_validation_result(False, 'NumberOfPeople',
                                           'You can only have an integer number of people to attend. How many people will attend?')
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def dinning_suggestion(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    source = intent_request['invocationSource']

    Location = get_slots(intent_request)["Location"]
    Cuisine = get_slots(intent_request)["Cuisine"]
    DiningTime = get_slots(intent_request)["DiningTime"]
    NumberOfPeople = get_slots(intent_request)["NumberOfPeople"]
    PhoneNumber = get_slots(intent_request)["PhoneNumber"]
    Email = get_slots(intent_request)["Email"]

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dinning_suggestion(Location, Cuisine, DiningTime, NumberOfPeople, PhoneNumber,
                                                        Email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request[
                                                                               'sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.

    # send infomation to sqs
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/303721311054/Concierge_queue'
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'Location': {
                'DataType': 'String',
                'StringValue': Location
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': Cuisine
            },
            'DiningTime': {
                'DataType': 'String',
                'StringValue': DiningTime
            },
            'NumberOfPeople': {
                'DataType': 'Number',
                'StringValue': NumberOfPeople
            },
            'PhoneNumber': {
                'DataType': 'Number',
                'StringValue': PhoneNumber
            },
            'Email': {
                'DataType': 'String',
                'StringValue': Email
            }
        },
        MessageBody=(
            'a query for dining suggestion'
        )
    )

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'your suggestion for {}, {} has been processed. you will be notified from your email once the list of restaurant suggestions are ready.'.format(
                      Location, Cuisine)})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dinning_suggestion(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
