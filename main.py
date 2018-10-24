#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import yaml

from wazo import Wazo


def get_config():
    with open('config.yml') as config_file:
        data = yaml.load(config_file)
    return data if data else {}

config = get_config()

events = [
    'application_call_entered',
    'application_call_initiated',
    'application_call_updated',
    'application_call_deleted',
    'application_call_dtmf_received'
]

playback = {
    'uri': 'sound:tt-weasels',
}

wazo = Wazo(config, events)
wazo.connect()


def dtmf(data):
    if data.get('dtmf') == '1':
        wazo.playback(data['call_id'], playback)

def call_entered(data):
    print "Call entered"
    print data
    
def call_deleted(data):
    print "Call deleted"
    print data


wazo.on('application_call_dtmf_received', dtmf)
wazo.on('application_call_entered', call_entered)
wazo.on('application_call_deleted', call_deleted)

while True:
    time.sleep(0.2)
