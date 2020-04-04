from typing import List

from main.signal.action_classifier import is_valid_action
from main.signal.ir_raw_signal import IRRawSignal, read_ir_signal_from
from main.signal.actions import RegisteredNearPedalAction, RegisteredInFeederAction, StartAction, PedalStartAction, \
    FeederStartAction
from main.signal.peak import Peak
from main.signal.utils import is_difference_meaningful, is_difference_negligible


class LabeledSignal:
    def __init__(self, raw_signal: IRRawSignal):
        self.labels = []
        self.raw_signal = raw_signal
        self.ir_frequency = raw_signal._ir_frequency
        self.date_record = raw_signal._date_record

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
        return LabeledSignal(IRRawSignal.from_edf(edf_file_path))

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
            ) if peak is not None and idx < len(self.raw_signal._data) - 1 else False

            is_joined_action = (
                    not is_local_zero and
                    potential_label and
                    not is_plateau_before_finish
            ) if idx < len(self.raw_signal._data) - 1 else False

            is_next_zero = self.raw_signal._data[idx + 1] == self.raw_signal._min_value \
                if idx < len(self.raw_signal._data) - 1 else False
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

    def keep_only_pairs(self):
        final_labels = []
        i = 0
        while i < len(self.labels):
            if i == len(self.labels) - 1:
                break
            current_action = self.labels[i]
            next_action = self.labels[i + 1]

            if not self._is_pair_of_matching_events(current_action, next_action):
                i += 1
                continue
            final_labels.extend([current_action, next_action])
            i += 2
        self.labels = final_labels

    def check_only_pairs_are_left(self):
        for i in range(0, len(self.labels), 2):
            if not self._is_pair_of_matching_events(self.labels[i], self.labels[i + 1]):
                raise ValueError('not matching pair of consecutive events {} and {}'.format(i, i + 1))

    @staticmethod
    def _is_pair_of_matching_events(first, second):
        first_class = first.__class__
        second_class = second.__class__
        matching_rule = {
            PedalStartAction: RegisteredNearPedalAction,
            FeederStartAction: RegisteredInFeederAction
        }
        try:
            return matching_rule[first_class] == second_class
        except KeyError:
            return False
