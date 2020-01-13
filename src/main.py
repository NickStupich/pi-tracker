import is_pi
if is_pi.is_pi:
    import camera_pi as camera
else:
    import camera_files as camera


import single_point_tracking as tracking
import motor_control_l6470 as motor_control
import updates_listener
import web_ui
import image_preview    
import camera_adjuster
import dithering
import messages

if __name__ == '__main__':
    cam = camera.Camera()
    cam.start()

    tracker = tracking.SinglePointTracking()
    tracker.start()

    seconds_per_rotation = (24.*60.*60.)
    gear_ratio = 128.
    steps_per_rotation = 400.
    base_steps_per_second_ra = steps_per_rotation * gear_ratio / seconds_per_rotation  
    motor_ra = motor_control.MotorControl(bus=1, cs_pin = 0, slave_pin=26, reset_pin = 3, 
            speed_adjustment_msg = messages.CMD_SET_SPEED_ADJUSTMENT_RA,
            base_steps_per_second = base_steps_per_second_ra,
            default_speed = 1)    
    motor_ra.start()

    preview = image_preview.ImagePreview()

    adjuster = camera_adjuster.CameraAdjuster()
    adjuster.start()

    seconds_per_rotation = (24.*60.*60.)
    gear_ratio = (99 + 1044./ 2057.) * 27 * 84 / 52.
    steps_per_rotation = 200.
    base_steps_per_second_dec = steps_per_rotation * gear_ratio / seconds_per_rotation 
    motor_dec = motor_control.MotorControl(bus=0, cs_pin = 0, slave_pin=25, reset_pin = 3, 
            speed_adjustment_msg = messages.CMD_SET_SPEED_ADJUSTMENT_DEC,
            base_steps_per_second = base_steps_per_second_dec,
            default_speed = 0)    
    motor_dec.start()

    ditherer = dithering.Ditherer()
    ditherer.start()

    web_ui.run()
