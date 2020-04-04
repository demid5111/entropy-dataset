import datetime


class Action:
    required_peaks = None

    def __init__(self, name, time_begin, time_end, max_value, ir_frequency, date_record):
        self.name = name
        self.time_begin = time_begin
        self.time_end = time_end
        self.max = max_value
        self.ir_frequency = ir_frequency
        self.date_record = date_record

    def __eq__(self, other: 'Action'):
        return (
                self.time_begin == other.time_begin and
                self.time_end == other.time_end and
                self.max == other.max and
                self.ir_frequency == other.ir_frequency
        )

    def same_type_same_start_time(self, other: 'Action'):
        return (
                self.time_begin == other.time_begin and
                self.__class__ == other.__class__
        )

    def __str__(self):
        time_template = '{start}(index: {index}, seconds: {seconds})'

        start_seconds = self.time_begin / self.ir_frequency
        time_begin = self.date_record + datetime.timedelta(seconds=start_seconds)
        start = time_template.format(start=time_begin.strftime('%H:%M:%S:%f'),
                                     index=self.time_begin,
                                     seconds=start_seconds
                                     )

        if self.time_end:
            end_seconds = self.time_end / self.ir_frequency
            time_end = self.date_record + datetime.timedelta(seconds=end_seconds)
            end = time_template.format(start=time_end.strftime('%H:%M:%S:%f'),
                                       index=self.time_end,
                                       seconds=end_seconds)
            return '{name} {begin} - {end}, peak value: {peak}'.format(
                name=self.name,
                begin=start,
                begin_idx=self.time_begin,
                end=end,
                end_idx=self.time_end,
                peak=self.max)
        return '{name} {begin}'.format(
            name=self.name,
            begin=start)


class RegisteredInFeederAction(Action):
    required_peaks = 5

    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)


class RegisteredNearPedalAction(Action):
    required_peaks = 6

    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)


class StartAction(Action):
    required_peaks = 4

    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)


class FeederStartAction(Action):
    required_peaks = 4

    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)


class PedalStartAction(Action):
    required_peaks = 4

    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)


class MachineJustSwitchedOnAction(Action):
    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)


class MachineJustBeforeSwitchedOffAction(Action):
    def __init__(self, time_begin, time_end, max_value, ir_frequency, date_record):
        super().__init__(self.__class__.__name__, time_begin, time_end, max_value, ir_frequency, date_record)

