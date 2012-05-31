#!/usr/bin/env python
# -*- coding: utf-8 -*-
# authors: Dat Chu <dattanchu@gmail.com>
#          Dominik Mayer <dominik.mayer@gmail.com>
# Prerequisite
#  - aplay to play a sound of your choice

import time
import os
import sys
import argparse
import subprocess

from datetime import timedelta

# ———————————————————————————— CONFIGURATIONS ————————————————————————————

# Files and Folders
pymodoro_directory_config = os.path.dirname(__file__)
session_file = '~/.pomodoro_session'

# Times
session_duration_in_seconds = 25 * 60 +1
break_duration_in_seconds = 5 * 60
update_interval_in_seconds = 1

# Progress Bar
total_number_of_marks = 10
session_full_mark_character = '#'
break_full_mark_character = '|'
empty_mark_character = '·'
left_to_right = False

# Prefixes
break_prefix = 'B'
break_suffix = ''
pomodoro_prefix = 'P'
pomodoro_suffix = ''

# Sound
enable_sound = True
enable_tick_sound = False
session_sound_file_config = 'nokiaring.wav'
break_sound_file_config = 'rimshot.wav'
tick_sound_file_config = 'klack.wav'

# —————————————————————————— END CONFIGURATIONS ———————————————————————————

# constant inferred from configurations
pymodoro_directory = os.path.expanduser(pymodoro_directory_config)
session_sound_file = pymodoro_directory + '/' + session_sound_file_config
break_sound_file = pymodoro_directory + '/' + break_sound_file_config
tick_sound_file = pymodoro_directory + '/' + tick_sound_file_config

# variables
last_start_time = 0

def set_configuration_from_arguments(args):
    #print(args)
    global session_duration_in_seconds
    global break_duration_in_seconds
    global update_interval_in_seconds
    global total_number_of_marks
    global session_full_mark_character
    global break_full_mark_character
    global empty_mark_character
    global session_file
    global session_sound_file
    global break_sound_file
    global tick_sound_file
    global enable_sound
    global enable_tick_sound
    global left_to_right
    global break_prefix
    global break_suffix
    global pomodoro_prefix
    global pomodoro_suffix

    if args.session_duration:
        if args.durations_in_seconds == True:
            session_duration_in_seconds = args.session_duration
        else:
            session_duration_in_seconds = args.session_duration * 60
    if args.break_duration:
        if args.durations_in_seconds == True:
            break_duration_in_seconds = args.break_duration
        else:
            break_duration_in_seconds = args.break_duration * 60
    if args.update_interval_in_seconds:
        update_interval_in_seconds = args.update_interval_in_seconds
    if args.total_number_of_marks:
        total_number_of_marks = args.total_number_of_marks
    if args.session_full_mark_character:
        session_full_mark_character = args.session_full_mark_character
    if args.break_full_mark_character:
        break_full_mark_character = args.break_full_mark_character
    if args.empty_mark_character:
        empty_mark_character = args.empty_mark_character
    if args.session_file:
        session_file = args.session_file
    if args.session_sound_file:
        session_sound_file = args.session_sound_file
    if args.break_sound_file:
        break_sound_file = args.break_sound_file
    if args.tick_sound_file:
        tick_sound_file = args.tick_sound_file
    if args.silent:
        enable_sound = False
    if args.tick:
        enable_tick_sound = True
    if args.left_to_right:
        left_to_right = True
    if args.no_break:
        break_duration_in_seconds = 0
    if args.break_prefix:
        break_prefix = args.break_prefix
    if args.break_suffix:
        break_suffix = args.break_suffix
    if args.pomodoro_prefix:
        pomodoro_prefix = args.pomodoro_prefix
    if args.pomodoro_suffix:
        pomodoro_suffix = args.pomodoro_suffix

def get_seconds_left():
    if os.path.exists(session_file):
        global last_start_time
        start_time = os.path.getmtime(session_file)
        if last_start_time != start_time:
            last_start_time = start_time
            setup_new_timer()
        return session_duration_in_seconds - time.time() + start_time
    else:
        return

def setup_new_timer():
    options = read_session_file()
    if len(options) > 0:
        set_session_duration(options[0])
    if len(options) > 1:
        set_break_duration(options[1])

def read_session_file():
    f = open(session_file)
    content = f.readline()
    f.close()
    return content.rsplit()

