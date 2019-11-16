
# import camera_pi as camera
import camera_files as camera
import single_point_tracking as tracking
import motor_control_l6470 as motor_control
import updates_listener
import web_ui
    



if __name__ == '__main__':
    cam = camera.Camera()
    cam.start()

    tracker = tracking.SinglePointTracking()
    tracker.start()

    motor = motor_control.MotorControl()
    motor.start()

    web_ui.run()
