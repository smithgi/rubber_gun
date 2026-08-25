import logging

logger = logging.getLogger(__name__)


class AssetMonitor:
    def __init__(self, asset_x, asset_y, buffer_size=20, approach_threshold=10):
        self.asset_x = asset_x
        self.asset_y = asset_y
        self.buffer_size = buffer_size
        self.coordinates_buffer = []
        self.approach_threshold = approach_threshold

    def add_coordinates(self, x, y):
        if len(self.coordinates_buffer) >= self.buffer_size:
            self.coordinates_buffer.pop(0)
        self.coordinates_buffer.append((x, y))
        self.check_approaching()

    def check_approaching(self):
        if len(self.coordinates_buffer) < 8:
            return

        initial_x, initial_y = self.coordinates_buffer[0]
        final_x, final_y = self.coordinates_buffer[-1]

        initial_distance = self.calculate_distance(initial_x, initial_y)
        final_distance = self.calculate_distance(final_x, final_y)

        if initial_distance - final_distance > self.approach_threshold:
            logger.info("Alert: The item is approaching the asset!")

    def calculate_distance(self, x, y):
        return ((x - self.asset_x) ** 2 + (y - self.asset_y) ** 2) ** 0.5