def set_session_duration(session_duration_as_string):
    global session_duration_in_seconds
    session_duration_as_integer = convert_string_to_int(session_duration_as_string)
    if session_duration_as_integer != -1:
        session_duration_in_seconds = session_duration_as_integer * 60

def convert_string_to_int(string):
    if not string.isdigit():
        #print("Session File may only contain digits!")
        return -1
    else:
        return int(string)

def set_break_duration(break_duration_as_string):
    global break_duration_in_seconds
    break_duration_as_integer = convert_string_to_int(break_duration_as_string)
    if break_duration_as_integer != -1:
        break_duration_in_seconds = break_duration_as_integer * 60

def print_session_output(seconds_left):
    print_output(pomodoro_prefix, session_duration_in_seconds, seconds_left, session_full_mark_character, pomodoro_suffix)

def print_break_output(seconds_left):
    break_seconds_left = get_break_seconds_left(seconds_left)
    print_output(break_prefix, break_duration_in_seconds, break_seconds_left, break_full_mark_character, break_suffix)

def get_break_seconds_left(seconds):
    return break_duration_in_seconds + seconds

def print_output(description, duration_in_seconds, seconds, full_mark_character, suffix):
    minutes = get_minutes(seconds)
    output_seconds = get_output_seconds(seconds)
    progress_bar = print_progress_bar(duration_in_seconds, seconds, full_mark_character)
    output = description + "%s %02d:%02d" % (progress_bar, minutes, output_seconds) + suffix
    sys.stdout.write(output+"\n")

def get_minutes(seconds):
    return int(seconds / 60)

def get_output_seconds(seconds):
    minutes = get_minutes(seconds)
    return int(seconds - minutes * 60)

def print_progress_bar(duration_in_seconds, seconds, full_mark_character):
    if total_number_of_marks != 0:
        seconds_per_mark = (duration_in_seconds / total_number_of_marks)
        number_of_full_marks = int(round(seconds / seconds_per_mark))
        # Reverse the display order
        if left_to_right:
            number_of_full_marks = total_number_of_marks - number_of_full_marks
        output = " " + print_full_marks(number_of_full_marks, full_mark_character) \
            + print_empty_marks(total_number_of_marks - number_of_full_marks)
    else:
        output = ""
    return output

def print_full_marks(number_of_full_marks, full_mark_character):
    return full_mark_character * number_of_full_marks

def print_empty_marks(number_of_empty_marks):
    return empty_mark_character * number_of_empty_marks

def print_break_output_hours(seconds):
    seconds = -seconds
    minutes = get_minutes(seconds)
    output_minutes = get_output_minutes(seconds)
    hours = get_hours(seconds)
    output_seconds = get_output_seconds(seconds)

    if minutes < 60:
        sys.stdout.write("B %02d:%02d min\n" % (minutes, output_seconds))
    elif hours < 24:
        sys.stdout.write("B %02d:%02d h\n" % (hours, output_minutes))
    else:
        days = int(hours/24)
        output_hours = hours - days * 24
        sys.stdout.write("B %02d d %02d h\n" % (days, output_hours))

def get_hours(seconds):
    return int(seconds / 3600)

def get_output_minutes(seconds):
    hours = get_hours(seconds)
    minutes = get_minutes(seconds)
    return int(minutes - hours * 60)

def play_sound(sound_file):
    if enable_sound:
        os.system('aplay -q %s &' % sound_file)

def notify_end_of_session():
    global play_sound_after_session
    if play_sound_after_session:
        play_sound_after_session = False
        play_sound(session_sound_file)
        notify(["Worked enough.", "Time for a break!"])

def notify_end_of_break():
    global play_sound_after_break
    if play_sound_after_break:
        play_sound_after_break = False
        play_sound(break_sound_file)
        notify(["Break is over.", "Back to work!"])

def notify(strings):
    try:
        subprocess.Popen(['notify-send'] + strings)
    except OSError as e:
        pass

