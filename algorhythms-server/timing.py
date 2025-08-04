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
    def get_formatted_time(self):
        nanoseconds = self.get_time_ns()
        if nanoseconds >= 1_000_000_000:
            seconds = nanoseconds / 1_000_000_000
            return f"{seconds:.3f} s"
        elif nanoseconds >= 1_000_000:
            milliseconds = nanoseconds / 1_000_000
            return f"{milliseconds:.3f} ms"
        else:
            return f"{nanoseconds} ns"