#!/bin/bash

dump_grabber -H 192.168.1.23 -P 7110 -s -o 192.168.1.34 -p 6001 -L -4 > /dev/null 2>/dev/null & 


#vlc --no-audio --video-on-top --no-video-title-show --no-osd \
#		--repeat --qt-notification 0 --no-video-deco --autoscale \
#		http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8
