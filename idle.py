"""Idle timing is based on interaction with Grazi, not global OS monitoring."""
import time


class IdleState:
    def __init__(self, timeout=60, clock=time.monotonic):
        self.timeout = timeout
        self.clock = clock
        self.last_activity = clock()
        self.sleeping = False

    def touch(self):
        self.last_activity = self.clock()
        self.sleeping = False

    def update(self, occupied=False):
        if occupied:
            self.touch()
        elif self.clock() - self.last_activity > self.timeout:
            self.sleeping = True
        return self.sleeping
