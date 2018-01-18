#!/bin/bash

killall devilspie
devilspie &

# ekg plotter
STR="EKGPlotterMain"
wmctrl -r $STR -e 0,1600,0,640,480
wmctrl -r $STR -b add,sticky,above

# datenstroeme
STR="DumpGrabberMain"
wmctrl -r $STR -e 0,2240,0,640,480
wmctrl -r $STR -b add,sticky,above

# vlc mit annes texter
STR="PSYtexter"
wmctrl -r $STR -e 0,2882,0,640,480
wmctrl -r $STR -b add,sticky,above

# vlc mit Kamera
#STR="PSYwebcam"
#wmctrl -r $STR -e 0,1600,480,780,600
#wmctrl -r $STR -b add,sticky,above


#das HealthDisplay
wmctrl -r "HD Main" -e 0,2570,480,950,570
wmctrl -r "HD Main" -b add,sticky,above

