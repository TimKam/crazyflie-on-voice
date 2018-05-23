#!/usr/bin/env python3

# Author: Christopher Blöcker, Timotheus Kampik, Tobias Sundqvist, Marcus?

from __future__      import print_function

import logging
import numpy   as np
import sys
import termios

from cflib           import crazyflie, crtp
from controller      import ControllerThread
from multiprocessing import Process, Queue
from server          import runServer, runPathPlanner

# Set a channel - if set to None, the first available crazyflie is used
URI = 'radio://0/110/2M'


def read_input(file=sys.stdin):
    """Registers keystrokes and yield these every time one of the
    *valid_characters* are pressed."""
    old_attrs = termios.tcgetattr(file.fileno())
    new_attrs = old_attrs[:]
    new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
    try:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
        while True:
            try:
                yield sys.stdin.read(1)
            except (KeyboardInterrupt, EOFError):
                break
    finally:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)


def handle_keyboard_input(control, server):
    pos_step = 0.1 # [m]
    yaw_step = 5   # [deg]

    for ch in read_input():
        if ch == 'h':
            print('Key map:')
            print('>: Increase thrust (non-control mode)')
            print('<: Decrease thrust (non-control mode)')
            print('Q: quit program')
            print('e: Enable motors')
            print('q: Disable motors')
            print('w: Increase x-reference by ', pos_step, 'm.')
            print('s: Decrease x-reference by ', pos_step, 'm.')
            print('a: Increase y-reference by ', pos_step, 'm.')
            print('d: Decrease y-reference by ', pos_step, 'm.')
            print('i: Increase z-reference by ', pos_step, 'm.')
            print('k: Decrease z-reference by ', pos_step, 'm.')
            print('j: Increase yaw-reference by ', yaw_step, 'm.')
            print('l: Decrease yaw-reference by ', yaw_step, 'deg.')
            print('7: Toggle debug logging')
        elif ch == '>':
            control.increase_thrust()
            print('Increased thrust to', control.thrust_r)
        elif ch == '<':
            control.decrease_thrust()
            print('Decreased thrust to', control.thrust_r)
        elif ch == 'w':
            control.pos_ref[0] += pos_step
            print('Reference position changed to :', control.pos_ref)
        elif ch == 's':
            control.pos_ref[0] -= pos_step
            print('Reference position changed to :', control.pos_ref)
        elif ch == 'a':
            control.pos_ref[1] += pos_step
            print('Reference position changed to :', control.pos_ref)
        elif ch == 'd':
            control.pos_ref[1] -= pos_step
            print('Reference position changed to :', control.pos_ref)
        elif ch == 'i':
            control.pos_ref[2] += pos_step
            print('Reference position changed to :', control.pos_ref)
        elif ch == 'k':
            control.pos_ref[2] -= pos_step
            print('Reference position changed to :', control.pos_ref)
        elif ch == 'j':
            control.yaw_ref += np.radians(yaw_step)
            print('Yaw reference changed to :',
                    np.degrees(control.yaw_ref), 'deg.')
        elif ch== 'l':
            control.yaw_ref -= np.radians(yaw_step)
            print('Yaw reference changed to :',
                    np.degrees(control.yaw_ref), 'deg.')
        elif ch == ' ':
            control.pos_ref[2] = 0.0
            print('Reference position changed to :', control.pos_ref)
        elif ch == 'e':
            control.enable()
        elif ch == 'q':
            if not control.enabled:
                print('Uppercase Q quits the program')
            control.disable()
        elif ch == 'Q':
            server.terminate()
            control.disable()
            print('Bye!')
            break
        elif ch == '7':
            control.toggle_debug()
        else:
            print('Unhandled key', ch, 'was pressed')


if __name__ == "__main__":
    logging.basicConfig()
    crtp.init_drivers(enable_debug_driver = False)

    # the command queue for the crazyflie
    crazyflieCommandQueue = Queue()

    # set up the crazyflie
    cf = crazyflie.Crazyflie(rw_cache = './cache')
    control = ControllerThread(cf, crazyflieCommandQueue)
    control.start()

    # start the web interface to the crazyflie
    server = Process(target = runServer, args = ("0.0.0.0", 8000, crazyflieCommandQueue))
    server.start()

    # start the path planning server
    pathPlanner = Process(target = runPathPlanner, args = ("0.0.0.0", 8001, crazyflieCommandQueue))
    pathPlanner.start()

    # connect to the crazyflie
    if URI is None:
        print('Scanning for Crazyflies...')
        available = crtp.scan_interfaces()
        if available:
            print('Found Crazyflies:')
            for i in available:
                print('-', i[0])
            URI = available[0][0]
        else:
            print('No Crazyflies found!')
            sys.exit(1)

    print('Connecting to', URI)
    cf.open_link(URI)

    handle_keyboard_input(control, server)

    cf.close_link()
