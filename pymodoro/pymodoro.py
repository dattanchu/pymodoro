#!/usr/bin/env python
# -*- coding: utf-8 -*-
# authors: Dat Chu <dattanchu@gmail.com>
#          Dominik Mayer <dominik.mayer@gmail.com>
# Prerequisite
#  - aplay to play a sound of your choice

from __future__ import division

import os
from os import path
import sys
import time
import subprocess
from subprocess import Popen
from argparse import ArgumentParser


try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def get_days(seconds):
    """Convert seconds to days."""
    return seconds // 86400


def get_hours(seconds):
    """Convert seconds to hours."""
    return seconds // 3600


def get_minutes(seconds):
    """Convert seconds to minutes."""
    return seconds // 60


class PymodoroConfigParser(configparser.RawConfigParser):
    def __init__(self, defaults):
        configparser.RawConfigParser.__init__(self)
        defaults = PymodoroConfigParser._quote_strings(defaults)
        self.read_dict(defaults)

    @staticmethod
    def _quote_strings(settings):
        """Quote all strings with double quotes."""
        settings = {section: {key: (f'"{settings[section][key]}"'
                                    if type(settings[section][key]) is str
                                    else settings[section][key])
                              for key in settings[section]}
                    for section in settings}
        return settings

    def set_quoted_string(self, section, option, value):
        """
        Surround this string option in double quotes so whitespace can
        be included.
        """
        value = '"' + str(value) + '"'
        self.set(section, option, value)

    def get_quoted_string(self, section, option):
        """
        Remove double quotes from a string option.
        """
        return self.get(section, option).strip('"')


