class ActionCode:
    """
    +1 - pedal event
    -1 - feeder event
    0 - no event
    """
    pedal = 1
    feeder = -1


class ActionDescriptor:
    start_index = None
    stop_index = None
    action: ActionCode = None

    def __init__(self, start_index, stop_index, action):
        self.start_index = start_index
        self.stop_index = stop_index
        self.action = action

    def __str__(self):
        mapping = {
            ActionCode.pedal: 'pedal',
            ActionCode.feeder: 'feeder'
        }
        return f'ActionDescriptor: ({self.start_index}, {self.stop_index}), action type: {mapping[self.action]}'


class ECGDescriptor:
    def __init__(self, intervals, ms_times):
        self.intervals = intervals
        self.ms_times = ms_times
