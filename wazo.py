#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import yaml
import requests
from concurrent.futures import ThreadPoolExecutor

from xivo_auth_client import Client as Auth
from xivo_ctid_ng_client import Client as CtidNg
from wazo_websocketd_client import Client as Websocketd


class Wazo:
    def __init__(self, config_file):
        self.config = self._get_config(config_file)
        self.host = self.config['wazo']['host']
        self.username = self.config['wazo']['username']
        self.password = self.config['wazo']['password']
        self.port = self.config['wazo']['port']
        self.backend = self.config['wazo']['backend']
        self.application_uuid = self.config['wazo']['application_uuid']
        self.expiration = 3600
        self.ctid_ng = None
        self.third_party = None
        self.auth = None
        self.ws = None

        self._callbacks = {}
        self._threadpool = ThreadPoolExecutor(max_workers=1)

    def on(self, event, callback):
        self._callbacks[event] = callback

    def run(self):
        self._connect()

    def _get_config(self, config_file):
        with open(config_file) as config:
            data = yaml.load(config, Loader=yaml.SafeLoader)
        return data if data else {}

    def _connect(self):
        print('Connection...')
        token_data = self._get_token()
        token = token_data['token']

        self.ctid_ng = CtidNg(self.host, token=token, prefix='api/ctid-ng', port=self.port, verify_certificate=False)
        self.third_party = ThirdParty(self.host, token=token)
        self.ws = Websocketd(self.host, token=token, verify_certificate=False)
        self._threadpool.submit(self._ws, self._callbacks)

        print('Connected...')

    def _ws(self, events):
        for event in events:
            self.ws.on(event, events[event])
        self.ws.run()

    def _get_token(self):
        self.auth = Auth(self.host, username=self.username, password=self.password, prefix='api/auth', port=self.port, verify_certificate=False)
        return self.auth.token.new(self.backend, expiration=self.expiration)


class ThirdParty:
    def __init__(self, url, token):
        self.url = 'https://{}/api/calld/1.0/stt'.format(url)
        self.token = token

    def start(self, call_id):
        headers = {'X-Auth-Token': self.token}
        data = {'call_id': call_id}
        requests.post(self.url, json=data, headers=headers)