class Config(object):
    """Load config from defaults, file and arguments."""

    def __init__(self):
        self.init_paths()

        # Load defaults
        self._parser = self.defaults()
        self._load_settings(self._parser)

        # Create config file if it's missing.
        if not path.exists(self._config_file):
            with open(self._config_file, 'at') as f:
                self._parser.write(f)

        self.load_from_file(self._config_file)
        self.load_from_args()

        if self.enable_sound and not path.exists(self.session_sound_file):
            print(f"ERROR: Session end sound file '{self.session_sound_file}' does not exist.")
            sys.exit(1)
        if self.enable_sound and not path.exists(self.break_sound_file):
            print(f"ERROR: Break sound file '{self.break_sound_file}' does not exist.")
            sys.exit(1)
        if self.enable_tick_sound and not path.exists(self.tick_sound_file):
            print(f"ERROR: Tick sound file '{self.tick_sound_file}' does not exist.")
            sys.exit(1)

    def init_paths(self):
        """
        Determine locations of directories and files used by pymodoro. Missing
        directories are created, if applicable.

        Determines locations of: config directory and file, the cache
        directory, the resource directory (containing the default sounds) and
        the hooks directory.

        Prefer following the XDG Base Directory specification for the config
        and cache locations, if possible.
        """

        self._cache_home = os.environ.get('XDG_CACHE_HOME', '~/.cache')
        self._config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')

        # Determine location of config dir/file.
        old_config_dir = path.expanduser('~/.pymodoro')
        new_config_dir = path.join(self._config_home, 'pymodoro')

        if path.exists(old_config_dir):
            print("Warning: Using deprecated old-style config dir '{}'. Please"
                  " move it to '{}'.".format(old_config_dir, new_config_dir),
                  file=sys.stderr)
            self._config_dir = path.expanduser(old_config_dir)
        else:
            self._config_dir = path.expanduser(new_config_dir)

        self._config_file = path.join(self._config_dir, 'config')

        # For the cache directory, we simply use the XDG cache home instead of
        # creating a subdirectory.
        self._cache_dir = path.expanduser(self._cache_home)

        # Determine some other directories used by pymodoro
        self._hooks_dir = path.join(self._config_dir, "hooks")
        self._script_path = self._get_script_path()
        self._resource_dir = path.join(self._script_path, 'data')

        # Create missing directories.
        for d in (self._cache_dir, self._config_dir, self._hooks_dir):
            if not path.exists(d):
                os.makedirs(d)

    def defaults(self):
        return PymodoroConfigParser({
            'General': {
                'oneline': False,
                'autohide': False,
                'session': path.join(self._cache_dir, 'pomodoro_session'),
            },

            'Times': {
                'session_duration_secs': 25 * 60 + 1,
                'break_duration_secs': 5 * 60,
                'update_interval_secs': 1,
            },

            'Labels': {
                'pomodoro_prefix': 'P ',
                'pomodoro_suffix': '',
                'break_prefix': 'B ',
                'break_suffix': '',
            },

            'Progress Bar': {
                'left_to_right': False,
                'total_marks': 10,
                'session_character': '#',
                'break_character': '|',
                'empty_character': '·',
            },

            'Sound': {
                'enable': True,
                'tick': False,
                'sound_command': 'aplay -q %s &',
                'session_sound_file': path.join(self._resource_dir, 'session.wav'),
                'break_sound_file': path.join(self._resource_dir, 'break.wav'),
                'tick_sound_file': path.join(self._resource_dir, 'tick.wav'),
            },

            'Hooks': {
                'pomodoro_start': path.join(self._hooks_dir, 'start-pomodoro.py'),
                'pomodoro_end': path.join(self._hooks_dir, 'complete-pomodoro.py'),
            }
        })

    def _get_script_path(self):
        module_path = path.realpath(__file__)
        return path.dirname(module_path)

    def _load_settings(self, settings):
        """Initialize settings from a settings dict."""
        # General
        self.session_file = settings.get_quoted_string('General', 'session')
        self.enable_only_one_line = settings.getboolean('General', 'oneline')
        self.auto_hide = settings.getboolean('General', 'autohide')

        # Times
        self.session_duration_secs = settings.getint('Times', 'session_duration_secs')
        self.break_duration_secs = settings.getint('Times', 'break_duration_secs')
        self.update_interval_secs = settings.getint('Times', 'update_interval_secs')

        # Labels
        self.pomodoro_prefix = settings.get_quoted_string('Labels', 'pomodoro_prefix')
        self.pomodoro_suffix = settings.get_quoted_string('Labels', 'pomodoro_suffix')
        self.break_prefix = settings.get_quoted_string('Labels', 'break_prefix')
        self.break_suffix = settings.get_quoted_string('Labels', 'break_suffix')

        # Progress Bar
        self.total_number_of_marks = settings.getint('Progress Bar', 'total_marks')
        self.session_full_mark_character = settings.get_quoted_string('Progress Bar', 'session_character')
        self.break_full_mark_character = settings.get_quoted_string('Progress Bar', 'break_character')
        self.empty_mark_character = settings.get_quoted_string('Progress Bar', 'empty_character')
        self.left_to_right = settings.getboolean('Progress Bar', 'left_to_right')

        # Sound
        self.enable_sound = settings.getboolean('Sound', 'enable')
        self.enable_tick_sound = settings.getboolean('Sound', 'tick')
        self.sound_command = settings.get_quoted_string('Sound', 'sound_command')
        self.session_sound_file = settings.get_quoted_string('Sound', 'session_sound_file')
        self.break_sound_file = settings.get_quoted_string('Sound', 'break_sound_file')
        self.tick_sound_file = settings.get_quoted_string('Sound', 'tick_sound_file')

        # Files for hooks
        self.start_pomodoro_hook_file = path.join(self._hooks_dir,
                                                  "start-pomodoro.py")
        self.complete_pomodoro_hook_file = path.join(self._hooks_dir,
                                                    "complete-pomodoro.py")

    def load_from_file(self, config_path):
        self._parser.read(config_path)
        self._load_settings(self._parser)

    def load_from_args(self):
        arg_parser = ArgumentParser(
            description='Create a Pomodoro display for a status bar.'
        )

        arg_parser.add_argument(
            '-s',
            '--seconds',
            action='store_true',
            help='Changes format of input times from minutes to seconds.',
            dest='durations_secs'
        )
        arg_parser.add_argument(
            'session_duration',
            action='store',
            nargs='?',
            type=int,
            help='Pomodoro duration in minutes (default: 25).',
            metavar='POMODORO DURATION'
        )
        arg_parser.add_argument(
            'break_duration',
            action='store',
            nargs='?',
            type=int,
            help='Break duration in minutes (default: 5).',
            metavar='BREAK DURATION'
        )

        arg_parser.add_argument(
            '-f',
            '--file',
            action='store',
            help='Pomodoro session file (default: ~/.pomodoro_session).',
            metavar='PATH',
            dest='session_file'
        )
        arg_parser.add_argument(
            '-n',
            '--no-break',
            action='store_true',
            help='No break sound.',
            dest='no_break'
        )
        arg_parser.add_argument(
            '-ah',
            '--auto-hide',
            action='store_true',
            help='Hide output when session file is removed.',
            dest='auto_hide'
        )

        arg_parser.add_argument(
            '-i',
            '--interval',
            action='store',
            type=int,
            help='Update interval in seconds (default: 1).',
            metavar='DURATION',
            dest='update_interval_secs'
        )
        arg_parser.add_argument(
            '-l',
            '--length',
            action='store',
            type=int,
            help='Bar length in characters (default: 10).',
            metavar='CHARACTERS',
            dest='total_number_of_marks'
        )

        arg_parser.add_argument(
            '-p',
            '--pomodoro',
            action='store',
            help='Pomodoro full mark characters (default: #).',
            metavar='CHARACTER',
            dest='session_full_mark_character'
        )
        arg_parser.add_argument(
            '-b',
            '--break',
            action='store',
            help='Break full mark characters (default: |).',
            metavar='CHARACTER',
            dest='break_full_mark_character'
        )
        arg_parser.add_argument(
            '-e',
            '--empty',
            action='store',
            help='Empty mark characters (default: ·).',
            metavar='CHARACTER',
            dest='empty_mark_character'
        )

        arg_parser.add_argument(
            '-sp',
            '--pomodoro-sound',
            action='store',
            help='Pomodoro end sound file (default: session.wav).',
            metavar='PATH',
            dest='session_sound_file'
        )
        arg_parser.add_argument(
            '-sb',
            '--break-sound',
            action='store',
            help='Break end sound file (default: break.wav).',
            metavar='PATH',
            dest='break_sound_file'
        )
        arg_parser.add_argument(
            '-st',
            '--tick-sound',
            action='store',
            help='Ticking sound file (default: tick.wav).',
            metavar='PATH',
            dest='tick_sound_file'
        )
        arg_parser.add_argument(
            '-si',
            '--silent',
            action='store_true',
            help='Play no end sounds',
            dest='silent'
        )
        arg_parser.add_argument(
            '-t',
            '--tick',
            action='store_true',
            help='Play tick sound at every interval',
            dest='tick'
        )
        arg_parser.add_argument(
            '-sc',
            '--sound-command',
            action='store',
            help='Command called to play a sound. '
                 'Defaults to "aplay -q %%s &". %%s will be replaced with the '
                 'sound filename.',
            metavar='SOUND COMMAND',
            dest='sound_command'
        )
        arg_parser.add_argument(
            '-ltr',
            '--left-to-right',
            action='store_true',
            help='Display markers from left to right (incrementing marker '
                 'instead of decrementing)',
            dest='left_to_right'
        )
        arg_parser.add_argument(
            '-bp',
            '--break-prefix',
            action='store',
            help='String to display before, when we are in a break. '
                 'Defaults to "B". Can be used to format display for dzen.',
            metavar='BREAK PREFIX',
            dest='break_prefix'
        )
        arg_parser.add_argument(
            '-bs',
            '--break-suffix',
            action='store',
            help='String to display after, when we are in a break. '
                 'Defaults to "". Can be used to format display for dzen.',
            metavar='BREAK SUFFIX',
            dest='break_suffix'
        )
        arg_parser.add_argument(
            '-pp',
            '--pomodoro-prefix',
            action='store',
            help='String to display before, when we are in a pomodoro. '
                 'Defaults to "P". Can be used to format display for dzen.',
            metavar='POMODORO PREFIX',
            dest='pomodoro_prefix'
        )
        arg_parser.add_argument(
            '-ps',
            '--pomodoro-suffix',
            action='store',
            help='String to display after, when we are in a pomodoro. '
                 'Defaults to "". Can be used to format display for dzen.',
            metavar='POMODORO SUFFIX',
            dest='pomodoro_suffix'
        )

        arg_parser.add_argument(
            '-o',
            '--one-line',
            action='store_true',
            help='Print one line of output and quit.',
            dest='oneline'
        )

        args = arg_parser.parse_args()

        if args.session_duration:
            if args.durations_secs:
                self.session_duration_secs = args.session_duration
            else:
                self.session_duration_secs = args.session_duration * 60
        if args.break_duration:
            if args.durations_secs:
                self.break_duration_secs = args.break_duration
            else:
                self.break_duration_secs = args.break_duration * 60
        if args.update_interval_secs:
            self.update_interval_secs = args.update_interval_secs
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
        if args.sound_command:
            self.sound_command = args.sound_command
        if args.left_to_right:
            self.left_to_right = True
        if args.no_break:
            self.break_duration_secs = 0
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

        if args.oneline:
            self.enable_only_one_line = True


