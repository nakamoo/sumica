import colorsys
import json

from .node import Node

import controllermanager as cm


def data2command(data):
    h = data['color'].lstrip('#')
    r, g, b = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    cmddata = list()

    if data['on']:
        hue = {"bri": int(v * 255), "hue": int(h * 65535), "sat": int(s * 255), 'on': True}
    else:
        hue = {'on': False}

    for id in data['hue_names'].split(','):
        cmddata.append({'id': id, 'state': hue})

    cmddata = json.dumps(cmddata)
    command = {'platform': 'hue', 'data': cmddata}

    if "confirm" in data and data["confirm"] == "Always":
        confirm = data["confirm_say"]

        command['confirmation'] = confirm

    return command

class HueNode(Node):
    testable = True
    askable = True
    check_state = True
    param_file = "hue-parameters.html"
    input_types = ["boolean"]
    output_types = ["action"]
    display_name = "Hue"
    icon = Node.icon_pic("fa fa-lightbulb")

    @staticmethod
    def test_execute(args):
        cmd = data2command(args)
        cmd["manual"] = True
        return [cmd]

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.act = data2command(args)

    def forward(self, values):
        if len(values) > 0 and not (False in values):
            return [self.act]

        return []