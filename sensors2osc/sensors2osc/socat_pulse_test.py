# -*- coding: utf-8 -*-

# This file is part of chaosc
#
# chaosc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# chaosc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with chaosc.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

from __future__ import absolute_import

import time, random

from sensors2osc.main import RingBuffer


class DataGenenerator(object):
    def  __init__(self):
        self.get_i = 0

    def read(self):
        value = None
        if self.get_i == 0:
            value = random.randint(1, 254)
        elif self.get_i == 1:
            value = random.sample((1, 245), 1)[0]
        elif self.get_i == 2:
            value = 0
        elif self.get_i == 3:
            value = 255
        elif self.get_i == 4:
            value = random.randint(1, 255)
        elif self.get_i == 5:
            value = random.randint(1, 255)

        self.get_i = (self.get_i + 1) % 6
        return value

def parse(ring_buffer, reader):
    t = r.read()
    print t
    ring_buffer.append(t)

    if t == 0:
        try:
            my_data = ring_buffer.getData()
            print my_data
        except ValueError, e:
            print e


ring_buffer = RingBuffer(6)
r = DataGenenerator()

while 1:
    parse(ring_buffer, r)
    time.sleep(0.5)
