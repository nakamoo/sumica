from flask import current_app
import time
from datetime import datetime

import coloredlogs
import logging
import numpy as np

from .controller import Controller
from controllers import activitylearner
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


class TimeTracker(Controller):
    def __init__(self, username):
        super().__init__(username)

        self.segments = None
        self.cmds = []

    def get_summary_text(self):
        al = cm.cons[self.username]["activitylearner"]

        if al.classes is None or self.segments is None:
            return None

        send = "今日は"

        for i, name in enumerate(al.classes):
            mask = self.segments[:, 2] == i
            total_time = int(np.sum(self.segments[mask, 1] - self.segments[mask, 0]) / 60)
            logger.debug("{}: {} hours".format(al.classes[i], total_time / 60))

            send += "{}を{}時間".format(al.classes[i], int(total_time / 60))

        send += "やりました"

        return send

    def on_event(self, event, data):
        if event == "activity":
            al = cm.cons[self.username]["activitylearner"]
            preds = np.array(al.predictions)

            if preds is not None:
                start_time = time.time() - 3600 * 24
                times = np.array(al.misc["times"])
                mask = times >= start_time
                segs = predictions2segments(preds[mask], al.misc["cam_segments"], times[mask])

                self.segments = segs
        elif event == "speech" and data["type"] == "speech":
            msg = data["text"]

            if "まとめ" in msg:
                summary = self.get_summary_text()

                if summary is not None:
                    self.cmds = [{"platform": "tts", "data": summary}]

    def execute(self):
        cmds = self.cmds
        self.cmds = []
        return cmds