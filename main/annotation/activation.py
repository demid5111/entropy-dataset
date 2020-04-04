import numpy as np

from main.signal.actions import FeederStartAction, RegisteredInFeederAction, PedalStartAction, RegisteredNearPedalAction


class ActionsClassifier:
    """
    +1 - pedal event
    -1 - feeder event
    0 - no event
    """

    @staticmethod
    def interval(start_action, end_action):
        feeder_combination = (FeederStartAction, RegisteredInFeederAction)
        pedal_combination = (PedalStartAction, RegisteredNearPedalAction)

        is_feeder = (
                start_action.__class__ == feeder_combination[0] and
                end_action.__class__ == feeder_combination[1]
        )

        is_pedal = (
                start_action.__class__ == pedal_combination[0] and
                end_action.__class__ == pedal_combination[1]
        )

        if not is_feeder and not is_pedal:
            raise ValueError('Actions MUST be: <start, end>. Found incompatible combination')

        start_time = start_action.time_begin
        end_time = end_action.time_begin

        return start_time, end_time, 1 if is_pedal else -1

    @staticmethod
    def apply(labeled_signal):
        raw_data = np.zeros(labeled_signal.raw_signal._data.shape[0])
        for i in range(0, len(labeled_signal.labels), 2):
            start_action = labeled_signal.labels[i]
            end_action = labeled_signal.labels[i+1]
            start, end, value = ActionsClassifier.interval(start_action, end_action)
            raw_data[start:end] = np.full((end - start,), value)
        return raw_data
