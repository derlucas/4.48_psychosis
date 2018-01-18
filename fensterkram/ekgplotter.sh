#!/bin/bash

#ekgplotter -o 192.168.1.34 -p 6002 -L > /dev/null 2>/dev/null &
ekgplotter -o 192.168.1.34 -H 192.168.1.23 -p 6002 -s >/dev/null 2>/dev/null & 

#vlc --no-audio --video-on-top --no-video-title-show --no-osd \
#		--repeat --qt-notification 0 --no-video-deco --autoscale \
#		http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8
