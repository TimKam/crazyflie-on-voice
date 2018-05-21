import numpy           as np
import time
import transformations as trans

from cflib.crazyflie.log import LogConfig
from threading           import Thread
from multiprocessing     import Process
from path                import *
from requests            import post
from json                import dumps

# constants
K_height_proportional = 0.25  # this should not be lower than 0.25
K_height_derivative   = 0.15
K_height_integral     = 0.05

K_position_proportional = 12
K_position_derivative   = 13
K_position_integral     = 0

K_yaw_derivative        = 1

C = 100000
m = 0.0327
g = 9.82


class Command():
    def __init__(self):
        pass

    def execute(self, drone):
        pass

class DistanceCommand(Command):
    def __init__(self, dx, dy, dz):
        Command.__init__(self)
        self.dx = dx
        self.dy = dy
        self.dz = dz

    def execute(self, drone):
        drone.setRelativeTarget(self.dx, self.dy, self.dz)

class PositionCommand(Command):
    def __init__(self, x, y, z):
        Command.__init__(self)
        self.x = x
        self.y = y
        self.z = z

    def execute(self, drone):
        drone.setAbsoluteTarget(self.x, self.y, self.z)

class StartCommand(Command):
    def __init__(self):
        Command.__init__(self)

    def execute(self, drone):
        drone.startMotors()

class StopCommand(Command):
    def __init__(self):
        Command.__init__(self)

    def execute(self, drone):
        drone.stopMotors()


def planPath(drone, dx, dy, dz):
    try:
        start  = Point(drone.pos_ref[0],      drone.pos_ref[1],      drone.pos_ref[2])
        target = Point(drone.pos_ref[0] + dx, drone.pos_ref[1] + dy, drone.pos_ref[2] + dz)

        planningStart = time.time()
        path = drone.scene.planPath(start, target)
        print(path)
        if drone.debug:
            print("[DEBUG] Path planning took {:.2f}s.".format(time.time() - planningStart))
        for waypoint in path:
            drone.commandQueue.put(PositionCommand(waypoint.x, waypoint.y, waypoint.z))
    except Exception as e:
        print("[ERROR] {}".format(e))


