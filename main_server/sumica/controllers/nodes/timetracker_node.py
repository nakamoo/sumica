import time

from flask import current_app
import numpy as np
import coloredlogs
import logging

from .node import Node
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def predictions2segments(predictions, cam_segments, times):
    segments = []

    for start_cam, end_cam in cam_segments:
        current = None
        start = None

        seq = predictions[start_cam:end_cam]
        for i, p in enumerate(seq):
            if current != p or i == len(seq) - 1:
                if current is not None:
                    segments.append([
                        times[start_cam + start],
                        times[start_cam + i],
                        current
                    ])
                start = i

            current = p

    return np.array(segments)

class TimetrackerNode(Node):
    param_file = "timetracker-parameters.html"

    def __init__(self, man, args):
        super().__init__(args)

        self.min_time = float(args["minTime"])
        self.max_time = float(args["maxTime"])
        self.activities = args["inputs"]
        self.username = man.username

    def forward(self, values):
        al = cm.cons[self.username]["activitylearner"]
        preds = np.array(al.predictions)

        if preds is not None:
            start_time = time.time() - 3600 * 24
            times = np.array(al.misc["times"])
            mask = times >= start_time
            segs = predictions2segments(preds[mask], al.misc["cam_segments"], times[mask])
            total_hours = 0

            #logger.debug("timetracker activities: {}".format(self.activities))

            for act in self.activities:
                mask = segs[:, 2] == al.classes.index(act)
                hours = np.sum(segs[mask, 1] - segs[mask, 0]) / 3600

                #logger.debug("{}: {} hours".format(act, hours))

                total_hours += hours

            #logger.debug("{} {} {}".format(self.min_time, self.max_time, total_hours))
            return [total_hours < self.min_time, total_hours > self.max_time]

        return [False, False]