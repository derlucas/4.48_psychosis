#!/bin/bash

# vlc mit Kamera
STR="Universal Pictures"
wmctrl -r $STR -e 0,1600,0,640,480
wmctrl -r $STR -b add,sticky,above

# vlc mit annes texter
STR="http://walter"
wmctrl -r $STR -e 0,2240,0,640,480
wmctrl -r $STR -b add,sticky,above

# datenstroeme
STR="http://devimages"
wmctrl -r $STR -e 0,2880,0,640,480
wmctrl -r $STR -b add,sticky,above

#das HealthDisplay
wmctrl -r "HD Main" -e 0,2570,480,950,570
wmctrl -r "HD Main" -b add,sticky,above

killall devilspie
devilspie &
