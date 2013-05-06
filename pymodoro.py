#!/usr/bin/env python
# -*- coding: utf-8 -*-
# authors: Dat Chu <dattanchu@gmail.com>
#          Dominik Mayer <dominik.mayer@gmail.com>
# Prerequisite
#  - aplay to play a sound of your choice

import os
import sys
import time
from argparse import ArgumentParser
from subprocess import Popen

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class Config(object):

    def __init__(self):

        self.script_path = self._get_script_path()
        self.set_default_values()
        self.get_from_file()
        self.get_from_arguments()

    def set_default_values(self):

        # Default Config Values
        self.session_file = '~/.pomodoro_session'
        self.auto_hide = False

        # Times
        self.session_duration_in_seconds = 25 * 60 + 1
        self.break_duration_in_seconds = 5 * 60
        self.update_interval_in_seconds = 1

        # Progress Bar
        self.total_number_of_marks = 10
        self.session_full_mark_character = '#'
        self.break_full_mark_character = '|'
        self.empty_mark_character = '·'
        self.left_to_right = False

        # Prefixes
        self.break_prefix = 'B'
        self.break_suffix = ''
        self.pomodoro_prefix = 'P'
        self.pomodoro_suffix = ''

        # Sound
        self.enable_sound = True
        self.enable_tick_sound = False
        self.session_sound_file = 'nokiaring.wav'
        self.break_sound_file = 'rimshot.wav'
        self.tick_sound_file = 'klack.wav'

    def get_from_file(self):
        self._parser = configparser.RawConfigParser()
        self._dir = os.path.expanduser('~/.config/pymodoro')
        self._file = os.path.join(self._dir, 'config')
        self.load_config_file()

    def _get_script_path(self):
        module_path = os.path.realpath(__file__)
        return os.path.dirname(module_path)

    def load_config_file(self):

        if not os.path.exists(self._file):
            self.create_config_file()

        self._parser.read(self._file)

        self.session_file = self._config_get_quoted_string('General', 'session')
        self.auto_hide = self._parser.getboolean('General', 'autohide')

        self.pomodoro_prefix = self._config_get_quoted_string('Labels', 'pomodoro_prefix')
        self.pomodoro_suffix = self._config_get_quoted_string('Labels', 'pomodoro_suffix')
        self.break_prefix = self._config_get_quoted_string('Labels', 'break_prefix')
        self.break_suffix = self._config_get_quoted_string('Labels', 'break_suffix')

        self.left_to_right = self._parser.getboolean('Progress Bar', 'left_to_right')
        self.total_number_of_marks = self._parser.getint('Progress Bar', 'total_marks')
        self.session_full_mark_character = self._config_get_quoted_string('Progress Bar', 'session_character')
        self.break_full_mark_character = self._config_get_quoted_string('Progress Bar', 'break_character')
        self.empty_mark_character = self._config_get_quoted_string('Progress Bar', 'empty_character')

        self.enable_sound = self._parser.getboolean('Sound', 'enable')
        self.enable_tick_sound = self._parser.getboolean('Sound', 'tick')

    def create_config_file(self):

        self._parser.add_section('General')
        self._parser.set('General', 'autohide', str(self.auto_hide).lower())
        self._config_set_quoted_string('General', 'session', self.session_file)

        self._parser.add_section('Labels')
        self._config_set_quoted_string('Labels', 'pomodoro_prefix', self.pomodoro_prefix)
        self._config_set_quoted_string('Labels', 'pomodoro_suffix', self.pomodoro_suffix)
        self._config_set_quoted_string('Labels', 'break_prefix', self.break_prefix)
        self._config_set_quoted_string('Labels', 'break_suffix', self.break_suffix)

        self._parser.add_section('Progress Bar')
        self._parser.set('Progress Bar', 'left_to_right', str(self.left_to_right).lower())
        self._parser.set('Progress Bar', 'total_marks', self.total_number_of_marks)
        self._config_set_quoted_string('Progress Bar', 'session_character', self.session_full_mark_character)
        self._config_set_quoted_string('Progress Bar', 'break_character', self.break_full_mark_character)
        self._config_set_quoted_string('Progress Bar', 'empty_character', self.empty_mark_character)

        self._parser.add_section('Sound')
        self._parser.set('Sound', 'enable', str(self.enable_sound).lower())
        self._parser.set('Sound', 'tick', str(self.enable_tick_sound).lower())

        if not os.path.exists(self._dir):
            os.makedirs(self._dir)

        with open(self._file, 'wb') as configfile:
            self._parser.write(configfile)

    def _config_set_quoted_string(self, section, option, value):
        """
        Surround this string option in double quotes so whitespace can
        be included.
        """
        value = '"' + str(value) + '"'
        self._parser.set(section, option, value)

    def _config_get_quoted_string(self, section, option):
        """
        Remove doublequotes from a string option.
        """
        return self._parser.get(section, option).strip('"')

    def get_from_arguments(self):

        arg_parser = ArgumentParser(description='Create a Pomodoro display for a status bar.')

        arg_parser.add_argument('-s', '--seconds', action='store_true', help='Changes format of input times from minutes to seconds.', dest='durations_in_seconds')
        arg_parser.add_argument('session_duration', action='store', nargs='?', type=int, help='Pomodoro duration in minutes (default: 25).', metavar='POMODORO DURATION')
        arg_parser.add_argument('break_duration', action='store', nargs='?', type=int, help='Break duration in minutes (default: 5).', metavar='BREAK DURATION')

        arg_parser.add_argument('-f', '--file', action='store', help='Pomodoro session file (default: ~/.pomodoro_session).', metavar='PATH', dest='session_file')
        arg_parser.add_argument('-n', '--no-break', action='store_true', help='No break sound.', dest='no_break')
        arg_parser.add_argument('-ah', '--auto-hide', action='store_true', help='Hide output when session file is removed.', dest='auto_hide')

        arg_parser.add_argument('-i', '--interval', action='store', type=int, help='Update interval in seconds (default: 1).', metavar='DURATION', dest='update_interval_in_seconds')
        arg_parser.add_argument('-l', '--length', action='store', type=int, help='Bar length in characters (default: 10).', metavar='CHARACTERS', dest='total_number_of_marks')

        arg_parser.add_argument('-p', '--pomodoro', action='store', help='Pomodoro full mark characters (default: #).', metavar='CHARACTER', dest='session_full_mark_character')
        arg_parser.add_argument('-b', '--break', action='store', help='Break full mark characters (default: |).', metavar='CHARACTER', dest='break_full_mark_character')
        arg_parser.add_argument('-e', '--empty', action='store', help='Empty mark characters (default: ·).', metavar='CHARACTER', dest='empty_mark_character')

        arg_parser.add_argument('-sp', '--pomodoro-sound', action='store', help='Pomodoro end sound file (default: nokiaring.wav).', metavar='PATH', dest='session_sound_file')
        arg_parser.add_argument('-sb', '--break-sound', action='store', help='Break end sound file (default: rimshot.wav).', metavar='PATH', dest='break_sound_file')
        arg_parser.add_argument('-st', '--tick-sound', action='store', help='Ticking sound file (default: klack.wav).', metavar='PATH', dest='tick_sound_file')
        arg_parser.add_argument('-si', '--silent', action='store_true', help='Play no end sounds', dest='silent')
        arg_parser.add_argument('-t', '--tick', action='store_true', help='Play tick sound at every interval', dest='tick')
        arg_parser.add_argument('-ltr', '--left-to-right', action='store_true', help='Display markers from left to right (incrementing marker instead of decrementing)', dest='left_to_right')
        arg_parser.add_argument('-bp', '--break-prefix', action='store', help='String to display before, when we are in a break. Default to "B". Can be used to format display for dzen.', metavar='BREAK PREFIX', dest='break_prefix')
        arg_parser.add_argument('-bs', '--break-suffix', action='store', help='String to display after, when we are in a break. Default to "". Can be used to format display for dzen.', metavar='BREAK SUFFIX', dest='break_suffix')
        arg_parser.add_argument('-pp', '--pomodoro-prefix', action='store', help='String to display before, when we are in a pomodoro. Default to "P". Can be used to format display for dzen.', metavar='POMODORO PREFIX', dest='pomodoro_prefix')
        arg_parser.add_argument('-ps', '--pomodoro-suffix', action='store', help='String to display after, when we are in a pomodoro. Default to "". Can be used to format display for dzen.', metavar='POMODORO SUFFIX', dest='pomodoro_suffix')

        args = arg_parser.parse_args()

        if args.session_duration:
            if args.durations_in_seconds:
                self.session_duration_in_seconds = args.session_duration
            else:
                self.session_duration_in_seconds = args.session_duration * 60
        if args.break_duration:
            if args.durations_in_seconds:
                self.break_duration_in_seconds = args.break_duration
            else:
                self.break_duration_in_seconds = args.break_duration * 60
        if args.update_interval_in_seconds:
            self.update_interval_in_seconds = args.update_interval_in_seconds
        if args.total_number_of_marks:
            self.total_number_of_marks = args.total_number_of_marks
        if args.session_full_mark_character:
            self.session_full_mark_character = args.session_full_mark_character
        if args.break_full_mark_character:
            self.break_full_mark_character = args.break_full_mark_character
        if args.empty_mark_character:
            self.empty_mark_character = args.empty_mark_character
        if args.session_file:
            self.session_file = args.session_file
        if args.session_sound_file:
            self.session_sound_file = args.session_sound_file
        if args.break_sound_file:
            self.break_sound_file = args.break_sound_file
        if args.tick_sound_file:
            self.tick_sound_file = args.tick_sound_file
        if args.silent:
            self.enable_sound = False
        if args.tick:
            self.enable_tick_sound = True
        if args.left_to_right:
            self.left_to_right = True
        if args.no_break:
            self.break_duration_in_seconds = 0
        if args.auto_hide:
            self.auto_hide = True
        if args.break_prefix:
            self.break_prefix = args.break_prefix
        if args.break_suffix:
            self.break_suffix = args.break_suffix
        if args.pomodoro_prefix:
            self.pomodoro_prefix = args.pomodoro_prefix
        if args.pomodoro_suffix:
            self.pomodoro_suffix = args.pomodoro_suffix


