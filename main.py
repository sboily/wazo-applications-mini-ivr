#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wazo import Wazo


players = {}


def dtmf(data):
    dtmf = data.get('dtmf')
    print("User press: ", dtmf)

    if dtmf == '1':
        playback = {'uri': 'sound:tt-weasels'}
        wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call_id'], playback)
    if dtmf == '2':
        playback = {'uri': 'sound:hello-world'}
        wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call_id'], playback)
    if dtmf == '*':
        print('Activating STT')
        wazo.third_party.start(data['call_id'])

def call_entered(data):
    print("Call entered", data["call"]["id"])
    playback = {'uri': 'sound:confbridge-join'}
    wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call']['id'], playback)
    
def call_deleted(data):
    print("Call deleted")

def conference_joined(data):
    print("Conference joined")

def playback_created(data):
    print('Playback created')

def stt(data):
    global players

    call_id = data['call_id']
    game_activated = players.get(call_id)

    print('People said:', data['result_stt'])
    print('Game is activated for this player:', 'No' if not game_activated else 'Yes')

    if 'hangup' in data['result_stt']:
        print('hangup call...')
        hangup_call(data)
    if not game_activated and 'play' in data['result_stt']:
        print('Playing to yes no games...')
        players[call_id] = True
        playback = {'uri': 'sound:hello-world'}
        wazo.ctid_ng.applications.send_playback(wazo.application_uuid, data['call_id'], playback)
    if game_activated and ('yes' in data['result_stt'] or 'no' in data['result_stt']):
        players.pop(call_id)
        print('Sorry you loose...')
        hangup_call(data)

def hangup_call(data):
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
