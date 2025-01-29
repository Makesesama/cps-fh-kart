from gpiozero import Servo
from time import sleep
import random


class Breakdancer:
    breakServo = None
    luckyNumber = 6

    def __init__(self):
        self.breakServo = Servo(18)
        self.breakServo.min()
        sleep(1)

    def luckyStrike(self):
        rand = random.randint(1, 10)
        if self.luckyNumber == rand:
            print("pass")
            self.breakServo.max()
            sleep(1)
            self.breakServo.min()
            sleep(1)
        else:
            print("fail")
