__author__ = 'kic'
import unittest
import mock
from source.lib.worker import get_redirect_history_from_task


class Test(object):
    def __init__(self, checker='empty'):
        self.data = {
            'url': 'empty',
            'url_id': 1,
            'recheck': checker,
            'suspicious': 'empty'
        }
        self.task_id = 1


class WorkerTestCase(unittest.TestCase):

    def test_get_redirect_history_from_task_input_true(self):
        to_unicode_mock = mock.Mock()
        logger_mock = mock.Mock()

        test = Test()

        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                is_input, data = get_redirect_history_from_task(test, 10)
                self.assertEqual(False, is_input)

    def test_get_redirect_history_from_task_input_false(self):
        to_unicode_mock = mock.Mock()
        logger_mock = mock.Mock()

        test = Test(None)

        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                is_input, data = get_redirect_history_from_task(test, 10)
                self.assertEqual(True, is_input)