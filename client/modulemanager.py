import threading
import traceback

from managers.camera import Manager as CameraManager
from managers.talk import Manager as TalkManager
from managers.screen import Manager as ScreenManager
from actors.hueactor import HueActor


class ModuleManager(object):
    def __init__(self, ID, SERVER_IP):
        self.ID = ID
        self.SERVER_IP = SERVER_IP

        camera_manager = CameraManager(ID, SERVER_IP)
        talk_manager = TalkManager(ID, SERVER_IP)

        self.sensor_mods = {
            "talk": talk_manager,
            "camera": camera_manager,
            "screen": ScreenManager(ID, SERVER_IP, self)
        }

        hue_actor = HueActor(self.ID, self.SERVER_IP)
        self.actor_mods = [hue_actor]

    def start_sensor_mods(self):
        for inp in self.sensor_mods.values():
            thread_stream = threading.Thread(target=inp.start)
            thread_stream.daemon = True
            thread_stream.start()

    def execute_actor_mods(self, acts):
        for inp in self.actor_mods:
            try:
                inp.execute(acts)
            except:
                traceback.print_exc()
