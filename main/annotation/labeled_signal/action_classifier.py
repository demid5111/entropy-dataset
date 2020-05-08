from typing import List

from main.annotation.labeled_signal.peak import Peak
from main.annotation.labeled_signal.utils import is_difference_negligible


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
                                          or
                                          peaks[-1].points[0].value > peaks[-1].max_points()[-1]
                                  )
                                  and
                                  peaks[-1].max_points()[0] > 240
                          ) or is_bad_ending
    if not is_last_peak_ending:
        # final peak of any action has 3-point header
        return False

    negligible_diff = 0.1
    final_mark_diff = 0.02
    left_point = peaks[-1].points[-3].value
    middle_point = peaks[-1].points[-2].value
    right_point = peaks[-1].points[-1].value

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