def main():
    # Parse command line arguments
    global session_file
    global play_sound_after_session
    global play_sound_after_break
    global tick_sound_file
    global enable_tick_sound
    global pomodoro_prefix
    global pomodoro_suffix

    parser = argparse.ArgumentParser(description='Create a Pomodoro display for a status bar.')

    parser.add_argument('-s', '--seconds', action='store_true', help='Changes format of input times from minutes to seconds.', dest='durations_in_seconds')
    parser.add_argument('session_duration', action='store', nargs='?', type=int, help='Pomodoro duration in minutes (default: 25).', metavar='POMODORO DURATION')
    parser.add_argument('break_duration', action='store', nargs='?', type=int, help='Break duration in minutes (default: 5).', metavar='BREAK DURATION')

    parser.add_argument('-f', '--file', action='store', help='Pomodoro session file (default: ~/.pomodoro_session).', metavar='PATH', dest='session_file')
    parser.add_argument('-n', '--no-break', action='store_true', help='No break sound.', dest='no_break')

    parser.add_argument('-i', '--interval', action='store', type=int, help='Update interval in seconds (default: 1).', metavar='DURATION', dest='update_interval_in_seconds')
    parser.add_argument('-l', '--length', action='store', type=int, help='Bar length in characters (default: 10).', metavar='CHARACTERS', dest='total_number_of_marks')

    parser.add_argument('-p', '--pomodoro', action='store', help='Pomodoro full mark characters (default: #).', metavar='CHARACTER', dest='session_full_mark_character')
    parser.add_argument('-b', '--break', action='store', help='Break full mark characters (default: |).', metavar='CHARACTER', dest='break_full_mark_character')
    parser.add_argument('-e', '--empty', action='store', help='Empty mark characters (default: ·).', metavar='CHARACTER', dest='empty_mark_character')

    parser.add_argument('-sp', '--pomodoro-sound', action='store', help='Pomodoro end sound file (default: nokiaring.wav).', metavar='PATH', dest='session_sound_file')
    parser.add_argument('-sb', '--break-sound', action='store', help='Break end sound file (default: rimshot.wav).', metavar='PATH', dest='break_sound_file')
    parser.add_argument('-st', '--tick-sound', action='store', help='Ticking sound file (default: klack.wav).', metavar='PATH', dest='tick_sound_file')
    parser.add_argument('-si', '--silent', action='store_true', help='Play no end sounds', dest='silent')
    parser.add_argument('-t', '--tick', action='store_true', help='Play tick sound at every interval', dest='tick')
    parser.add_argument('-ltr', '--left-to-right', action='store_true', help='Display markers from left to right (incrementing marker instead of decrementing)', dest='left_to_right')
    parser.add_argument('-bp', '--break-prefix', action='store', help='String to display before, when we are in a break. Default to "B". Can be used to format display for dzen.', metavar='BREAK PREFIX', dest='break_prefix')
    parser.add_argument('-bs', '--break-suffix', action='store', help='String to display after, when we are in a break. Default to "". Can be used to format display for dzen.', metavar='BREAK SUFFIX', dest='break_suffix')
    parser.add_argument('-pp', '--pomodoro-prefix', action='store', help='String to display before, when we are in a pomodoro. Default to "B". Can be used to format display for dzen.', metavar='POMODORO PREFIX', dest='pomodoro_prefix')
    parser.add_argument('-ps', '--pomodoro-suffix', action='store', help='String to display after, when we are in a pomodoro. Default to "". Can be used to format display for dzen.', metavar='POMODORO SUFFIX', dest='pomodoro_suffix')

    args = parser.parse_args()
    set_configuration_from_arguments(args)
    session_file = os.path.expanduser(session_file)

# variables to keep track of sound playing
    play_sound_after_session = False
    play_sound_after_break = False

# sanity check
    if not os.path.exists(session_sound_file):
        print("Error: Cannot find sound file %s" % session_sound_file)
    if not os.path.exists(break_sound_file):
        print("Error: Cannot find sound file %s" % break_sound_file)
    if not os.path.exists(tick_sound_file):
        print("Error: Cannot find sound file %s" % tick_sound_file)

# Repeat printing the status of our session
    seconds_left = get_seconds_left()
    while True:
        if seconds_left == None:
            sys.stdout.write("%s —%s\n" % (pomodoro_prefix, pomodoro_suffix))
        elif 0 < seconds_left:
            print_session_output(seconds_left)
            play_sound_after_session = True
            if enable_tick_sound:
                play_sound(tick_sound_file)
        elif -break_duration_in_seconds <= seconds_left < 0:
            notify_end_of_session()
            print_break_output(seconds_left)
            if break_duration_in_seconds != 0:
                play_sound_after_break = True
        else:
            notify_end_of_session() # Needed in case break duration = 0
            notify_end_of_break()
            print_break_output_hours(seconds_left)

        sys.stdout.flush()

        time.sleep(update_interval_in_seconds)

        seconds_left = get_seconds_left()


if __name__ == "__main__": main()
