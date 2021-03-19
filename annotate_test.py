import unittest
import os

import pandas as pd

from main.constants import TEST_REFERENCE_DIR, TEST_DIR, ARTIFACTS_DIR
from main.annotation.labeled_signal.actions import StartAction, FeederStartAction, RegisteredInFeederAction, \
    PedalStartAction, \
    RegisteredNearPedalAction
from main.annotation.labeled_signal.labeled_signal import LabeledSignal


class NotIdenticalActionsError(Exception):
    pass


class CustomAssertions:
    def assertActionsMatch(self, labeled_signal, expected_labels, fail_early=None):
        not_identical_actions = []
        for idx, label in enumerate(labeled_signal.labels):
            if idx >= len(expected_labels):
                not_identical_actions.append([label, None])
            elif not expected_labels[idx].same_type_same_start_time(label):
                not_identical_actions.append([label, expected_labels[idx]])
                if fail_early is not None and len(not_identical_actions) == fail_early:
                    break

        if not_identical_actions:
            error_messages = []
            for actual, expected in not_identical_actions:
                error_messages.append('Expected: {expected}, actual: {actual}'.format(expected=expected, actual=actual))

            if len(expected_labels) != len(labeled_signal.labels):
                error_messages.append(
                    'Expected {} actions, got {}'.format(len(expected_labels), len(labeled_signal.labels)))
            error_messages.append('{} actions were recognized incorrectly'.format(len(not_identical_actions)))
            error_message = '\n'.join(['', *error_messages])

            raise NotIdenticalActionsError(error_message)


class ReferenceReporter:
    @staticmethod
    def report_excel(actual_labels, expected_labels):
        action_map = {
            StartAction: 'unstart',
            FeederStartAction: 'fstart',
            RegisteredInFeederAction: 'fend',
            PedalStartAction: 'pstart',
            RegisteredNearPedalAction: 'pend',
        }

        data_frame_sources = []
        for actual, expected in zip(actual_labels, expected_labels):
            actual_time = actual.time_begin / 100
            actual_type = action_map[actual.__class__]
            reference_time = expected.time_begin / 100
            reference_type = action_map[expected.__class__]

            data_frame_sources.append([
                reference_time,
                reference_type,
                actual_time,
                actual_type,
                reference_time - actual_time,
                int(reference_type != actual_type)
            ])

        columns = [
            'reference time',
            'reference label',
            'predicted time',
            'predicted label',
            'reference time - actual time',
            'do labels differ?'
        ]
        df = pd.DataFrame(data_frame_sources, columns=columns)

        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        writer = pd.ExcelWriter(os.path.join(ARTIFACTS_DIR, 'output.xlsx'), engine='xlsxwriter')

        df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1, header=False)

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        for idx, column_name in enumerate(['A', 'B', 'C', 'D', 'E', 'F']):
            worksheet.write(0, idx, columns[idx], header_format)

        writer.save()


class ReaderSingleEDFFileTest(unittest.TestCase, CustomAssertions):
    ir_frequency = 100

    def read_expected_labels(self, path, date_record):
        df = pd.read_excel(path, header=None)
        actions = []
        action_map = {
            'unstart': StartAction,
            'unend': StartAction,
            'fstart': FeederStartAction,
            'fend': RegisteredInFeederAction,
            'pstart': PedalStartAction,
            'pend': RegisteredNearPedalAction,
        }
        for index, row in df.iterrows():
            start_time = round(row[0] * (10 ** 2))
            action_type = row[1]
            cls = action_map[action_type]
            actions.append(cls(start_time, None, None, self.ir_frequency, date_record))
        return actions

    # @unittest.skip("temp skip as it works")
    def test_single_file_1(self):
        file_name = os.path.join(TEST_REFERENCE_DIR, 'T3', '2018.11.13', 'SN-00000043 - Track 1 - 1164 sec.edf')
        labeled_signal = LabeledSignal.from_edf(file_name)
        ref_name = os.path.join(TEST_DIR, 'T3', '2018.11.13', 'SN-00000043 - Track 1 - 1164 sec.xlsx')
        expected_labels = self.read_expected_labels(ref_name, labeled_signal.date_record)

        ReferenceReporter.report_excel(labeled_signal.labels, expected_labels)

        self.assertActionsMatch(labeled_signal, expected_labels)

    # @unittest.skip("temp skip as it works")
    def test_single_file_2(self):
        file_name = os.path.join(TEST_REFERENCE_DIR, 'T4', '2018.12.21', 'SN-00000042 - Track 1 - 2032 sec.edf')
        labeled_signal = LabeledSignal.from_edf(file_name)
        ref_name = os.path.join(TEST_DIR, 'T4', '2018.12.21', 'SN-00000042 - Track 1 - 2032 sec.xlsx')
        expected_labels = self.read_expected_labels(ref_name, labeled_signal.date_record)

        ReferenceReporter.report_excel(labeled_signal.labels, expected_labels)

        self.assertActionsMatch(labeled_signal, expected_labels, fail_early=None)

    # @unittest.skip("temp skip as it does not work")
    def test_single_file_3(self):
        file_name = os.path.join(TEST_REFERENCE_DIR, 'T5', '2019.02.11', 'SN-00000042 - Track 1 - 2002 sec.edf')
        labeled_signal = LabeledSignal.from_edf(file_name)
        ref_name = os.path.join(TEST_DIR, 'T5', '2019.02.11', 'SN-00000042 - Track 1 - 2002 sec.xlsx')
        expected_labels = self.read_expected_labels(ref_name, labeled_signal.date_record)

        ReferenceReporter.report_excel(labeled_signal.labels, expected_labels)

        self.assertActionsMatch(labeled_signal, expected_labels, fail_early=None)
