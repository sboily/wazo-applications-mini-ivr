#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wazo import Wazo


def dtmf(data):
    dtmf = data.get('dtmf')
    print("User press: ", dtmf)

    playback = {'uri': 'sound:tt-weasels'}
    if dtmf == '1':
        wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call_id'], playback)
    if dtmf == '2':
        wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call_id'], playback)

def call_entered(data):
    print("Call entered")
    playback = {'uri': 'sound:confbridge-join'}
    wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call']['id'], playback)
    
def call_deleted(data):
    print("Call deleted")

def conference_joined(data):
    print("Conference joined")

def playback_created(data):
    print('Playback created')

def stt(data):
    print('People said: ', data['result_stt'])
    if 'raccrocher' in data['result_stt']:
        print('hangup call...')
        playback = {'uri': 'sound:bye'}
        wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call_id'], playback)
        wazo.ctid_ng.applications.hangup_call(wazo.application_uuid, data['call_id'])

wazo = Wazo('config.yml')
wazo.on('application_call_dtmf_received', dtmf)
wazo.on('application_call_entered', call_entered)
wazo.on('application_call_deleted', call_deleted)
wazo.on('conference_participant_joined', conference_joined)
wazo.on('application_playback_created', playback_created)
wazo.on('stt', stt)
wazo.run()
