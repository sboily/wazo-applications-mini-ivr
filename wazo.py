#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import yaml
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from xivo_auth_client import Client as Auth
from xivo_ctid_ng_client import Client as CtidNg
from wazo_websocketd_client import Client as Websocketd


message_queue = Queue()


class Message:
    def __init__(self, name):
        self.name = name

    def message(self, data):
        message_queue.put({'name': self.name, 'data': data})


class CallbacksHandler:
    def __init__(self):
        self.callbacks = dict()

    def on(self, event, callback):
        self.callbacks[event] = callback

    def triggerCallback(self, event, data):
        if self.callbacks.get(event):
            self.callbacks[event](data)

    def on_message(self, msg):
        self.triggerCallback(msg['name'], msg['data'])

    def run(self):
        while True:
            self.on_message(message_queue.get())


class Wazo:
    def __init__(self, config_file, events):
        config = self._get_config(config_file)
        self.events = events
        self.host = config['wazo']['host']
        self.username = config['wazo']['username']
        self.password = config['wazo']['password']
        self.port = config['wazo']['port']
        self.backend = config['wazo']['backend']
        self.application_uuid = config['wazo']['application_uuid']
        self.expiration = 3600
        self.token = None
        self.call_control = None
        self.ws = None

        self._callbacksHandler = CallbacksHandler()
        self._threadpool = ThreadPoolExecutor(max_workers=10)
        self._connect()

    def on(self, event, callback):
        self._callbacksHandler.on(event, callback)

    def hangup(self, call_id):
        self.callcontrol.applications.hangup_call(self.application_uuid, call_id)

    def playback(self, call_id, playback):
        return self.callcontrol.applications.send_playback(self.application_uuid, call_id, playback)

    def list_calls(self):
        return self.callcontrol.applications.list_calls(self.application_uuid)

    def make_call(self, call_id, exten, context):
        calls = {'calls': [{'id': call_id}]}
        node = self.callcontrol.applications.create_node(self.application_uuid, calls)
        call = {
            'autoanswer': False,
            'context': context,
            'exten': exten
        }
        return self.callcontrol.applications.make_call_to_node(self.application_uuid, node['uuid'], call)

    def _get_config(self, config_file):
        with open(config_file) as config:
            data = yaml.load(config, Loader=yaml.SafeLoader)
        return data if data else {}

    def _connect(self):
        print('Connection...')
        self._get_token()
        self.callcontrol = CtidNg(self.host, token=self.token, prefix='api/ctid-ng', port=self.port, verify_certificate=False)
        self.ws = Websocketd(self.host, token=self.token, verify_certificate=False)

        self._threadpool.submit(self._callbacksHandler.run)
        self._threadpool.submit(self._ws, self.events)

        print('Connected...')

    def _ws(self, events):
        for event in events:
            m = Message(event)
            self.ws.on(event, m.message)
        self.ws.run()

    def _get_token(self):
        auth = Auth(self.host, username=self.username, password=self.password, prefix='api/auth', port=self.port, verify_certificate=False)
        token_data = auth.token.new(self.backend, expiration=self.expiration)
        self.token = token_data['token']
