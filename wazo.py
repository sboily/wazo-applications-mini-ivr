#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import yaml
import time
from concurrent.futures import ThreadPoolExecutor

from xivo_auth_client import Client as Auth
from xivo_ctid_ng_client import Client as CtidNg
from wazo_websocketd_client import Client as Websocketd


class Wazo:
    def __init__(self, config_file):
        config = self._get_config(config_file)
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
        self._callbacks = {}

        self._threadpool = ThreadPoolExecutor(max_workers=10)

    def on(self, event, callback):
        self._callbacks[event] = callback

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

    def run(self):
        self._connect()

    def _get_config(self, config_file):
        with open(config_file) as config:
            data = yaml.load(config, Loader=yaml.SafeLoader)
        return data if data else {}

    def _connect(self):
        print('Connection...')
        self._get_token()

        self.callcontrol = CtidNg(self.host, token=self.token, prefix='api/ctid-ng', port=self.port, verify_certificate=False)
        self.ws = Websocketd(self.host, token=self.token, verify_certificate=False)
        self._threadpool.submit(self._ws, self._callbacks)

        print('Connected...')

    def _ws(self, events):
        for event in events:
            self.ws.on(event, events[event])
        self.ws.run()

    def _get_token(self):
        auth = Auth(self.host, username=self.username, password=self.password, prefix='api/auth', port=self.port, verify_certificate=False)
        token_data = auth.token.new(self.backend, expiration=self.expiration)
        self.token = token_data['token']