class ControllerThread(Thread):
    period_in_ms = 20  # Control period. [ms]
    thrust_step = 5000 # Thrust step with W/S. [65535 = 100% PWM duty cycle]
    thrust_initial = 0
    thrust_limit = (0, 65535)
    roll_limit   = (-30.0, 30.0)
    pitch_limit  = (-30.0, 30.0)
    yaw_limit    = (-200.0, 200.0)
    enabled = False
    debug   = True

    # to integrate over the error
    dt     = period_in_ms/1000.0
    ex_int = 0
    ey_int = 0
    ez_int = 0

    def __init__(self, cf, commandQueue):
        super(ControllerThread, self).__init__()
        self.cf = cf
        self.commandQueue = commandQueue

        # Reset state
        self.disable(stop=False)

        # Keeps track of when we last printed
        self.last_time_print = 0.0

        # Connect some callbacks from the Crazyflie API
        self.cf.connected.add_callback(self._connected)
        self.cf.disconnected.add_callback(self._disconnected)
        self.cf.connection_failed.add_callback(self._connection_failed)
        self.cf.connection_lost.add_callback(self._connection_lost)
        self.send_setpoint = self.cf.commander.send_setpoint

        # Pose estimate from the Kalman filter
        self.pos = np.r_[0.0, 0.0, 0.0]
        self.vel = np.r_[0.0, 0.0, 0.0]
        self.attq = np.r_[0.0, 0.0, 0.0, 1.0]
        self.R = np.eye(3)

        # Attitide (roll, pitch, yaw) from stabilizer
        self.stab_att = np.r_[0.0, 0.0, 0.0]

        # This makes Python exit when this is the only thread alive.
        self.daemon = True

    def _connected(self, link_uri):
        print('Connected to', link_uri)

        log_stab_att = LogConfig(name='Stabilizer', period_in_ms=self.period_in_ms)
        log_stab_att.add_variable('stabilizer.roll', 'float')
        log_stab_att.add_variable('stabilizer.pitch', 'float')
        log_stab_att.add_variable('stabilizer.yaw', 'float')
        self.cf.log.add_config(log_stab_att)

        log_pos = LogConfig(name='Kalman Position', period_in_ms=self.period_in_ms)
        log_pos.add_variable('kalman.stateX', 'float')
        log_pos.add_variable('kalman.stateY', 'float')
        log_pos.add_variable('kalman.stateZ', 'float')
        self.cf.log.add_config(log_pos)

        log_vel = LogConfig(name='Kalman Velocity', period_in_ms=self.period_in_ms)
        log_vel.add_variable('kalman.statePX', 'float')
        log_vel.add_variable('kalman.statePY', 'float')
        log_vel.add_variable('kalman.statePZ', 'float')
        self.cf.log.add_config(log_vel)

        log_att = LogConfig(name='Kalman Attitude', period_in_ms=self.period_in_ms)
        log_att.add_variable('kalman.q0', 'float')
        log_att.add_variable('kalman.q1', 'float')
        log_att.add_variable('kalman.q2', 'float')
        log_att.add_variable('kalman.q3', 'float')
        self.cf.log.add_config(log_att)

        if log_stab_att.valid and log_pos.valid and log_vel.valid and log_att.valid:
            log_stab_att.data_received_cb.add_callback(self._log_data_stab_att)
            log_stab_att.error_cb.add_callback(self._log_error)
            log_stab_att.start()

            log_pos.data_received_cb.add_callback(self._log_data_pos)
            log_pos.error_cb.add_callback(self._log_error)
            log_pos.start()

            log_vel.error_cb.add_callback(self._log_error)
            log_vel.data_received_cb.add_callback(self._log_data_vel)
            log_vel.start()

            log_att.error_cb.add_callback(self._log_error)
            log_att.data_received_cb.add_callback(self._log_data_att)
            log_att.start()
        else:
            raise RuntimeError('One or more of the variables in the configuration was not'
                               'found in log TOC. Will not get any position data.')

    def _connection_failed(self, link_uri, msg):
        print('Connection to %s failed: %s' % (link_uri, msg))

    def _connection_lost(self, link_uri, msg):
        print('Connection to %s lost: %s' % (link_uri, msg))

    def _disconnected(self, link_uri):
        print('Disconnected from %s' % link_uri)

    def _log_data_stab_att(self, timestamp, data, logconf):
        self.stab_att = np.r_[data['stabilizer.roll'],
                              data['stabilizer.pitch'],
                              data['stabilizer.yaw']]

    def _log_data_pos(self, timestamp, data, logconf):
        self.pos = np.r_[data['kalman.stateX'],
                         data['kalman.stateY'],
                         data['kalman.stateZ']]

    def _log_data_vel(self, timestamp, data, logconf):
        vel_bf = np.r_[data['kalman.statePX'],
                       data['kalman.statePY'],
                       data['kalman.statePZ']]
        self.vel = np.dot(self.R, vel_bf)

    def _log_data_att(self, timestamp, data, logconf):
        # NOTE q0 is real part of Kalman state's quaternion, but
        # transformations.py wants it as last dimension.
        self.attq = np.r_[data['kalman.q1'], data['kalman.q2'],
                          data['kalman.q3'], data['kalman.q0']]
        # Extract 3x3 rotation matrix from 4x4 transformation matrix
        self.R = trans.quaternion_matrix(self.attq)[:3, :3]
        #r, p, y = trans.euler_from_quaternion(self.attq)

    def _log_error(self, logconf, msg):
        print('Error when logging %s: %s' % (logconf.name, msg))

    def make_position_sanity_check(self):
      # We assume that the position from the LPS should be
      # [-20m, +20m] in xy and [0m, 5m] in z
      if np.max(np.abs(self.pos[:2])) > 20 or self.pos[2] < 0 or self.pos[2] > 5:
        raise RuntimeError('Position estimate out of bounds', self.pos)

    def run(self):
        """Control loop definition"""
        while not self.cf.is_connected():
            time.sleep(0.2)

        print('Waiting for position estimate to be good enough...')
        self.reset_estimator()
        self.make_position_sanity_check();

        # how accurately do we want the drone to reach its position?
        tolerance  = 0.2 # in meters

        self.pos_ref    = self.pos
        self.yaw_ref    = 0.0
        self.stop_motor = False
        position_found  = False

        print('[INFO ] Initial positional reference:', self.pos_ref)
        print('[INFO ] Initial thrust reference:', self.thrust_r)
        print('[INFO ] Ready! Press e to enable motors, h for help and Q to quit')

        log_file_name = 'flightlog_' + time.strftime("%Y%m%d_%H%M%S") + '.csv'
        with open(log_file_name, 'w') as fh:
            t0 = time.time()
            while True:
                time_start = time.time()

                # set the new target position if we have reached the current target sufficiently well
                if np.linalg.norm(self.pos_ref - self.pos) < tolerance and not position_found:
                    position_found = True

                if position_found and not self.commandQueue.empty():
                    self.commandQueue.get().execute(self)
                    position_found = False

                # calculate the control signals to reach the desired position
                self.calc_control_signals()

                if self.enabled:
                    sp = (self.roll_r, self.pitch_r, self.yawrate_r, int(self.thrust_r))
                    self.send_setpoint(*sp)
                    # Log data to file for analysis
                    ld = np.r_[time.time() - t0]
                    ld = np.append(ld, np.asarray(sp))
                    ld = np.append(ld, self.pos_ref)
                    ld = np.append(ld, self.yaw_ref)
                    ld = np.append(ld, self.pos)
                    ld = np.append(ld, self.vel)
                    ld = np.append(ld, self.attq)
                    ld = np.append(ld, (np.reshape(self.R, -1)))
                    ld = np.append(ld, trans.euler_from_quaternion(self.attq))
                    ld = np.append(ld, self.stab_att)
                    fh.write(','.join(map(str, ld)) + '\n')
                    fh.flush()
                self.loop_sleep(time_start)

    def calc_control_signals(self):
        roll, pitch, yaw  = trans.euler_from_quaternion(self.attq)

        # Compute control errors in position
        ex, ey, ez = self.pos_ref - self.pos

        vx, vy, vz = self.vel
        self.ex_int += ex * self.dt
        self.ey_int += ey * self.dt
        self.ez_int += ez * self.dt

        phi_ref    =      K_position_proportional * ex - K_position_derivative * vx + K_position_integral * self.ex_int
        theta_ref  =   - (K_position_proportional * ey - K_position_derivative * vy + K_position_integral * self.ey_int)
        psi_ref    =                                     K_yaw_derivative      * self.yawrate_r
        thrust_ref = C * (K_height_proportional   * ez - K_height_derivative   * vz + K_height_integral   * self.ez_int + m*g)

        # The code below will simply send the thrust that you can set using
        # the keyboard and put all other control signals to zero. It also
        # shows how, using numpy, you can threshold the signals to be between
        # the lower and upper limits defined by the arrays *_limit
        self.roll_r    = np.clip(theta_ref, *self.roll_limit)
        self.pitch_r   = np.clip(phi_ref, *self.pitch_limit)
        self.yawrate_r = np.clip(psi_ref, *self.yaw_limit)
        self.thrust_r  = np.clip(thrust_ref, *self.thrust_limit)

        if self.debug and (time.time() - 2.0) > self.last_time_print:
            self.last_time_print = time.time()

            print("ref:      ({:.2f}, {:.2f}, {:.2f}, {:.2f})".format(self.pos_ref[0], self.pos_ref[1], self.pos_ref[2], self.yaw_ref))
            print("pos:      ({:.2f}, {:.2f}, {:.2f}, {:.2f})".format(self.pos[0], self.pos[1], self.pos[2], yaw))
            print("vel:      ({:.2f}, {:.2f}, {:.2f})".format(self.vel[1], self.vel[1], self.vel[2]))
            print("error:    ({:.2f}, {:.2f}, {:.2f})".format(ex, ey, ez))
            print("integral: ({:.2f}, {:.2f}, {:.2f})".format(self.ex_int, self.ey_int, self.ez_int))
            print("control:  ({:.2f}, {:.2f}, {:.2f}, {:.2f})".format(self.roll_r, self.pitch_r, self.yawrate_r, self.thrust_r))
            print("")


    def reset_estimator(self):
        self.cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        self.cf.param.set_value('kalman.resetEstimation', '0')
        # Sleep a bit, hoping that the estimator will have converged
        # Should be replaced by something that actually checks...
        time.sleep(1.5)

    def disable(self, stop=True):
        if stop:
            self.send_setpoint(0.0, 0.0, 0.0, 0)
        if self.enabled:
            print('Disabling controller')
        self.enabled = False
        self.roll_r    = 0.0
        self.pitch_r   = 0.0
        self.yawrate_r = 0.0
        self.thrust_r  = self.thrust_initial

    def enable(self):
        if not self.enabled:
            print('Enabling controller')
        # Need to send a zero setpoint to unlock the controller.
        self.send_setpoint(0.0, 0.0, 0.0, 0)
        # let it take off a bit
        self.pos_ref = self.pos + np.r_[0.0, 0.0, 0.3]
        self.enabled = True
        # reset the integrated error!
        self.ex_int = 0
        self.ey_int = 0
        self.ez_int = 0

    def loop_sleep(self, time_start):
        """ Sleeps the control loop to make it run at a specified rate """
        delta_time = 1e-3*self.period_in_ms - (time.time() - time_start)
        if delta_time > 0:
            time.sleep(delta_time)
        else:
            print('Deadline missed by', -delta_time, 'seconds. Too slow control loop!')

    def increase_thrust(self):
        self.thrust_r += self.thrust_step
        self.thrust_r = min(self.thrust_r, 0xffff)

    def decrease_thrust(self):
        self.thrust_r -= self.thrust_step
        self.thrust_r = max(0, self.thrust_r)

    def toggle_debug(self):
        print("[DEBUG] Switching debug output {:s}".format("off" if self.debug else "on"))
        self.debug = not self.debug

    def setRelativeTarget(self, dx, dy, dz):
        json = dumps({ "start"  : (self.pos_ref[0],      self.pos_ref[1],      self.pos_ref[2])
                     , "target" : (self.pos_ref[0] + dx, self.pos_ref[1] + dy, self.pos_ref[2] + dz)
                     })
        t = Thread(target = post, args = ("http://localhost:8001", json))
        t.daemon = True
        t.start()

    def setAbsoluteTarget(self, x, y, z):
        self.pos_ref = np.r_[x, y, z]

        if self.debug:
            print("[DEBUG] Setting reference position to ({:.2f}, {:.2f}, {:.2f})".format(self.pos_ref[0], self.pos_ref[1], self.pos_ref[2]))

    def stopMotors(self):
        #self.stop_motor = True
        self.disable()
        if self.debug:
            print("[DEBUG] Stopping motors!")

    def startMotors(self):
        #self.stop_motor = False
        self.enable()
        if self.debug:
            print("[DEBUG] Starting motors!")
