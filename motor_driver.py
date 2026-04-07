#!/usr/bin/python3
import time

# -------------------------------------------------------
# Try to import RPi.GPIO (only available on Raspberry Pi)
# Fall back to a stub so the code runs on PC without errors
# -------------------------------------------------------
try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    _GPIO_AVAILABLE = False
    print("[motor_driver] RPi.GPIO not available – running in STUB mode (PC)")

    class _GPIOStub:
        BCM = OUT = HIGH = LOW = 0
        def setmode(self, *a): pass
        def setwarnings(self, *a): pass
        def setup(self, *a, **kw): pass
        def output(self, *a): pass
        def cleanup(self): pass

    GPIO = _GPIOStub()

# GPIO pin mapping
IN1 = 24 #14  # Left motor forward
IN2 = 25 #15  # Left motor backward
IN3 = 18  # Right motor forward
IN4 = 23  # Right motor backward

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT, initial=GPIO.LOW)

class MotorDriver:

    def forward(self):
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        print("Motors: FORWARD")

    def backward(self):
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        print("Motors: BACKWARD")

    def left(self):
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        print("Motors: LEFT TURN")

    def right(self):
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        print("Motors: RIGHT TURN")

    def stop(self):
        GPIO.output([IN1, IN2, IN3, IN4], GPIO.LOW)
        print("Motors: STOP")

    # Convenience wrapper for brain orders
    def set(self, speed, steering):
        """
        speed: 0=stop, 1=forward, -1=back
        steering: 0=center, <0=left, >0=right
        """
        if speed == 0:
            self.stop()
        elif speed > 0:
            if steering == 0:
                self.forward()
            elif steering < 0:
                self.left()
            else:
                self.right()
        else:
            if steering == 0:
                self.backward()
            elif steering < 0:
                self.left()
            else:
                self.right()


