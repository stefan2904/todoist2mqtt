import base64
import hashlib
import hmac
import json
import logging
import os

import todoist
from flask import Flask, jsonify, request

from mqtt import Mqtt

TODOIST_CLIENT_SECRET = os.environ.get('TODOIST_CLIENT_SECRET')
TODOIST_TOKEN = os.environ.get('TODOIST_TOKEN')
BROKERHOST = os.getenv('MQTTHOST')
BROKERPORT = int(os.getenv('MQTTPORT'))
USERNAME = os.getenv('MQTTUSERNAME')
PASSWORD = os.getenv('MQTTPASSWORD')
MQTTTOPIC = os.getenv('MQTTTOPIC')

app = Flask(__name__)
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.info('loglevel is ' + str(app.logger.level))
    app.logger.info('set loglevel to ' + str(gunicorn_logger.level))
    # app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    app.logger.info('set loglevel to ' + str(logging.DEBUG))
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('loglevel is ' + str(app.logger.level))
else:
    app.logger.info('loglevel is ' + app.logger.info.level)

todoist_api = todoist.TodoistAPI(TODOIST_TOKEN)

mqtt = Mqtt(BROKERHOST, BROKERPORT, USERNAME, PASSWORD, topics=[], log=app.logger)
mqtt.waitForConnection()


def verify_headers(headers):
    return headers.get('USER-AGENT') == 'Todoist-Webhooks'


def verify_hmac(req):
    request_hmac = req.headers.get('X-Todoist-Hmac-Sha256')
    key = bytes(TODOIST_CLIENT_SECRET, 'latin-1')
    calculated_hmac = hmac.new(key, msg=req.get_data(),
                               digestmod=hashlib.sha256).digest()
    calculated_hmac = base64.b64encode(calculated_hmac)
    calculated_hmac = calculated_hmac.decode('ascii')
    app.logger.info('Comparing ' + calculated_hmac + ' with ' + request_hmac)
    return request_hmac == calculated_hmac


def process_event(event_type, event):
    # event_type = event_type.replace(':', '_')
    topic = '{}/{}'.format(MQTTTOPIC, event_type)
    item = todoist_api.items.get(event['id'])
    item = json.dumps(item)
    app.logger.info('Reporting {} event ...'.format(event_type))
    mqtt.publish(topic, item)


@app.route('/todoist_hook', methods=['POST'])
def todoist():
    event_id = request.headers.get('X-Todoist-Delivery-ID')

    if not verify_headers(request.headers):
        app.logger.warning('invalid headers:' + request.headers)
        return jsonify({'status': 'rejected'}), 400

    if not request.json:
        app.logger.warning('Request contains no valid JSON')
        return jsonify({'status': 'rejected', 'reason': 'malformed request'}), 400

    if not verify_hmac(request):
        app.logger.info('HMAC is invalid')
        return jsonify({'status': 'rejected', 'reason': 'invalid request'}), 400

    process_event(request.json['event_name'], request.json['event_data'])

    return jsonify({'status': 'accepted', 'request_id': event_id}), 200


@app.route('/test')
def test():
    app.logger.info('OK, lets test it ...')
    process_event('test event', {'id': '3697787544'})
    return jsonify({'status': 'test request send to mqtt',
                    'health': 'ok'}), 200


@app.route('/')
def index():
    app.logger.info('Yes, I am alive!')
    return jsonify({'status': 'accepted',
                    'health': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=True)
