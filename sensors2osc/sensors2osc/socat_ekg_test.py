#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of sensors2osc package
#
# sensors2osc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# sensors2osc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with sensors2osc.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

# used this line before opening that script
# socat -d -d PTY,raw,echo=0,link=/tmp/pty1,b115200,user=stefan PTY,raw,echo=0,link=/tmp/pty2,b115200,user=stefan

import serial, sys, time, random, struct


def get_steps(pulse_rate, rate):
    beat_length = 60. / pulse_rate
    steps_pre =  int(beat_length / rate) + 1
    used_sleep_time = beat_length / steps_pre
    steps = int(beat_length / used_sleep_time)
    return steps, used_sleep_time

serial_sock = serial.Serial()
serial_sock.port = sys.argv[1]
serial_sock.baudrate = 115200
serial_sock.timeout = 0
serial_sock.open()

data_points = 0

sleep_time = 0.04

min_puls = 70
max_pulse = 130
pulse = random.randint(min_puls, max_pulse)

steps, sleep_time = get_steps(pulse, sleep_time)
count = 0
delta = 1


result = list()

print "pulse", pulse
print "sleep_time", sleep_time
print "steps", steps

while 1:
    value = random.randint(0, steps)
    if count < int(steps / 100. * 20):
        value = random.randint(0,20)
    elif count < int(steps / 100. * 30):
        value = random.randint(20, 30)
    elif count < int(steps / 100. * 40):
        value = random.randint(30,100)
    elif count < int(steps / 2.):
        value = random.randint(100,200)
    elif count == int(steps / 2.):
        value = 255
    elif count < int(steps / 100. * 60):
        value = random.randint(100, 200)
    elif count < int(steps / 100. * 70):
        value = random.randint(50, 100)
    elif count < int(steps / 100. * 80):
        value = random.randint(20, 50)
    elif count <= steps:
        value = random.randint(0,20)
    elif count >= steps:
        count = 0

    #if data_points % (5 * steps) == 0:
        #print "new steps", steps, delta
        #steps += delta

    #if steps <= min_steps:
        #delta = 1
    #elif steps >= max_steps:
        #print "change step sign", steps, delta
        #delta = -1

    time.sleep(sleep_time)
    count += 1
    #data_points += 1
    serial_sock.write(struct.pack("B", value))
