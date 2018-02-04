import threading
import traceback

from managers.cvcamera import Manager as CameraManager
from managers.speech import Manager as SpeechManager
from managers.hue import Manager as HueManager
from actors.youtubeactor import YoutubeActor
from actors.hueactor import HueActor
from actors.generalactor import GeneralActor

speech_event = threading.Event()
# When speech_event is not set, speech_manager wait.
speech_event.set()


class ModuleManager(object):
    def __init__(self, ID, SERVER_IP):
        self.ID = ID
        self.SERVER_IP = SERVER_IP

        speech_manager = SpeechManager(ID, SERVER_IP, speech_event)
        hue_manager = HueManager(ID, SERVER_IP)
        camera_manager = CameraManager(ID, SERVER_IP)
        self.sensor_mods = [speech_manager, hue_manager, camera_manager]

        youtube_actor = YoutubeActor(self.ID, self.SERVER_IP)
        hue_actor = HueActor(self.ID, self.SERVER_IP)
        general_actor = GeneralActor(self.ID, self.SERVER_IP)
        self.actor_mods = [youtube_actor, hue_actor, general_actor]

    def start_sensor_mods(self):
        for inp in self.sensor_mods:
            thread_stream = threading.Thread(target=inp.start)
            thread_stream.daemon = False
            thread_stream.start()

    def execute_actor_mods(self, acts):
        for act in acts:
            for inp in self.actor_mods:
                try:
                    inp.execute(act)
                except:
                    traceback.print_exc()
