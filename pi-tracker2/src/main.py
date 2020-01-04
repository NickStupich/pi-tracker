
import camera_pi as camera
# import camera_files as camera


import single_point_tracking as tracking
import motor_control_l6470 as motor_control
import motor_control_pwm as motor_control_axis_2
import updates_listener
import web_ui
import image_preview    
import camera_adjuster
import dithering

if __name__ == '__main__':
    cam = camera.Camera()
    cam.start()

    tracker = tracking.SinglePointTracking()
    tracker.start()

    motor = motor_control.MotorControl()
    motor.start()

    preview = image_preview.ImagePreview()

    adjuster = camera_adjuster.CameraAdjuster()
    adjuster.start()

    motor_2 = motor_control_axis_2.MotorControl()
    motor_2.start()

    ditherer = dithering.Ditherer()
    ditherer.start()

    web_ui.run()
