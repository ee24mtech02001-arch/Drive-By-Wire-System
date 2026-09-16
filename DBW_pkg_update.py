import rospy
from std_msgs.msg import Float32, Bool, String
from pymodbus.client import ModbusTcpClient as ModbusClient
import time

host = '192.168.140.5'
port = 502
client = ModbusClient(host, port)
UNIT = 0x1

# Connect to the Modbus server
client.connect()
print("Connected to Modbus server")


class DBWFeedbackPublisher:
    def __init__(self):
        print("Initializing DBWFeedbackPublisher node...")
        # Publishers for feedback topics
        self.steering_angle_pub = rospy.Publisher('/steering_angle_feedback', Float32, queue_size=10)
        self.acceleration_pub = rospy.Publisher('/acceleration_feedback', Float32, queue_size=10)
        self.brake_pub = rospy.Publisher('/brake_feedback', Float32, queue_size=10)
        self.emergency_status_pub = rospy.Publisher('/emergency_status', Bool, queue_size=10)
        self.auto_manual_status_pub = rospy.Publisher('/auto_manual_status', String, queue_size=10)

        # Subscribers to set topics
        rospy.Subscriber('/set_steering', Float32, self.update_set_steering)
        rospy.Subscriber('/set_accel', Float32, self.update_set_accel)
        rospy.Subscriber('/set_control_effort', Float32, self.update_set_control_effort)
        rospy.Subscriber('/set_brake_rate', Float32, self.update_set_brake_rate)

        # Initialize set topic values
        self.set_steering = 0.0
        self.set_accel = 0.0
        self.set_control_effort = 0.0
        self.set_brake_rate = 0.0

        # Set up the rate of publishing
        self.rate = rospy.Rate(10)  # 10 Hz

    def read_angle(self):
        read1 = client.read_holding_registers(1, 1, unit=UNIT)
        current_angle = int(read1.registers[0])  # Convert to integer
        return current_angle

    def set_steer(self, angle):
        angle = int(angle)  # Convert to integer
        if angle < 0:
            y = abs(angle)
            client.write_coils(20, True, unit=UNIT)
            client.write_registers(400, y, unit=UNIT)
        else:
            client.write_coils(20, False, unit=UNIT)
            client.write_registers(400, angle, unit=UNIT)

    def control_effort(self, value):
        value = int(value)  # Convert to integer
        client.write_registers(22, value, unit=UNIT)

    def apply_brake(self, seed):
        seed = int(seed)  # Convert to integer
        client.write_coil(3, True, unit=UNIT)
        client.write_coil(4, False, unit=UNIT)
        time.sleep(seed)
        client.write_coil(3, False, unit=UNIT)
        client.write_coil(4, False, unit=UNIT)

    def update_set_steering(self, msg):
        self.set_steering = int(msg.data)  # Convert to integer
        self.set_steer(self.set_steering)

    def update_set_accel(self, msg):
        self.set_accel = int(msg.data)  # Convert to integer
        client.write_registers(500, self.set_accel, unit=UNIT)

    def update_set_control_effort(self, msg):
        self.set_control_effort = int(msg.data)  # Convert to integer
        self.control_effort(self.set_control_effort)

    def update_set_brake_rate(self, msg):
        self.set_brake_rate = int(msg.data)  # Convert to integer
        self.apply_brake(self.set_brake_rate)

    def read_feedback_data(self):
        """Simulate or read data from hardware for feedback."""
        steering_angle = self.read_angle()  # Example: 15 degrees
        emergency_status = False  # Example: No emergency
        auto_manual_status = "Auto"  # Example: Current mode is autonomous

        return steering_angle, emergency_status, auto_manual_status

    def publish_feedback(self):
        while not rospy.is_shutdown():
            # Read feedback data
            steering_angle, emergency_status, auto_manual_status = self.read_feedback_data()

            # Publish the feedback data
            self.steering_angle_pub.publish(steering_angle)
            self.emergency_status_pub.publish(emergency_status)
            self.auto_manual_status_pub.publish(auto_manual_status)

            # Sleep to maintain the publishing rate
            self.rate.sleep()


if __name__ == '__main__':
    try:
        # Initialize the ROS node
        rospy.init_node('dbw_feedback_publisher', anonymous=True)

        # Create an instance of the DBWFeedbackPublisher
        publisher = DBWFeedbackPublisher()

        # Start publishing feedback data
        publisher.publish_feedback()
    except rospy.ROSInterruptException:
        print("Shutting down")
        pass
