__author__ = 'kic'
import unittest
import mock
# from source.lib.worker import get_redirect_history_from_task, worker
from lib.worker import *


class Test(object):
    def __init__(self, checker='empty'):
        self.data = {
            'url': 'empty',
            'url_id': 1,
            'recheck': checker,
            'suspicious': 'empty'
        }
        self.task_id = 1


class Tube(object):
    def __init__(self, inp=True):
        self.opt = {
            'tube': 'empty'
        }
        self.queue = self.Queue()
        self.b = inp

    def take(self, a):
        return self.Task()

    def put(self, a='empty', delay='empty', pri='empty'):
        return None

    class Task(object):
        def __init__(self):
            self.task_id = 1
            self.data = {
                'url': 'empty',
                'url_id': 1,
                'recheck': 'empty',
                'suspicious': 'empty'
            }

        def meta(self):
            return {'pri': 'empty'}

        def ack(self):
            return None

    class Queue(object):
        def __init__(self):
            self.host = 'empty'
            self.port = 1
            self.space = 'empty'


class Config(object):
    def __init__(self):
        self.INPUT_QUEUE_HOST = "empty"
        self.INPUT_QUEUE_PORT = 1
        self.INPUT_QUEUE_SPACE = 1
        self.INPUT_QUEUE_TUBE = Tube()
        self.OUTPUT_QUEUE_HOST = "empty"
        self.OUTPUT_QUEUE_PORT = 1
        self.OUTPUT_QUEUE_SPACE = 1
        self.OUTPUT_QUEUE_TUBE = Tube()
        self.QUEUE_TAKE_TIMEOUT = 0
        self.HTTP_TIMEOUT = 0
        self.MAX_REDIRECTS = 1
        self.USER_AGENT = 'empty'
        self.RECHECK_DELAY = 1


class WorkerTestCase(unittest.TestCase):
    def test_get_redirect_history_from_task_input_true(self):
        to_unicode_mock = mock.Mock(return_value=None)
        logger_mock = mock.Mock()
        redir_history_mock = [[], [], []]
        test = Test()

        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                with mock.patch('lib.worker.get_redirect_history', return_value=redir_history_mock):
                    is_input, data = get_redirect_history_from_task(test, 10)
                    self.assertEqual(False, is_input)

    def test_get_redirect_history_from_task_input_false(self):
        to_unicode_mock = mock.Mock()
        logger_mock = mock.Mock()
        redir_history_mock = [['ERROR'], [], []]

        test = Test(None)

        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                with mock.patch('lib.worker.get_redirect_history', return_value=redir_history_mock):
                    is_input, data = get_redirect_history_from_task(test, 10)
                    self.assertEqual(True, is_input)

    def test_worker_is_input(self):
        logger = mock.Mock()
        cnf = Config()
        cnf.QUEUE_TAKE_TIMEOUT = mock.Mock(side_effect=[True, False])

        with mock.patch('lib.worker.get_tube', return_value=Tube()):
            with mock.patch('lib.worker.get_redirect_history_from_task', return_value=[mock.Mock(), mock.Mock()]):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.logger', logger, create=True):
                        worker(cnf, 1)
                        logger.info.assert_any_call(u'Task id=1 done')

    '''def test_worker_isnt_input_and_exc(self):
        logger = mock.Mock()
        cnf = Config()
        cnf.QUEUE_TAKE_TIMEOUT = mock.Mock(side_effect=[True, False])

        with mock.patch('lib.worker.get_tube', return_value=Tube()):
            with mock.patch('lib.worker.get_redirect_history_from_task', return_value=[mock.Mock(), mock.Mock()]):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.logger', logger, create=True):
                        worker(cnf, 1)
                        logger.info.assert_any_call(u'Task id=1 done')'''