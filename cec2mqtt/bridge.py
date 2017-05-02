from __future__ import print_function

import json
import logging
import signal
import time

import click
import paho.mqtt.client as mqtt

from cec2mqtt.version import __version__
from cec2mqtt.cec_client import CECClient
from cec2mqtt.config import load_config

FORMAT = '%(asctime)s: %(levelname)-8s %(name)-15s: %(message)s'
logger = logging.getLogger(__name__)


RUN = True


def mqtt_on_connect(client, userdata, flags, rc):
    logger.info("Conntect to mqtt broker")
    client.subscribe('{}/#'.format(client.bridge.config.mqtt.topic_subscribe_prefix))


def mqtt_on_message(client, userdata, message):
    bridge = client.bridge
    config = bridge.config
    cec = bridge.cec

    cmd = message.topic.replace(config.mqtt.topic_subscribe_prefix, '').strip('/')

    target = None
    if '/' in cmd:
        cmd, _, target = cmd.partition('/')
        target = int(target)
    payload = message.payload

    logger.debug('got cmd: %s target: %s payload: %s', cmd, target, payload)

    if cmd == 'power':
        if payload == 'on':
            cec.on(int(target))
        elif payload == 'standby':
            cec.standby(target)
    elif cmd == 'volume':
        if payload == 'up':
            cec.volume_up()
        elif payload == 'down':
            cec.volume_down()
    elif cmd == 'active':
        cec.active_source(target)


class Bridge(object):

    def __init__(self, config):

        self.config = config
        self.cec = CECClient(
            osd_name=config.name,
            port=config.cec.port,
            connect=False
        )
        self.mqtt = mqtt.Client(config.name)
        self.mqtt.on_connect = mqtt_on_connect
        self.mqtt.on_message = mqtt_on_message

        if self.config.mqtt.username:
            self.mqtt.username_pw_set(self.config.mqtt.username, self.config.mqtt.username)

        self.mqtt.bridge = self
        self.cec.bridge = self

    def connect(self):
        self.cec.connect()
        self.mqtt.connect(self.config.mqtt.host, self.config.mqtt.port, 60)
        self.mqtt.loop_start()

    def loop(self):
        logger.info("Running")
        while RUN:
            for device_id in self.config.cec.devices:
                device = self.cec.devices[device_id]
                power = self.cec.power_status(device_id)
                self.send_status('power/{}'.format(device_id), power)
                logger.debug("device(%s) '%s' is %s", device_id, device['osd_name'], power)

            logger.debug('sleeping...')
            time.sleep(10)
        logger.info("Exiting")

    def end(self):
        logger.info("disconnecting mqtt")
        self.mqtt.disconnect()

    def send_status(self, sufix, payload):
        self.mqtt.publish(
            '{}/{}'.format(self.config.mqtt.topic_publish_prefix, sufix),
            payload=str(payload),
        )


def stop(signum, frame):
    global RUN
    logger.info("shutting down ...")
    RUN = False


@click.group()
@click.version_option(__version__)
@click.option('--debug/--no-debug', default=False)
@click.option(
    '--config', '-c', default='/etc/cec2mqtt/config.yaml', help='Config file path', type=click.Path())
@click.pass_context
def cli(ctx, debug, config):
    logging.basicConfig(format=FORMAT, level=logging.DEBUG if debug else logging.INFO)
    signal.signal(signal.SIGINT, stop)
    configuration = load_config(config)
    logger.debug("final config: %s", configuration)
    ctx.obj['bridge'] = Bridge(configuration)


@cli.command()
@click.pass_context
def run(ctx):
    bridge = ctx.obj['bridge']
    bridge.connect()
    try:
        bridge.loop()
    finally:
        bridge.end()

@cli.command()
@click.pass_context
def cecdevices(ctx):
    bridge = ctx.obj['bridge']
    bridge.cec.connect()
    final_ids = []
    for index, device in bridge.cec.devices.items():
        if index == bridge.cec.logical_address:
            continue
        print("Found device with id={} and name={} power=".format(index, device['osd_name'], device['power_status']))
        final_ids.append(index)
    print("Use the following list in your config: [{}]".format(",".join(final_ids)))


@cli.command()
@click.pass_context
def homekit2mqtt(ctx):
    bridge = ctx.obj['bridge']
    bridge.cec.connect()
    homekit2mqtt_config = {}
    for index, device in bridge.cec.devices.items():
        if index == bridge.cec.logical_address:
            continue
        switch = {
            "service": "Switch",
            "name": device['osd_name'],
            "topic": {
              "statusOn": "{}/power/{}".format(bridge.config.mqtt.topic_publish_prefix, index),
              "setOn": "{}/power/{}".format(bridge.config.mqtt.topic_subscribe_prefix, index),
            },
            "payload": {
              "onTrue": 'on',
              "onFalse": 'standby'
            },
            "manufacturer": "vendor {}".format(device['vendor_id']),
            "model": "Switch",
        }
        homekit2mqtt_config['cec_device_{}'.format(index)] = switch
    print(json.dumps(homekit2mqtt_config, indent=4))


def main():
    cli(obj={})