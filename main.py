#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wazo import Wazo

config = 'config.yml'
events = [
    'application_call_entered',
    'application_call_initiated',
    'application_call_updated',
    'application_call_deleted',
    'application_call_dtmf_received',
    'conference_participant_joined',
    'application_playback_created',
    'stt',
]
playback = {
    'uri': 'sound:tt-weasels',
}

def dtmf(data):
    print("User press: ", data.get('dtmf'))
    if data.get('dtmf') == '1':
        print('Playback file', playback)
        wazo.playback(data['call_id'], playback)
    elif data.get('dtmf') == '2':
        print('Playback file', playback)
        wazo.playback(data['call_id'], playback)

def call_entered(data):
    print("Call entered")
    print(data)
    
def call_deleted(data):
    print("Call deleted")
    print(data)

def conference_joined(data):
    print("Conference joined")
    print(data)

def playback_created(data):
    print('Playback created')
    print(data)

def stt(data):
    print('STT')
    print(data)

wazo = Wazo(config, events)
wazo.on('application_call_dtmf_received', dtmf)
wazo.on('application_call_entered', call_entered)
wazo.on('application_call_deleted', call_deleted)
wazo.on('conference_participant_joined', conference_joined)
wazo.on('application_playback_created', playback_created)
wazo.on('stt', stt)

while True:
    pass
