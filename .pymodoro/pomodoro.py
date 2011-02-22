#!/usr/bin/env python
# author: Dat Chu <dattanchu@gmail.com>
# Prerequisite
#  - aplay to play a sound of your choice
# To do
#  - what if session_file doesn't exist
#  - add support for breaks
import time
import os
import sys

# configurations
session_file = '/home/dchu/.pymodoro/pomodoro_session'
sound_file = '/home/dchu/.pymodoro/rimshot.wave'
session_duration = 25 * 60 # 25 minutes => 25 * 60
update_interval = 1 # 1 => 1 second sleep between updates
minutes_per_mark = 5 # 5 => 5 minutes is represented as one #

# constant infered from configurations
total_num_marks = int(session_duration / 60 / minutes_per_mark + 0.5)

# variables to keep track of sound playing
to_play_session_end_sound = False

# how to find seconds_left
def get_seconds_left():
    # find out the start time
    start_time = os.path.getmtime(session_file)
    return session_duration - time.time() + start_time

# Repeat printing the status of our session
seconds_left = get_seconds_left()
while True:
    if seconds_left > 0:
        # Calculate the time left
        minutes_left = int(seconds_left / 60)
        seconds_left = int(seconds_left - minutes_left * 60)

        # Construct progress indicator
        num_mark = (minutes_left/minutes_per_mark + 1)
        progress_bar = '#' * num_mark + ' ' * (total_num_marks - num_mark)

        # Print out the status
        sys.stdout.write("P %s %02d:%02d\n" % (progress_bar, minutes_left, seconds_left))
        
        # We are in a session, so we should play a sound once done
        to_play_session_end_sound = True
    else:
        # Pomodoro is done, print a blank template
        sys.stdout.write('Pomodoro Break\n')
        
        # If we were in a session, play a sound
        if to_play_session_end_sound:
            to_play_session_end_sound = False
            os.system('aplay -q %s' % sound_file)

    sys.stdout.flush()
    
    # sleep a little bit
    time.sleep(update_interval)

    # update time left
    seconds_left = get_seconds_left()
