"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
from botocore.vendored import requests
import time


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': '<speak>' + output + '</speak>'
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title         = "Welcome"
    speech_output      = "Welcome to the Luxembourg Airport Skill by David Gwynne"
    reprompt_text      = None
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Luxembourg Airport skill. "
    
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def spellOut(input):
    return '<say-as interpret-as="spell-out">' + input + '</say-as>'

def pause(seconds):
    return '<break time="' + str(seconds) + 's"/>'


def alexaifyEpoch(epoch):
    return time.strftime('%H:%M', time.localtime(epoch))


def alexaifyFlight(flight, isDeparture):
    text = flight['airline'] + ' flight ' + spellOut(flight['flight']) + \
           (' to ' if isDeparture else ' from ') + flight['destination'] + \
           ', scheduled to ' + ('take off' if isDeparture else 'land') + \
           ' at ' + alexaifyEpoch(flight['scheduled'])

    if flight['status'] == 'Cancelled':
        text = text + ' has been cancelled'
    elif (flight['status'] == 'Delayed'):
        text = text + ' is delayed'

        if flight['real'] != 'null':
            text = text + ' until ' + alexaifyEpoch(flight['real'])
    else:
        text = text + ' is on time'

    text = text + '.'

    return text


def getDepartures(intent, session):
    session_attributes = {}
    reprompt_text      = None
    speech_output      = ''
    should_end_session = True

    request = requests.get('https://api.tfl.lu/v1/Airport/Departures')
    data    = request.json()

    cityOutput = ''
    if 'slots' in intent and 'city' in intent['slots']:
        cityOutput = 'to ' + intent['slots']['city']['value']
        data = [x for x in data if intent['slots']['city']['value'].lower() in x['destination'].lower()]

    if len(data) == 0:
        speech_output = 'There are no upcoming departures ' + cityOutput
    elif len(data) == 1:
        speech_output = 'The only upcoming departure ' + cityOutput + ' is ' + pause(1)
    else:
        speech_output = 'The next ' + str(min(len(data), 5)) + ' scheduled departures ' + cityOutput + ' are ' + pause(1)

    for flight in data[:5]:
        speech_output = speech_output + alexaifyFlight(flight, True) + pause(1)
    
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))
        

def getArrivals(intent, session):
    session_attributes = {}
    reprompt_text      = None
    speech_output      = ''
    should_end_session = True

    request = requests.get('https://api.tfl.lu/v1/Airport/Arrivals')
    data    = request.json()

    cityOutput = ''
    if 'slots' in intent and 'city' in intent['slots']:
        cityOutput = 'from ' + intent['slots']['city']['value']
        data = [x for x in data if intent['slots']['city']['value'].lower() in x['destination'].lower()]

    if len(data) == 0:
        speech_output = 'There are no upcoming arrivals ' + cityOutput
    elif len(data) == 1:
        speech_output = 'The only upcoming arrival ' + cityOutput + ' is ' + pause(1)
    else:
        speech_output = 'The next ' + str(min(len(data), 5)) + ' scheduled arrivals ' + cityOutput + ' are ' + pause(1)

    for flight in data[:5]:
        speech_output = speech_output + alexaifyFlight(flight, False) + pause(1)
    
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetDepartures" or intent_name == "GetDeparturesToCity":
        return getDepartures(intent, session)
    elif intent_name == "GetArrivals" or intent_name == "GetArrivalsFromCity":
        return getArrivals(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] != "amzn1.ask.skill.6b1940e0-a71e-4961-80a1-18884696fd5d"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


if __name__ == "__main__":
    # execute only if run as a script
    intent = {'name' : 'GetDepartures'}
    #intent = {'name' : 'GetDeparturesToCity', 'slots' : {'city' : {'value' : 'London'}}}
    #intent = {'name' : 'GetArrivals', 'slots' : {}}
    session = {}

    print(getDepartures(intent, session))
