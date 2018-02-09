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
    input_types = ["boolean"]
    output_types = ["boolean"]
    display_name = "Moving Average"
    icon = Node.icon_pic("fa fa-sliders-h")
    param_file = "inputsmoother-parameters.html"

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.history = []
        self.activation = tosecs(args["activation"])
        self.activated = False

        self.on_threshold = 0.5
        self.off_threshold = 0.5

        if "onThreshold" in args:
            self.on_threshold = float(args["onThreshold"])

        if "offThreshold" in args:
            self.off_threshold = float(args["offThreshold"])

    def forward(self, values):
        self.history.append([time.time(), values[0]])

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

            if float(hits / tot) >= self.on_threshold:
                self.activated = True
            elif float(hits / tot) <= self.off_threshold:
                self.activated = False

            return [self.activated]