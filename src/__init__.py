import time, sys

from src.command_loop import start_command_loop

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

try:
    uri = sys.argv[1]
except IndexError:
    print('Please provide the URI of your Crazyflie, e.g. "radio://0/80/250K"')
    quit()

print(f'Connecting to Crazyflie {uri}...')
cflib.crtp.init_drivers(enable_debug_driver=False)

with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)
    print('Starting command loop')
    start_command_loop(cf)
