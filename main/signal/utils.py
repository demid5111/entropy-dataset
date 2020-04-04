import matplotlib.pyplot as plt

import numpy as np


def visualize_signal(signal, left=None, right=None):
    """
    Usage:
    visualize_signal(labeled_signal.raw_signal._data, left=53779, right=53779 + 70)
    :param signal:
    :param left:
    :param right:
    """
    np.random.seed(19680801)
    plt.subplot(211)
    plt.plot(signal)
    plt.subplot(212)
    left_border = left if left is not None else 0
    right_border = right + 1 if right is not None and right + 1 < len(signal) else len(signal)
    plt.plot(signal[left_border:right_border])
    plt.show()


def is_difference_meaningful(first_value, second_value, diff_threshold=0.1):
    max_value = max(first_value, second_value)
    min_value = min(first_value, second_value)
    return abs((max_value / min_value) - 1) > diff_threshold


def is_difference_negligible(first_value, second_value, diff_threshold=0.1):
    max_value = max(first_value, second_value)
    min_value = min(first_value, second_value)
    return abs((max_value / min_value) - 1) < diff_threshold
