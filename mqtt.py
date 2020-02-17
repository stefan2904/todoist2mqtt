import logging

import paho.mqtt.client as mqtt


class Mqtt():
    def __init__(self, host, port, username, password, topics=['failcloud/todoist/#'], log=None):
        self.host = host
        self.username = username
        self.topics = topics
        self.client = mqtt.Client(client_id='todoist2mqtt.' + self.username)
        self.client.enable_logger()

        self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)

        self.onMessageCallback = None
        self.connected = False

        self.client.tls_set()
        self.client.username_pw_set(username, password)
        self.client.connect(host, port, 60)

        if log is None:
            self.log = logging
        else:
            self.log = log

        self.log.info("MQTT initialized.")

    def on_connect(self, client, userdata, flags, rc):
        self.log.info("Connected with result code " + str(rc))
        if self.onMessageCallback is not None:
            self.onMessageCallback('MQTT Status', 'Connected to Broker at {} as {}!'.format(self.host, self.username))
        if rc == 5:
            self.log.error("Unauthenticated")
            self.onMessageCallback('MQTT Status', 'Unauthenticated')
            return

        for topic in self.topics:
            client.subscribe(topic)
            self.log.info("Subscribed to {}".format(topic))
        # self.client.subscribe('$SYS/#')
        self.connected = True

    def on_message(self, client, userdata, msg):
        if self.onMessageCallback is not None and not msg.retain:
            self.onMessageCallback(msg.topic, str(msg.payload, 'utf-8'))
        else:
            self.log.info(msg.topic + ": " + str(msg.payload, 'utf-8'))

    def loop_forever(self):
        self.client.loop_forever()

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

    def loop(self):
        self.client.loop()

    def waitForConnection(self):
        while not self.connected:
            self.loop()

    def publish(self, topic, payload, retain=False):
        self.client.publish(topic, payload, qos=0, retain=retain)
        self.log.info('> Published: {}: {}'.format(topic, payload))

    def setCallback(self, cb):
        self.onMessageCallback = cb

    def disconnect(self):
        self.client.disconnect()
