import datetime
from typing import List

import numpy as np
import os

from main.constants import DATA_DIR
from utils import read_ir_signal_from, is_difference_negligible, visualize_signal, is_difference_meaningful


class IRRawSignal:
    def __init__(self, series):
        self._data = series
        self._start_offset = 0
        self._min_value = np.amin(self._data)
        # self.strip()

    def strip(self):
        idx = len(self._data)

        # strip from beginning
        # TODO: find the way to remove calibration of the system
        for i in range(len(self._data)):
            if self._data[i] > self._min_value:
                idx = i
                break
        self._start_offset = idx
        self._data = self._data[self._start_offset:]

        # strip from end
        for i in range(len(self._data) - 1, 0, -1):
            if self._data[i] > self._min_value:
                idx = i
                break
        self._data = self._data[:idx]


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


class Point:
    def __init__(self, idx, value):
        self.index_in_raw_sequence = idx
        self.value = value


class Peak:
    def __init__(self):
        self.points = []

    def new_point(self, idx, value):
        self.points.append(Point(idx, value))

    def max_points(self):
        if not self.points:
            return None
        with_duplicates = sorted(self.points, key=lambda x: x.value, reverse=True)

        res = []
        for i in with_duplicates:
            if i.value not in res:
                res.append(i.value)
        if len(res) == 1:
            res.append(res[0])
        return res


def is_valid_action(peaks: List[Peak], required_number_peaks=4, is_local_zero=False):
    if len(peaks) < required_number_peaks:
        # start action is usually 3 small and one big peak
        return False

    # need to collect times between peaks
    time_differences = []
    for idx in range(len(peaks) - required_number_peaks, len(peaks) - 1):
        end_first = peaks[idx].points[-1].index_in_raw_sequence
        start_second = peaks[idx + 1].points[0].index_in_raw_sequence
        time_differences.append(start_second - end_first)
    is_sequence_of_peaks = max(time_differences) < 100

    if not is_sequence_of_peaks:
        # actions are sequential peaks, need to filter out peaks that are far away
        # from actual actions
        return False

    is_bad_ending = (
            is_local_zero and
            len(peaks[-1].points) == 3 and
            peaks[-1].points[-3].value == peaks[-1].points[-2].value and
            peaks[-1].points[-2].value > peaks[-1].points[-1].value > 250 and
            peaks[-1].points[-3].value > 257
    )

    is_last_peak_ending = (
                                  len(peaks[-1].points) >= 3
                                  and
                                  (
                                      # should be the biggest or the second biggest point in the peak
                                          peaks[-1].points[-1].value == peaks[-1].max_points()[0]
                                          or
                                          peaks[-1].points[-1].value == peaks[-1].max_points()[1]
                                  )
                                  and
                                  (
                                      # there should be a difference between the first point and the middle
                                      # or the last point and the middle
                                          peaks[-1].points[-1].value > peaks[-1].max_points()[-1]
                                          # is_difference_meaningful(peaks[-1].points[-1].value, peaks[-1].max_points()[-1].value, 0.1)
                                          or
                                          peaks[-1].points[0].value > peaks[-1].max_points()[-1]
                                      # is_difference_meaningful(peaks[-1].points[0].value, peaks[-1].max_points()[-1].value, 0.1)
                                  )
                                  and
                                  peaks[-1].max_points()[0] > 240
                              # and
                              # is_difference_meaningful(peaks[-1].max_points()[0].value, peaks[-2].max_points()[0].value, 0.2)
                          ) or is_bad_ending
    if not is_last_peak_ending:
        # final peak of any action has 3-point header
        return False

    negligible_diff = 0.1
    final_mark_diff = 0.02
    left_point = peaks[-1].points[-3].value
    middle_point = peaks[-1].points[-2].value
    right_point = peaks[-1].points[-1].value

    # left_point = peaks[-1].max_points()[0].value
    # middle_point = peaks[-1].max_points()[-1].value
    # right_point = peaks[-1].max_points()[1].value

    is_almost_equal_boundary_points = is_difference_negligible(left_point, right_point, negligible_diff)
    is_different_with_boundary_points = (
            left_point >= (1 + final_mark_diff) * middle_point
            or
            right_point >= (1 + final_mark_diff) * middle_point
    )
    return (
                   is_almost_equal_boundary_points and
                   is_different_with_boundary_points
           ) or is_bad_ending


