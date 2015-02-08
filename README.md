# Pymodoro

## Running

### Xmobar

Put the files into a new folder called **.pymodoro** inside your home folder. Configure your xmobar to display pymodoro with

    Run CommandReader "~/.pymodoro/pymodoro.py" "pomodoro"

Then add it to your template.

### Dzen2

Add the following configuration to your Dzen2 configuration file to retrieve the current status of your Pomodoro and paste it in your display.

    ^fg(\#FFFFFF)${execi 10 python ~/.pymodoro/pymodoro.py -o}


## Install

To install Pymodoro system wide, run the setup.py script like this:

    python setup.py install

## Usage

A new Pomodoro -- 25 minutes followed by a break of 5 minutes -- is started by changing the timestamp of ~/.pomodoro_session. This can be done by the shell command:

    touch ~/.pomodoro_session

If you want to use counters with different times, write them into the session file. The first number specifies the length of the Pomodoro in minutes, the second one the length of the break. Both numbers are optional. Example:

    echo "20 2" > ~/.pomodoro_session

### Keybindings

The easiest way is to define keybindings for the commands.

#### Xmonad

Configure xmonad to start a new Pomodoro session by adding this to your xmonad.hs:

    -- start a pomodoro
    , ((modMask, xK_n), spawn "touch ~/.pomodoro_session")

Or:

    -- start a pomodoro
    , ("M-n", spawn "touch ~/.pomodoro_session")

This way, whenever you hit modMask + n, you will start a new pomodoro.

## Configure

You can set all the options via command line paramters. For a detailed description run:

    ~/.pymodoro.py --help

It is no longer needed to edit the script itself. If you still want to do it, open up the file **~/.pymodoro/pymodoro.py**.

## Credits

* Thanks to Mirko Horstmann for [the ticking sound](http://www.freesound.org/people/m1rk0/sounds/50070/).
* Session and Break sounds from Soothing Alerts by [Adam Dachis](http://adachis.kinja.com)
