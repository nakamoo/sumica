import datetime
import time

from .node import Node


def tosecs(act):
    tokens = act.split()
    if act == "immediate":
        return 0
    if "minute" in tokens[1]:
        return int(tokens[0]) * 60
    elif "second" in tokens[1]:
        return int(tokens[0])
    else:
        return 0

class InputSmootherNode(Node):
    def __init__(self, args):
        super().__init__(args)

        self.history = []
        self.activation = tosecs(args["activation"])

    def forward(self, values):
        self.history.append([time.time(), values[0][0]])

        if len(self.history) <= 0:
            return [False]

        if self.activation == 0:
            t, val = self.history[-1]

            return [val]
        else:
            hits = 0
            tot = 0

            for t, val in self.history[::-1]:
                if time.time() - t > self.activation:
                    break

                if val:
                    hits += 1
                tot += 1

            if tot <= 0:
                return [False]

            return [float(hits / tot) > 0.5]