class LabeledSignal:
    def __init__(self, raw_signal: IRRawSignal, ir_frequency: int, date_record):
        self.labels = []
        self.raw_signal = raw_signal
        self.ir_frequency = ir_frequency
        self.date_record = date_record

        # order is important
        self.mapping = [
            {
                'class': RegisteredNearPedalAction,
                'sanity_lambda': lambda x, zero: is_valid_action(x, RegisteredNearPedalAction.required_peaks, zero)
            },
            {
                'class': RegisteredInFeederAction,
                'sanity_lambda': lambda x, zero: is_valid_action(x, RegisteredInFeederAction.required_peaks, zero)
            },
            {
                'class': StartAction,
                'sanity_lambda': lambda x, zero: is_valid_action(x, StartAction.required_peaks, zero)
            },
        ]

        self.label()
        self.pair()

    @staticmethod
    def from_edf(edf_file_path):
        ir_buffer, ir_frequency, date_record = read_ir_signal_from(edf_file_path)
        ir_signal = IRRawSignal(ir_buffer)
        return LabeledSignal(ir_signal, ir_frequency, date_record)

    def add_label(self, label):
        self.labels.append(label)

    def label(self):
        peak = None
        peaks = []
        for idx, point in enumerate(self.raw_signal._data):
            is_local_zero = point == self.raw_signal._min_value

            # erase peaks if there is a huge pause
            if self.labels:
                last_point_idx = self.labels[-1].time_end
                if peak:
                    last_point_idx = peak.points[-1].index_in_raw_sequence
                elif peaks:
                    last_point_idx = peaks[-1].points[-1].index_in_raw_sequence

                if idx - last_point_idx > 25 and is_local_zero:
                    peak = None
                    peaks = []
                    continue

            potential_label = self.is_action([*peaks, peak], is_local_zero) \
                if peaks and peak else None

            is_rapid_start = (
                    peak and
                    len(peak.points) == 2 and
                    is_difference_meaningful(peak.points[0].value, peak.points[1].value, 0.2) and
                    is_difference_meaningful(peak.points[1].value, point, 0.2)
            ) if 3 < idx < len(self.raw_signal._data) - 3 else False

            is_joined_peak = (
                    point > 10 and
                    not is_rapid_start and
                    self.raw_signal._data[idx - 2] != self.raw_signal._min_value and
                    self.raw_signal._data[idx - 1] != self.raw_signal._min_value and
                    self.raw_signal._data[idx + 1] != self.raw_signal._min_value and
                    self.raw_signal._data[idx + 2] != self.raw_signal._min_value and
                    (
                            is_difference_meaningful(point, self.raw_signal._data[idx - 1], 0.23) or
                            (
                                    is_difference_meaningful(point, self.raw_signal._data[idx + 1], 0.23) and
                                    point < self.raw_signal._data[idx + 1]
                            )
                    ) and
                    bool(peak) and
                    len(peak.points) > 1 and
                    is_difference_negligible(peak.max_points()[0], peak.max_points()[-1], 0.3)
                    and
                    (
                            peak.max_points()[-1] > 30
                            or
                            (
                                peak.max_points()[-1] == peak.max_points()[0]
                                and
                                peak.max_points()[-1] > 17
                                and
                                peak.points[0].index_in_raw_sequence != peak.points[-1].index_in_raw_sequence
                                and
                                len(peak.points) > 2
                            )
                    )
            ) if 3 < idx < len(self.raw_signal._data) - 3 else False

            is_plateau_before_finish = (
                    len(peak.points) > 3 and
                    is_difference_negligible(self.raw_signal._data[idx + 1], peak.points[-1].value) and
                    is_difference_negligible(peak.max_points()[0], peak.max_points()[-1], 0.1) and
                    is_difference_meaningful(point, self.raw_signal._data[idx + 1], 0.3) and
                    is_difference_meaningful(point, peak.points[-1].value, 0.3) and
                    self.raw_signal._data[idx + 3] == self.raw_signal._min_value
            ) if peak is not None else False

            is_joined_action = (
                    not is_local_zero and
                    potential_label and
                    not is_plateau_before_finish
            ) if idx < len(self.raw_signal._data) - 1 else False

            is_next_zero = self.raw_signal._data[idx + 1] == self.raw_signal._min_value
            if not is_local_zero and not is_joined_action:
                # just new point for the peak
                if is_joined_peak:
                    # close current peak
                    peaks.append(peak)

                    # start new peak
                    peak = None
                else:
                    if peak is None:
                        peak = Peak()
                    peak.new_point(idx, point)
            elif not is_local_zero and is_joined_action:
                # two peaks are joined
                # close current peak
                peaks.append(peak)
                peak = None

                # check current peaks
                potential_label = self.is_action(peaks, is_local_zero)
                if potential_label:
                    self.add_label(potential_label)
                    peaks = []

                if not is_next_zero:
                    # start new peak
                    peak = Peak()
                    peak.new_point(idx, point)
                    # peaks.append(peak)
            elif is_local_zero and peak:
                # machine become idle after a peak
                # if is_difference_meaningful(peak.max_points()[0].value, peak.max_points()[-1].value, 0.2):
                #     for point_idx in range(len(peak.points)):

                peaks.append(peak)
                peak = None

                potential_label = self.is_action(peaks, is_local_zero)
                if potential_label:
                    self.add_label(potential_label)
                    peaks = []

    def is_action(self, peaks: List[Peak], is_next_point_zero=False):
        for item in self.mapping:
            if item['sanity_lambda'](peaks, is_next_point_zero):
                max_value = 0
                start_peak_idx = len(peaks) - item['class'].required_peaks
                for peak in peaks[-item['class'].required_peaks:]:
                    for point in peak.points:
                        if point.value > max_value:
                            max_value = point.value
                return item['class'](time_begin=peaks[start_peak_idx].points[0].index_in_raw_sequence,
                                     time_end=peaks[-1].points[-1].index_in_raw_sequence,
                                     max_value=max_value,
                                     ir_frequency=self.ir_frequency,
                                     date_record=self.date_record)

    def pair(self):
        for i in range(len(self.labels)):
            current_action = self.labels[i]
            previous_action = self.labels[i - 1] if i > 0 else None
            is_previous_start_action = (
                    isinstance(previous_action, StartAction) or
                    isinstance(previous_action, PedalStartAction) or
                    isinstance(previous_action, FeederStartAction)
            )
            new_action_cls = None
            if isinstance(current_action, RegisteredNearPedalAction) and is_previous_start_action:
                new_action_cls = PedalStartAction
            elif isinstance(current_action, RegisteredInFeederAction) and is_previous_start_action:
                new_action_cls = FeederStartAction
            if new_action_cls and previous_action:
                self.labels[i - 1] = new_action_cls(time_begin=previous_action.time_begin,
                                                    time_end=previous_action.time_end,
                                                    max_value=previous_action.max,
                                                    ir_frequency=previous_action.ir_frequency,
                                                    date_record=previous_action.date_record)


if __name__ == '__main__':
    # file_name = os.path.join(DATA_DIR, 'T3', '2018.11.13', 'SN-00000043 - Track 1 - 1164 sec.edf')
    # file_name = os.path.join(DATA_DIR, 'T4', '2018.12.21', 'SN-00000042 - Track 1 - 2032 sec.edf')
    file_name = os.path.join(DATA_DIR, 'T5', '2019.02.11', 'SN-00000042 - Track 1 - 2002 sec.edf')

    labeled_signal = LabeledSignal.from_edf(file_name)

    for idx, l in enumerate(labeled_signal.labels):
        print('{}. {}'.format(idx, l))

    visualize_signal(labeled_signal.raw_signal._data, left=53779, right=53779 + 70)
