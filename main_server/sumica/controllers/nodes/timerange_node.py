import datetime

from .node import Node


class TimeRangeNode(Node):
    def __init__(self, man, args):
        super().__init__(args)

        self.start_min, self.end_min = args["startTime"], args["endTime"]
        if self.end_min < self.start_min:
            self.end_min += 60*24

    def forward(self, values):
        now = datetime.datetime.now()
        now_min = now.hour * 60 + now.minute

        if self.start_min == self.end_min:
            return [True]

        if now_min < self.start_min:
            now_min += 60*24

        return [self.start_min <= now_min < self.end_min]