class Pymodoro(object):

    IDLE_STATE = 'IDLE'
    ACTIVE_STATE = 'ACTIVE'
    BREAK_STATE = 'BREAK'
    WAIT_STATE = 'WAIT'

    def __init__(self):
        self.config = Config()
        self.session = path.expanduser(self.config.session_file)
        self.set_durations()
        self.running = True
        # cache last time the session file was touched
        # to know if the session file contents should be re-read
        self.last_start_time = 0
        self.seconds_left = None

    def run(self):
        """Start main loop."""
        while self.running:
            self.update_state()
            self.print_output()
            self.tick_sound()
            if self.config.enable_only_one_line:
                break
            else:
                self.wait()

    def update_state(self):
        """Update the current state determined by timings."""
        if not hasattr(self, 'state'):
            self.state = self.IDLE_STATE

        self.seconds_left = self.get_seconds_left()
        seconds_left = self.seconds_left
        break_duration = self.config.break_duration_secs
        break_elapsed = self.get_break_elapsed(seconds_left)

        if seconds_left is None:
            self.state = self.IDLE_STATE
        elif seconds_left >= 0:
            self.state = self.ACTIVE_STATE
        elif break_elapsed <= break_duration:
            self.state = self.BREAK_STATE
        else:
            self.state = self.WAIT_STATE

        current_state = self.state

        if seconds_left is None:
            next_state = self.IDLE_STATE
        elif seconds_left > 1:
            next_state = self.ACTIVE_STATE
        elif break_elapsed + 1 < break_duration or seconds_left == 1:
            next_state = self.BREAK_STATE
        else:
            next_state = self.WAIT_STATE

        if next_state is not current_state:
            self.send_notifications(next_state)

            # Execute hooks
            if (current_state == self.ACTIVE_STATE and
                next_state == self.BREAK_STATE and
                path.exists(self.config.complete_pomodoro_hook_file)):
                subprocess.check_call(self.config.complete_pomodoro_hook_file)

            elif (current_state != self.ACTIVE_STATE and
                  next_state == self.ACTIVE_STATE and
                  path.exists(self.config.start_pomodoro_hook_file)):
                subprocess.check_call(self.config.start_pomodoro_hook_file)

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

    def make_output(self):
        """Make output determined by the current state."""
        auto_hide = self.config.auto_hide
        seconds_left = self.seconds_left

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
            duration = self.config.session_duration_secs
            output_seconds = self.get_output_seconds(seconds_left)
            output_minutes = get_minutes(seconds_left)

            prefix = self.config.pomodoro_prefix
            suffix = self.config.pomodoro_suffix
            progress = self.get_progress_bar(duration, seconds_left)
            timer = "%02d:%02d" % (output_minutes, output_seconds)
            format = "%s%s %s%s\n"

        elif self.state == self.BREAK_STATE:
            duration = self.config.break_duration_secs
            break_seconds = self.get_break_seconds_left(seconds_left)
            output_seconds = self.get_output_seconds(break_seconds)
            output_minutes = get_minutes(break_seconds)

            prefix = self.config.break_prefix
            suffix = self.config.break_suffix
            progress = self.get_progress_bar(duration, break_seconds)
            timer = "%02d:%02d" % (output_minutes, output_seconds)
            format = "%s%s %s%s\n"

        elif self.state == self.WAIT_STATE:
            seconds = -seconds_left
            minutes = get_minutes(seconds)
            hours = get_hours(seconds)
            days = get_days(seconds)

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

        return format % (prefix, progress, timer, suffix)

    def print_output(self):
        sys.stdout.write(self.make_output())
        sys.stdout.flush()

    def wait(self):
        """Wait for the specified interval."""
        interval = self.config.update_interval_secs
        time.sleep(interval)

    def tick_sound(self):
        """Play the Pomodoro tick sound if enabled."""
        enabled = self.config.enable_tick_sound
        if enabled and self.state == self.ACTIVE_STATE:
            self.play_sound(self.config.tick_sound_file)

    def get_seconds_left(self):
        """Return seconds remaining in the current session."""
        seconds_left = None
        if path.exists(self.session):
            start_time = path.getmtime(self.session)
            if start_time != self.last_start_time:
                # the session file has been updated
                # re-read the contents
                self.set_durations()
                self.last_start_time = start_time
            session_duration = self.config.session_duration_secs
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
        if path.exists(self.session):
            f = open(self.session)
            content = f.readline()
            f.close()
        return content.rsplit()

    def set_session_duration(self, session_duration_str):
        try:
            self.config.session_duration_secs = int(session_duration_str) * 60
        except ValueError:
            print(
                "Invalid session duration: {}.\n"
                "Try deleting your session file.".format(session_duration_str))
            sys.exit(1)

    def set_break_duration(self, break_duration_str):
        """Modify break duration."""
        try:
            self.config.break_duration_secs = int(break_duration_str) * 60
        except ValueError:
            print("Invalid break duration: {}.\n"
                  "Try deleting your session file.".format(break_duration_str))
            sys.exit(1)

    def get_break_seconds_left(self, seconds):
        return self.config.break_duration_secs + seconds

    def get_progress_bar(self, duration_secs, seconds):
        """Return progess bar using full and empty characters."""
        output = ""
        total_marks = self.config.total_number_of_marks
        left_to_right = self.config.left_to_right

        full_mark_character = self.config.session_full_mark_character
        empty_mark_character = self.config.empty_mark_character

        if self.state == self.BREAK_STATE:
            full_mark_character = self.config.break_full_mark_character

        if total_marks:
            seconds_per_mark = (duration_secs / total_marks)
            number_of_full_marks = int(round(seconds / seconds_per_mark))

            # Reverse the display order
            if left_to_right:
                number_of_full_marks = total_marks - number_of_full_marks

            number_of_empty_marks = total_marks - number_of_full_marks

            full_marks = full_mark_character * number_of_full_marks
            empty_marks = empty_mark_character * number_of_empty_marks
            output = full_marks + empty_marks

        return output

    def get_output_hours(self, seconds):
        hours = get_hours(seconds)
        days = get_days(seconds)
        output_hours = int(hours - days * 24)
        return output_hours

    def get_output_minutes(self, seconds):
        hours = get_hours(seconds)
        minutes = get_minutes(seconds)
        output_minutes = int(minutes - hours * 60)
        return output_minutes

    def get_output_seconds(self, seconds):
        minutes = get_minutes(seconds)
        output_seconds = int(seconds - minutes * 60)
        return output_seconds

    def play_sound(self, sound_file):
        """Play specified sound file with aplay by default."""
        if self.config.enable_sound:
            with open(os.devnull, 'wb') as devnull:
                subprocess.check_call(
                    self.config.sound_command % sound_file,
                    stdout=devnull,
                    stderr=subprocess.STDOUT,
                    shell=True
                )

    def notify(self, strings):
        """Send a desktop notification."""
        try:
            Popen(['notify-send', '--app-name', 'pymodoro'] + strings)
        except OSError:
            pass


def main():
    pymodoro = Pymodoro()
    pymodoro.run()


if __name__ == "__main__":
    main()
