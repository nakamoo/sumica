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

    def track(self, commands, manual=False):
        for command in commands:
            #if "confirmation" in command:
            #    pass
            #else:
            self.states[command['platform']] = command

    def clear(self, platform):
        self.states[platform] = None

    def satisfied(self, platform, state):
        # state corresponds to 'data' in command

        if platform in self.states:
            return self.states[platform] == state
        else:
            logger.debug("{} not tracked".format(platform))
            return False

    def should_change(self, new_command):
        platform = new_command["platform"]

        logger.debug("new: {}".format(new_command))

        if ("manual" in new_command and new_command["manual"]):
            return True

        if platform in self.states:
            old_command = self.states[platform]
            logger.debug("old: {}".format(old_command))
            same = old_command == new_command

            if same:
                return False
            else:
                if ("manual" in new_command and new_command["manual"]):
                    return True

                if "manual" in old_command:
                    if time.time() - old_command["manual_time"] > 60:
                        return True
                    else:
                        return False
        else:
            return True

        return False