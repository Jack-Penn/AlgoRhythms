import time

class Stopwatch():
    def __enter__(self):
        self.start_time = time.perf_counter_ns()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter_ns()
        if exc_type:
            print(f"An exception occurred: {exc_val}")
    def get_time_ns(self):
        return self.end_time-self.start_time
    def get_time_ms(self):
        return self.get_time_ns() / 1_000_000
    def get_time(self):
        return self.get_time_ns() / 1_000_000_000