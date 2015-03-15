import unittest
import mock
import tarantool
from notification_pusher import create_pidfile, daemonize, install_signal_handlers, load_config_from_pyfile, \
    parse_cmd_args, main_loop, stop_handler, done_with_processed_tasks, notification_worker
from mock import call
from test_redirect_checker import Config
from gevent import queue as gevent_queue
import requests

config = Config
config.WORKER_POOL_SIZE = 1
config.QUEUE_HOST = 1
config.QUEUE_PORT = 1
config.QUEUE_SPACE = 1
config.QUEUE_TUBE = 1
config.QUEUE_TAKE_TIMEOUT = 1
config.HTTP_CONNECTION_TIMEOUT = 1
config.SLEEP = 0


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_daemonize_create_daemon(self):
        fork_mock = mock.Mock()
        setsid_mock = mock.Mock()
        fork_mock.return_value = 0
        setsid_mock.return_value = 0
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock, create=True):
                daemonize()
                calls = [call(), call()]
                fork_mock.assert_has_calls(calls)

    def test_daemonize_cant_fork_twice(self):
        fork_mock = mock.Mock()
        fork_mock.side_effect = [0, 1]

        exit_mock = mock.Mock()
        setsid_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock, create=True):
                with mock.patch('os._exit', exit_mock, create=True):
                    daemonize()
                    self.assertEqual(True, exit_mock.called)

    def test_daemonize_cant_fork_any_times(self):
        fork_mock = mock.Mock()
        fork_mock.return_value = 1
        exit_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os._exit', exit_mock, create=True):
                daemonize()
                self.assertEqual(True, exit_mock.called)

    def test_daemonize_fork_except_first_time(self):
        fork_mock = mock.Mock()
        fork_mock.side_effect = OSError(1, "I am exception !")
        with mock.patch('os.fork', fork_mock, create=True):
            self.assertRaises(Exception)

    def test_daemonize_fork_except_second_time(self):
        fork_mock = mock.Mock()
        fork_mock.side_effect = [0, OSError(1, "I am exception !")]
        setsid_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock, create=True):
                self.assertRaises(Exception, lambda: daemonize())

    def test_install_signal_handlers(self):
        gevent_mock = mock.Mock()
        gevent_mock.signal.return_value = None
        with mock.patch('gevent.signal', gevent_mock, create=True):
            install_signal_handlers()
            self.assertEqual(4, gevent_mock.call_count)

    def test_parse_cmd_args(self):
        argparse_mock = mock.Mock()
        with mock.patch('notification_pusher.argparse.ArgumentParser', argparse_mock, create=True):
            parse_cmd_args(None)
            self.assertEqual(True, argparse_mock.called)

    def test_main_loop_run_app(self):
        logger_mock = mock.Mock()
        tarantool_queue_mock = mock.Mock()
        tube_mock = mock.Mock()
        gevent_queue_mock = mock.Mock()
        greenlet_mock = mock.Mock()
        sleep_mock = mock.Mock()
        done_with_processed_tasks_mock = mock.Mock()

        tube_mock.take.return_value = True
        sleep_mock.side_effect = KeyboardInterrupt
        gevent_queue_mock.Queue.return_value = 1

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.tarantool_queue', tarantool_queue_mock, create=True):
                with mock.patch('notification_pusher.gevent_queue', gevent_queue_mock, create=True):
                    with mock.patch('notification_pusher.tube', tube_mock, create=True):
                        with mock.patch('notification_pusher.Greenlet', greenlet_mock, create=True):
                            with mock.patch('notification_pusher.done_with_processed_tasks',
                                            done_with_processed_tasks_mock, create=True):
                                with mock.patch('notification_pusher.sleep', sleep_mock, create=True):
                                    with self.assertRaises(KeyboardInterrupt):
                                        main_loop(config)

    def test_main_loop_not_run_app(self):
        logger_mock = mock.Mock()
        tarantool_queue_mock = mock.Mock()
        tube_mock = mock.Mock()
        gevent_queue_mock = mock.Mock()

        tube_mock.take.return_value = True
        gevent_queue_mock.Queue.return_value = 1

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.tarantool_queue', tarantool_queue_mock, create=True):
                with mock.patch('notification_pusher.gevent_queue', gevent_queue_mock, create=True):
                    with mock.patch('notification_pusher.tube', tube_mock, create=True):
                        with mock.patch('notification_pusher.run_application', False, create=True):
                            main_loop(config)
                            logger_mock.info.assert_called_with('Stop application loop.')

    def test_stop_handler(self):
        signum = 42
        logger_mock = mock.Mock()
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            stop_handler(signum)
            logger_mock.info.assert_called_with('Got signal #{signum}.'.format(signum=signum))

    def test_done_with_processed_tasks_success(self):
        logger_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        getattr_mock = mock.Mock()

        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.return_value = [mock.Mock(), mock.Mock()]
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.task_queue', task_queue_mock, create=True):
                with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                    done_with_processed_tasks(task_queue_mock)
                    self.assertEqual(1, getattr_mock.call_count)

    def test_done_with_processed_tasks_tarantool_exc(self):
        logger_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        getattr_mock = mock.Mock()

        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.return_value = [mock.Mock(), mock.Mock()]
        getattr_mock.side_effect = tarantool.DatabaseError

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.task_queue', task_queue_mock, create=True):
                with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                    done_with_processed_tasks(task_queue_mock)
                    self.assertEqual(True, logger_mock.exception.called)

    def test_done_with_processed_tasks_queue_exc(self):
        logger_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        gevent_queue_mock = mock.Mock()
        getattr_mock = mock.Mock()

        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.side_effect = gevent_queue.Empty

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.task_queue', task_queue_mock, create=True):
                with mock.patch('notification_pusher.break', gevent_queue_mock, create=True):
                    with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                        done_with_processed_tasks(task_queue_mock)
                        self.assertEqual(False, getattr_mock.called)  # TODO check if break

    def test_load_config_from_pyfile_is_upper(self):
        variables_mock = mock.Mock()
        execfile_mock = mock.Mock()
        setattr_mock = mock.Mock()
        variables_mock.iteritems.return_value = {'first': 1, 'SECOND': 2}.iteritems()
        with mock.patch('notification_pusher.execfile', execfile_mock, create=True):
            with mock.patch('notification_pusher.setattr', setattr_mock, create=True):
                with mock.patch('notification_pusher.variables', variables_mock, create=True):
                    load_config_from_pyfile('')
                    self.assertEqual(True, setattr_mock.called)
                    # TODO ASK ABOUT VARIABLES = {}

    def test_notification_worker_all_right(self):
        logger_mock = mock.Mock()
        task_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        json_mock = mock.Mock()
        requests_mock = mock.Mock()

        task_mock.data.copy.return_value = {'id': 1, 'callback_url': 2}
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.json', json_mock, create=True):
                with mock.patch('notification_pusher.requests', requests_mock, create=True):
                    notification_worker(task_mock, task_queue_mock)
                    self.assertEqual(0, logger_mock.exception.call_count)

    def test_notification_worker_request_exc(self):
        logger_mock = mock.Mock()
        task_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        json_mock = mock.Mock()
        requests_mock = mock.Mock(side_effect=requests.RequestException)
        requests_mock.post.side_effect = requests.RequestException

        task_mock.data.copy.return_value = {'id': 1, 'callback_url': 2}
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.json', json_mock, create=True):
                with mock.patch('notification_pusher.requests', requests_mock, create=True):
                    self.assertRaises(requests.RequestException, lambda : notification_worker(task_mock, task_queue_mock))