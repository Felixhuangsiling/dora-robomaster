from robomaster import robot, led

class RobotController:
    def __init__(self):
        self.ep_robot = robot.Robot()
        self.ep_robot.initialize(conn_type="ap")
        self.ep_robot.led.set_led(comp=led.COMP_ALL, r=255, g=0, b=0, effect=led.EFFECT_OFF)
    def __del__(self):
        self.ep_robot.close()

rob = RobotController()
