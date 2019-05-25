#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
import math
import time

from twist_controller import Controller

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')
        self.dbw_enabled = False
        self.linear_velocity = 0
        self.angular_velocity = 0
        self.current_velocity = 0
	self.drive_by_wire_first_input_time = 0
        vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        brake_deadband = rospy.get_param('~brake_deadband', .1)
        decel_limit = rospy.get_param('~decel_limit', -5)
        accel_limit = rospy.get_param('~accel_limit', 1.)
        wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        max_steer_angle = rospy.get_param('~max_steer_angle', 8.)
	self.max_braking_percent = rospy.get_param('~max_braking_percentage', -0.1)
        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)
	self.dbw_enable_sub = rospy.Subscriber('/vehicle/dbw_enabled', Bool,  self.dbw_enabled_callback)
	self.current_velocity_sub = rospy.Subscriber('/current_velocity', TwistStamped, self.current_velocity_callback)
	self.twist_cmd_sub = rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_cmd_callback)
        # TODO: Create `TwistController` object

        self.controller = Controller(wheel_base,steer_ratio,0,max_lat_accel,max_steer_angle,accel_limit,decel_limit, vehicle_mass)

        # TODO: Subscribe to all the topics you need to

        self.loop()

    def loop(self):
        rate = rospy.Rate(50) # 50Hz
        while not rospy.is_shutdown():
            # TODO: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled
            # throttle, brake, steering = self.controller.control(<proposed linear velocity>,
            #                                                     <proposed angular velocity>,
            #                                                     <current linear velocity>,
            #                                                     <dbw status>,
            #                                                     <any other argument you need>)
            # if <dbw is enabled>:
	    if self.drive_by_wire_first_input_time == 0:
	    	self.drive_by_wire_first_input_time = time.time()*1000
            if self.dbw_enabled:
                throttle, brake, steering = self.controller.control(self.linear_velocity,self.angular_velocity,self.current_velocity)
                	#giving sometime for tf and warm up first
		if time.time()*1000 - self.drive_by_wire_first_input_time < 3000:
			throttle = 0.04
		self.publish(throttle, brake, steering)
            else:
                self.controller.reset()
            rate.sleep()

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)
    def dbw_enabled_callback(self, data):
	self.dbw_enabled = data.data

    def current_velocity_callback(self, data):
        self.current_velocity = data.twist.linear.x

    def twist_cmd_callback(self, data):
        self.linear_velocity = data.twist.linear.x
        self.angular_velocity = data.twist.angular.z

if __name__ == '__main__':
    DBWNode()
