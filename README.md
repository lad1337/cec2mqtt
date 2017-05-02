cec2mqtt
========

A HDMI-CEC to MQTT bridge for connecting your AV-devices to your Home Automation system. You can control and monitor power status and volume.

# Features
* Power feedback (given every ~10sec)
* Power control
* Volume control


# Dependencies

## MQTT
* MQTT broker (like [Mosquitto](https://mosquitto.org/))

## HDMI-CEC
* libcec3 with python bindings (https://drgeoffathome.wordpress.com/2015/08/09/a-premade-libcec-deb/ for a compiled RPI version)
  * You might need to compile the bindings yourself. See [this home-assistant issue](https://github.com/home-assistant/home-assistant/issues/2306) for more information.
* HDMI-CEC interface device (like a [Pulse-Eight](https://www.pulse-eight.com/) device, or a Raspberry Pi)

# Instalation

`pip install cec2mqtt`

# Usage
## Run
`$ cec2mqtt run`
> Runs the bridge in forground with info logging.

`$ cec2mqtt run --config /etc/cec2mqtt/config.yaml`
> Runs the bridge in forground using the config at `/etc/cec2mqtt/config.yaml` (default)

See more with `cec2mqtt --help`

## Generate config for homekit2mqtt

You can generate a config section for [homekit2mqtt](https://github.com/hobbyquaker/homekit2mqtt) with:
`$ cec2mqtt homekit2mqtt`
This prints a switch-service config for all currently connected cec devices.

## Check CEC devices

`$ cec2mqtt cecdevices` will print some cec device information.

# MQTT Topics

## Subscribtion

The bridge subscribes to `cec/set/#` (by default)
> This can be set in the config on the key `mqtt.topic_subscribe_prefix`. It will define everything before the wildcard `/#`. E.g. `topic_subscribe_prefix = foo/bar` will subscribe to `foo/bar/#`

Following topics are understood:

| topic (behind the prefix) | body              | remark |
|:---------------------|------------------------|--------|
| `power/<id>`         | `on` / `standby`       | set power state of device |
| `active/<id>`        |                        | make the device "active" |
| `volume`             | `up` / `down`          | volume up and down |
> `<id>` referes to the logical cec id (TV is always 0)


## Publishing

The bridge publishes to `cec/status` (by default):
> This can be set in the config on the key `mqtt.topic_publish_prefix`. It will define everything before the wildcard `/#`. E.g. `topic_publish_prefix = foo/bar` will publish to `foo/bar/#`


| topic (behind the prefix) | body              | remark |
|:---------------------|------------------------|--------|
| `power/<id>`         | `on` / `standby`       |        |
> `<id>` referes to the logical cec id (TV is always 0)


# Config
Default config location is at `etc/cec2mqtt/config.yaml` (this file may not exists)

Default config is:

```
name: CEC2MQTT
mqtt:
  host: localhost
  port: 8883
  username:
  password:
  topic_subscribe_prefix: cec/set
  topic_publish_prefix: cec/status
cec:
  id: 1
  port:
  devices: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
```
> Most cases you just want to set `cec.devices` to the list of device ids you have (try cec2mqtt cecdevices)

# Service File Example

```
[Unit]
Description=cec mqtt bridge
After=syslog.target network.target

[Service]
Type=simple
PIDFile=/var/cec2mqtt/cec2mqtt.pid
ExecStart=/home/pi/.virtualenvs/cec/bin/cec2mqtt run
Restart=on-failure

[Install]
WantedBy=multi-user.target

```



# Interesting links
* https://github.com/nvella/mqtt-cec
* http://www.cec-o-matic.com/
* http://wiki.kwikwai.com/index.php?title=The_HDMI-CEC_bus