class Pymodoro(object):

    def __init__(self):

        self.config = Config()
        self.session = os.path.expanduser(self.config.session_file)
        self.last_start_time = 0

        # variables to keep track of sound playing
        self.play_sound_after_session = False
        self.play_sound_after_break = False

    def get_seconds_left(self):
        if os.path.exists(self.session):
            start_time = os.path.getmtime(self.session)
            if self.last_start_time != start_time:
                self.last_start_time = start_time
                self.setup_new_timer()
            return self.config.session_duration_in_seconds - time.time() + start_time
        else:
            return

    def setup_new_timer(self):
        options = self.read_session_file()
        if len(options) > 0:
            self.set_session_duration(options[0])
        if len(options) > 1:
            self.set_break_duration(options[1])

    def read_session_file(self):
        f = open(self.session)
        content = f.readline()
        f.close()
        return content.rsplit()

    def set_session_duration(self, session_duration_as_string):
        session_duration_as_integer = self.convert_string_to_int(session_duration_as_string)
        if session_duration_as_integer != -1:
            self.config.session_duration_in_seconds = session_duration_as_integer * 60

    def convert_string_to_int(self, string):
        if not string.isdigit():
            return -1
        else:
            return int(string)

    def set_break_duration(self, break_duration_as_string):
        break_duration_as_integer = self.convert_string_to_int(break_duration_as_string)
        if break_duration_as_integer != -1:
            self.config.break_duration_in_seconds = break_duration_as_integer * 60

    def print_session_output(self, seconds_left):
        self.print_output(self.config.pomodoro_prefix,
                          self.config.session_duration_in_seconds,
                          seconds_left,
                          self.config.session_full_mark_character,
                          self.config.pomodoro_suffix)

    def print_break_output(self, seconds_left):
        break_seconds_left = self.get_break_seconds_left(seconds_left)
        self.print_output(self.config.break_prefix,
                          self.config.break_duration_in_seconds,
                          break_seconds_left,
                          self.config.break_full_mark_character,
                          self.config.break_suffix)

    def get_break_seconds_left(self, seconds):
        return self.config.break_duration_in_seconds + seconds

    def print_output(self, description, duration_in_seconds, seconds, full_mark_character, suffix):
        minutes = self.get_minutes(seconds)
        output_seconds = self.get_output_seconds(seconds)
        progress_bar = self.print_progress_bar(duration_in_seconds, seconds, full_mark_character)
        output = description + "%s %02d:%02d" % (progress_bar, minutes, output_seconds) + suffix
        sys.stdout.write(output + "\n")

    def get_minutes(self, seconds):
        return int(seconds / 60)

    def get_output_seconds(self, seconds):
        minutes = self.get_minutes(seconds)
        return int(seconds - minutes * 60)

    def print_progress_bar(self, duration_in_seconds, seconds, full_mark_character):
        if self.config.total_number_of_marks != 0:
            seconds_per_mark = (duration_in_seconds / self.config.total_number_of_marks)
            number_of_full_marks = int(round(seconds / seconds_per_mark))
            # Reverse the display order
            if self.config.left_to_right:
                number_of_full_marks = self.config.total_number_of_marks - number_of_full_marks
            output = " " + self.print_full_marks(number_of_full_marks, full_mark_character) \
                + self.print_empty_marks(self.config.total_number_of_marks - number_of_full_marks)
        else:
            output = ""
        return output

    def print_full_marks(self, number_of_full_marks, full_mark_character):
        return full_mark_character * number_of_full_marks

    def print_empty_marks(self, number_of_empty_marks):
        return self.config.empty_mark_character * number_of_empty_marks

    def print_break_output_hours(self, seconds):
        seconds = -seconds
        minutes = self.get_minutes(seconds)
        output_minutes = self.get_output_minutes(seconds)
        hours = self.get_hours(seconds)
        output_seconds = self.get_output_seconds(seconds)

        if minutes < 60:
            sys.stdout.write("%s %02d:%02d min%s\n" % (self.config.break_prefix,
                                                       minutes,
                                                       output_seconds,
                                                       self.config.break_suffix))
        elif hours < 24:
            sys.stdout.write("%s %02d:%02d h%s\n" % (self.config.break_prefix,
                                                     hours,
                                                     output_minutes,
                                                     self.config.break_suffix))
        else:
            days = int(hours / 24)
            output_hours = hours - days * 24
            sys.stdout.write("%s %02d d %02d h%s\n" % (self.config.break_prefix,
                                                       days,
                                                       output_hours,
                                                       self.config.break_suffix))

    def get_hours(self, seconds):
        return int(seconds / 3600)

    def get_output_minutes(self, seconds):
        hours = self.get_hours(seconds)
        minutes = self.get_minutes(seconds)
        return int(minutes - hours * 60)

    def play_sound(self, sound_file):
        if self.config.enable_sound:
            script_path = self.config.script_path
            sound_path = os.path.join(script_path, sound_file)
            os.system('aplay -q %s &' % sound_path)

    def notify_end_of_session(self):
        if self.play_sound_after_session:
            self.play_sound_after_session = False
            self.play_sound(self.config.session_sound_file)
            self.notify(["Worked enough.", "Time for a break!"])

    def notify_end_of_break(self):
        if self.play_sound_after_break:
            self.play_sound_after_break = False
            self.play_sound(self.config.break_sound_file)
            self.notify(["Break is over.", "Back to work!"])

    def notify(self, strings):
        try:
            Popen(['notify-send'] + strings)
        except OSError:
            pass

    def run(self):

        # Repeat printing the status of our session
        seconds_left = self.get_seconds_left()
        while True:
            if seconds_left is None:
                if self.config.auto_hide:
                    sys.stdout.write("\n")
                else:
                    sys.stdout.write("%s —%s\n" % (self.config.pomodoro_prefix,
                                                     self.config.pomodoro_suffix))
            elif 0 < seconds_left:
                self.print_session_output(seconds_left)
                self.play_sound_after_session = True
                if self.config.enable_tick_sound:
                    self.play_sound(self.config.tick_sound_file)
            elif -self.config.break_duration_in_seconds <= seconds_left < 0:
                self.notify_end_of_session()
                self.print_break_output(seconds_left)
                if self.config.break_duration_in_seconds != 0:
                    self.play_sound_after_break = True
            else:
                self.notify_end_of_session()  # Needed in case break duration = 0
                self.notify_end_of_break()
                self.print_break_output_hours(seconds_left)

            sys.stdout.flush()
            time.sleep(self.config.update_interval_in_seconds)
            seconds_left = self.get_seconds_left()


if __name__ == "__main__":
    pymodoro = Pymodoro()
    pymodoro.run()
