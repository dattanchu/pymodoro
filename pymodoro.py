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
    """Load config from defaults, file and arguments."""

    def __init__(self):
        self.load_defaults()
        self.load_user_data()
        self.load_from_file()
        self.load_from_args()

    def load_defaults(self):
        self.script_path = self._get_script_path()
        self.data_path = os.path.join(self.script_path, 'data')
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
        self.break_prefix = 'B '
        self.break_suffix = ''
        self.pomodoro_prefix = 'P '
        self.pomodoro_suffix = ''

        # Sound
        self.enable_sound = True
        self.enable_tick_sound = False
        self.session_sound_file = os.path.join(self.data_path, 'session.wav')
        self.break_sound_file = os.path.join(self.data_path, 'break.wav')
        self.tick_sound_file = os.path.join(self.data_path, 'tick.wav')

    def load_user_data(self):
        """
        Custom User Data

        Check the ~/.local/share/pymodoro directory for custom user
        files. This lets the user provide their own sound files which
        are used instead of the default ones.

        """
        self._user_dir = os.path.expanduser('~/.local/share/pymodoro')

        if not os.path.exists(self._user_dir):
            os.makedirs(self._user_dir)

        # Include any custom user sounds if present
        user_session_sound = os.path.join(self._user_dir, 'session.wav')
        user_break_sound = os.path.join(self._user_dir, 'break.wav')
        user_tick_sound = os.path.join(self._user_dir, 'tick.wav')

        if os.path.exists(user_session_sound):
            self.session_sound_file = user_session_sound
        if os.path.exists(user_break_sound):
            self.break_sound_file = user_break_sound
        if os.path.exists(user_tick_sound):
            self.tick_sound_file = user_tick_sound


    def load_from_file(self):
        self._parser = configparser.RawConfigParser()
        self._dir = os.path.expanduser('~/.config/pymodoro')
        self._file = os.path.join(self._dir, 'config')
        self._load_config_file()

    def _get_script_path(self):
        module_path = os.path.realpath(__file__)
        return os.path.dirname(module_path)

    def _load_config_file(self):
        if not os.path.exists(self._file):
            self._create_config_file()

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

    def _create_config_file(self):
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

    def load_from_args(self):
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

    IDLE_STATE = 'IDLE'
    ACTIVE_STATE = 'ACTIVE'
    BREAK_STATE = 'BREAK'
    WAIT_STATE = 'WAIT'

    def __init__(self):
        self.config = Config()
        self.session = os.path.expanduser(self.config.session_file)
        self.set_durations()
        self.running = True

    def run(self):
        """ Start main loop."""
        while self.running:
            self.update_state()
            self.print_output()
            self.tick_sound()
            self.wait()

    def update_state(self):
        """ Update the current state determined by timings."""
        if not hasattr(self, 'state'):
            self.state = self.IDLE_STATE

        current_state = self.state
        seconds_left = self.get_seconds_left()
        break_duration = self.config.break_duration_in_seconds
        break_elapsed = self.get_break_elapsed(seconds_left)

        if seconds_left is None:
            next_state = self.IDLE_STATE
        elif seconds_left > 0:
            next_state = self.ACTIVE_STATE
        elif break_elapsed < break_duration:
            next_state = self.BREAK_STATE
        else:
            next_state = self.WAIT_STATE

        if next_state is not current_state:
            self.send_notifications(next_state)
            self.state = next_state

    def send_notifications(self, next_state):
        """Send appropriate notifications when leaving a state."""
        current_state = self.state
        notification = None
        sound = None

        if current_state == self.ACTIVE_STATE:
            if next_state == self.BREAK_STATE:
                sound = self.config.session_sound_file
                notification = ["Worked enough.", "Time for a break!"]

        if current_state == self.BREAK_STATE:
            if next_state == self.WAIT_STATE:
                sound = self.config.break_sound_file
                notification = ["Break is over.", "Back to work!"]

        if notification:
            self.notify(notification)

        if sound:
            self.play_sound(sound)

    def print_output(self):
        """Print output determined by the current state."""
        auto_hide = self.config.auto_hide
        seconds_left = self.get_seconds_left()

        prefix = ""
        progress = ""
        timer = ""
        suffix = ""

        format = "%s%s%s%s\n"

        if self.state == self.IDLE_STATE and not auto_hide:
            prefix = self.config.pomodoro_prefix
            suffix = self.config.pomodoro_suffix
            progress = "-"

        elif self.state == self.ACTIVE_STATE:
            duration = self.config.session_duration_in_seconds
            output_seconds = self.get_output_seconds(seconds_left)
            output_minutes = self.get_minutes(seconds_left)

            prefix = self.config.pomodoro_prefix
            suffix = self.config.pomodoro_suffix
            progress = self.get_progress_bar(duration, seconds_left)
            timer = "%02d:%02d" % (output_minutes, output_seconds)
            format = "%s%s %s%s\n"

        elif self.state == self.BREAK_STATE:
            duration = self.config.break_duration_in_seconds
            break_seconds = self.get_break_seconds_left(seconds_left)
            output_seconds = self.get_output_seconds(break_seconds)
            output_minutes = self.get_minutes(break_seconds)

            prefix = self.config.break_prefix
            suffix = self.config.break_suffix
            progress = self.get_progress_bar(duration, break_seconds)
            timer = "%02d:%02d" % (output_minutes, output_seconds)
            format = "%s%s %s%s\n"

        elif self.state == self.WAIT_STATE:
            seconds = -seconds_left
            minutes = self.get_minutes(seconds)
            hours = self.get_hours(seconds)
            days = self.get_days(seconds)

            output_seconds = self.get_output_seconds(seconds)
            output_minutes = self.get_output_minutes(seconds)
            output_hours = self.get_output_hours(seconds)

            prefix = self.config.break_prefix
            suffix = self.config.break_suffix

            if minutes < 60:
                timer = "%02d:%02d min" % (minutes, output_seconds)
            elif hours < 24:
                timer = "%02d:%02d h" % (hours, output_minutes)
            elif days <= 7:
                timer = "%02d:%02d d" % (days, output_hours)
            else:
                timer = "Over a week"

        sys.stdout.write(format % (prefix, progress, timer, suffix))
        sys.stdout.flush()

    def wait(self):
        """Wait for the specified interval."""
        interval = self.config.update_interval_in_seconds
        time.sleep(interval)

    def tick_sound(self):
        """Play the Pomodoro tick sound if enabled."""
        enabled = self.config.enable_tick_sound
        if enabled and self.state == self.ACTIVE_STATE:
            self.play_sound(self.config.tick_sound_file)

    def get_seconds_left(self):
        """Return seconds remaining in the current session."""
        seconds_left = None
        session_duration = self.config.session_duration_in_seconds
        if os.path.exists(self.session):
            start_time = os.path.getmtime(self.session)
            seconds_left = session_duration - time.time() + start_time
        return seconds_left

    def get_break_elapsed(self, seconds_left):
        """Return the break elapsed in seconds"""
        break_elapsed = 0
        if seconds_left:
            break_elapsed = abs(seconds_left)
        return break_elapsed

    def set_durations(self):
        """Set durations from session values if available."""
        options = self.read_session_file()
        if len(options) > 0:
            self.set_session_duration(options[0])
        if len(options) > 1:
            self.set_break_duration(options[1])

    def read_session_file(self):
        """Get pomodoro and break durations from session as a list."""
        content = ""
        if os.path.exists(self.session):
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
        """Modify break duration."""
        break_duration_as_integer = self.convert_string_to_int(break_duration_as_string)
        if break_duration_as_integer != -1:
            self.config.break_duration_in_seconds = break_duration_as_integer * 60

    def get_break_seconds_left(self, seconds):
        return self.config.break_duration_in_seconds + seconds

    def get_progress_bar(self, duration_in_seconds, seconds):
        """Return progess bar using full and empty characters."""
        output = ""
        total_marks = self.config.total_number_of_marks
        left_to_right = self.config.left_to_right

        full_mark_character = self.config.session_full_mark_character
        empty_mark_character = self.config.empty_mark_character

        if self.state == self.BREAK_STATE:
            full_mark_character = self.config.break_full_mark_character

        if total_marks:
            seconds_per_mark = (duration_in_seconds / total_marks)
            number_of_full_marks = int(round(seconds / seconds_per_mark))

            # Reverse the display order
            if left_to_right:
                number_of_full_marks = total_marks - number_of_full_marks

            number_of_empty_marks = total_marks - number_of_full_marks

            full_marks = full_mark_character * number_of_full_marks
            empty_marks = empty_mark_character * number_of_empty_marks
            output = full_marks + empty_marks

        return output

    def get_days(self, seconds):
        """Convert seconds to days."""
        return int(seconds / 86400)

    def get_hours(self, seconds):
        """Convert seconds to hours."""
        return int(seconds / 3600)

    def get_minutes(self, seconds):
        """Convert seconds to minutes."""
        return int(seconds / 60)

    def get_output_hours(self, seconds):
        hours = self.get_hours(seconds)
        days = self.get_days(seconds)
        output_hours = int(hours - days * 24)
        return output_hours

    def get_output_minutes(self, seconds):
        hours = self.get_hours(seconds)
        minutes = self.get_minutes(seconds)
        output_minutes = int(minutes - hours * 60)
        return output_minutes

    def get_output_seconds(self, seconds):
        minutes = self.get_minutes(seconds)
        output_seconds = int(seconds - minutes * 60)
        return output_seconds

    def play_sound(self, sound_file):
        """Play specified sound file with aplay."""
        if self.config.enable_sound:
            os.system('aplay -q %s &' % sound_file)

    def notify(self, strings):
        """ Send a desktop notification."""
        try:
            Popen(['notify-send'] + strings)
        except OSError:
            pass

def main():
    pymodoro = Pymodoro()
    pymodoro.run()

if __name__ == "__main__":
    main()
