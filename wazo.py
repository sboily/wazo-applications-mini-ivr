#!/usr/bin/python
# -*- coding: utf-8 -*-

import websocket
import json
import logging
import urllib3

from Queue import Queue
from threading import Thread

from xivo_auth_client import Client as Auth
from xivo_ctid_ng_client import Client as CtidNg
from xivo_confd_client import Client as Confd

urllib3.disable_warnings()
logging.basicConfig()
logging.captureWarnings(True)


message_queue = Queue()


class callbacksHandler:
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
    def __init__(self, config, events):
        self.host = config['wazo']['host']
        self.username = config['wazo']['username']
        self.password = config['wazo']['password']
        self.port = config['wazo']['port']
        self.backend = config['wazo']['backend']
        self.application_uuid = config['wazo']['application_uuid']
        self.expiration = 3600
        self.token = None
        self.user_uuid = None
        self.call_control = None
        self.confd = None
        self.events = events
        self.callbacksHandler = callbacksHandler()

    def connect(self):
        self._get_token()
        self.callcontrol = CtidNg(self.host, token=self.token, prefix='api/ctid-ng', port=self.port, verify_certificate=False)
        self.confd = Confd(self.host, token=self.token, prefix='api/confd', port=self.port, verify_certificate=False)
        self._message_worker()
        self._websocket_worker()

    def on(self, event, callback):
        self.callbacksHandler.on(event, callback)

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

    def _message_worker(self):
        t = Thread(target=self.callbacksHandler.run)
        t.daemon = True
        t.start()

    def _websocket_worker(self):
        t = websocket_worker(self.host, self.token, self.events)
        t.daemon = True
        t.start()

    def _get_token(self):
        auth = Auth(self.host, username=self.username, password=self.password, prefix='api/auth', port=self.port, verify_certificate=False)
        token_data = auth.token.new(self.backend, expiration=self.expiration)
        self.token = token_data['token']
        self.user_uuid = token_data['xivo_user_uuid']


class websocket_worker(Thread):
    def __init__(self, host, token, events):
        Thread.__init__(self)
        self.host = host
        self.token = token
        self.events = events
        self.started = False
        self.ws = None

    def subscribe(self, event_name):
        self.ws.send(json.dumps({
            'op': 'subscribe',
            'data': {
                'event_name': event_name
            }
        }))

    def _start(self):
        msg = {'op': 'start'}
        self.ws.send(json.dumps(msg))

    def init(self, msg):
        if msg.get('op') == 'init':
            for event in self.events:
                self.subscribe(event)
            self._start()

        if msg.get('op') == 'start':
            self.started = True

    def on_message(self, message):
        msg = json.loads(message)

        if not self.started:
            self.init(msg)
        else:
            message_queue.put(msg)

    def on_error(self, error):
        print "### error {} ###".format(error)

    def on_close(self):
        print "### closed ###"

    def on_open(self):
        print "### open ###"

    def run(self):
        websocket.enableTrace(False)
        try:
            self.ws = websocket.WebSocketApp("wss://{}/api/websocketd/".format(self.host),
                                        header=["X-Auth-Token: {}".format(self.token)],
                                        on_message = self.on_message,
                                        on_open = self.on_open,
                                        on_error = self.on_error,
                                        on_close = self.on_close)
            self.ws.on_open = self.on_open
            self.ws.run_forever(sslopt={"cert_reqs": False})
        except Exception as e:
            print 'connection error to wazo', e
