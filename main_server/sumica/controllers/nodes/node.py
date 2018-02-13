
class Node:
    param_file = ""
    testable = False
    askable = False
    check_state = False
    input_types = []
    output_types = []
    display_name = None
    id = None

    # '<p style="font-size: 3em; position: absolute; color: #fff; z-index: 1">OR</p>'
    # '<i style="font-size:3em; position: absolute; color: #fff; z-index: 1" class="' + platform.icon + '"></i>'
    icon = ""

    @staticmethod
    def icon_text(text, size="2em"):
        return '<b style="font-size: {0}; position: absolute; color: #fff; z-index: 1">{1}</b>'.format(size, text)

    @staticmethod
    def icon_pic(icon_class, size="3em"):
        return '<i style="font-size:{0}; position: absolute; color: #fff; z-index: 1" class="{1}"></i>'.format(size, icon_class)

    def __init__(self, id, args):
        self.id = id
        self.args = args
        self.inputs = []
        self.outputs = []

    def forward(self, values):
        return []

    def on_event(self, event, data):
        pass