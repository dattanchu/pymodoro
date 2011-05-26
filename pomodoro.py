#!/usr/bin/env python
# author: Dat Chu <dattanchu@gmail.com>
# Prerequisite
#  - aplay to play a sound of your choice
# To do
#  - add support for breaks
#  - add support for locking the screen with gnome-screensaver-command --lock
#  - add support for multiple counters
#  - allow configuration directly from Xmobar via flags
import time
import os
import sys

# configurations
pymodoro_directory = os.path.expanduser('~/.pymodoro')
session_file = pymodoro_directory + '/pomodoro_session'
session_duration = 5 * 60 # 25 minutes => 25 * 60
update_interval = 1 # 1 => 1 second sleep between updates
total_num_marks = 20
#minutes_per_mark = 5 # 5 => 5 minutes is represented as one #
full_mark = '#'
empty_mark = '·'

#sound_file = '/home/dchu/.pymodoro/rimshot.wav'
sound_file = pymodoro_directory + '/nokiaring.wav'

# constant infered from configurations
# total_num_marks = int(session_duration / 60 / minutes_per_mark + 0.5)
seconds_per_mark = (session_duration / total_num_marks)

# variables to keep track of sound playing
to_play_session_end_sound = False

# sanity check
if not os.path.exists(sound_file):
    print("Error: Cannot find sound file %s" % sound_file)
if not os.path.exists(session_file):
    print("Error: Cannot find session file %s. Please make it." % session_file)


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
        output_seconds_left = int(seconds_left - minutes_left * 60)

        # Construct progress indicator
        num_mark = (seconds_left/seconds_per_mark)
        progress_bar = full_mark * int(num_mark) + empty_mark * (total_num_marks - int(num_mark))

        # Print out the status
        sys.stdout.write("P %s %02d:%02d\n" % (progress_bar, minutes_left, output_seconds_left))
        
        # We are in a session, so we should play a sound once done
        to_play_session_end_sound = True
    else:
        # Calculate the time since last pomodoro
        seconds_left = -seconds_left
        minutes_left = int(seconds_left / 60)
        hours_left = int(minutes_left / 60)
        seconds_left = int(seconds_left - minutes_left * 60)
        
        # Pomodoro is done, print time since
        sys.stdout.write("B %02d:%02d\n" % (minutes_left, seconds_left))
        
        # If we were in a session, play a sound
        if to_play_session_end_sound:
            to_play_session_end_sound = False
            os.system('aplay -q %s' % sound_file)

    sys.stdout.flush()
    
    # sleep a little bit
    time.sleep(update_interval)

    # update time left
    seconds_left = get_seconds_left()
