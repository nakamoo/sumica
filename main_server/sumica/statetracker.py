from flask import current_app
import coloredlogs
import logging
import json
import time
import datetime

import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class StateTracker():
    def __init__(self):
        self.states = {}

    def track(self, commands):
        for command in commands:
            self.states[command['platform']] = command['data']

    def clear(self, platform):
        self.states[platform] = None

    def satisfied(self, platform, state):
        # state corresponds to 'data' in command

        if platform in self.states:
            return self.states[platform] == state
        else:
            logger.debug("{} not tracked".format(platform))
            return False