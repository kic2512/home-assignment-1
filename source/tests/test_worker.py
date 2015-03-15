__author__ = 'kic'
import unittest
import mock
from source.lib.worker import get_redirect_history_from_task


class WorkerTestCase(unittest.TestCase):

    def test_get_redirect_history_from_task(self):
        task_mock = mock.Mock()
        timeout_mock = mock.Mock()
        get_redirect_history_from_task(task_mock, timeout_mock)
