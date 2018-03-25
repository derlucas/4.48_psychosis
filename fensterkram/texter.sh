#!/bin/bash


mplayer -title "PSYtexter" -demuxer lavf http://192.168.1.35:9001/stream.mjpeg 

#vlc --no-audio --video-on-top --no-video-title-show --no-osd \
#		--repeat --qt-notification 0 --no-video-deco --autoscale \
#		/home/lucas/home/ctdo/theater/psychose/streaming/Seren*
