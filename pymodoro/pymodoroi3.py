#!/usr/bin/env python
# -*- coding: utf-8 -*-
# authors: Vincent Jousse <vincent@jousse.org>
#
# Prerequisite
#  - py3status for i3bar
#  - pymodoro.py in your PYTHON_PATH or in the current directory

import os
import sys
import time
import math

# Append current path to the python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from pymodoro import Pymodoro

class Py3status:
    """
    Special class to allow pymodoro to be used as a module for
    py3status, a python wrapper for i3bar
    """

    color = None

    # Green
    start_color = "#8bf09b"
    # Red
    end_color = "#e94d44"
    # Yellow
    break_color = "#ddee5c" 

    def pymodoro_main(self, i3s_output_list, i3s_config):

        # Don't pass any arguments to pymodoro to avoid conflicts with
        # py3status arguments
        save_argv = sys.argv
        sys.argv = [sys.argv[0]]

        pymodoro = Pymodoro()
        pymodoro.update_state()

        # Get pymodoro output and remove newline
        text = pymodoro.make_output().rstrip()
        pymodoro.tick_sound()

        # Restore argv
        sys.argv = save_argv

        try:
            # If colour is installed, we will display a nice gradient
            # from red to green depending on how many time is left
            # in the current pomodoro
            from colour import Color
            start_c = Color(self.start_color)
            end_c = Color(self.end_color)
            break_c = Color(self.break_color)

            if pymodoro.state == pymodoro.ACTIVE_STATE:
                nb_minutes = int(math.floor(pymodoro.config.session_duration_in_seconds / 60))
                colors = list(end_c.range_to(start_c,nb_minutes))

                seconds_left = pymodoro.get_seconds_left()

                if seconds_left is not None:
                    nb_minutes_left = int(math.floor(seconds_left / 60))
                    if nb_minutes_left >=  len(colors):
                        nb_minutes_left = len(colors)-1
                    self.color = colors[nb_minutes_left].hex
                else:
                    self.color = start_c.hex
            else:
                self.color = break_c.hex 
            
        except ImportError:
            # If colour is not installed, use the default color
            pass

        response = {
            'full_text': text,
            'color': self.color,
            # Don't cache anything
            'cached_until': time.time()
        }

        return response

def main():
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.pymodoro_main([], config))
        sleep(1)

if __name__ == "__main__":
    main()
