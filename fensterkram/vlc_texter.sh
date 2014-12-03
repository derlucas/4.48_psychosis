#!/bin/bash



vlc --no-audio --video-on-top --no-video-title-show --no-osd \
		--repeat --qt-notification 0 --no-video-deco --autoscale \
		http://walterebert.com/playground/video/hls/sintel-trailer.m3u8
