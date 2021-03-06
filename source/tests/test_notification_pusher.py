# coding: utf-8

import unittest
import mock
import tarantool
from notification_pusher import create_pidfile, daemonize, install_signal_handlers, load_config_from_pyfile, \
    parse_cmd_args, main_loop, stop_handler, done_with_processed_tasks, notification_worker, main
from mock import call
from test_redirect_checker import Config
from gevent import queue as gevent_queue
from requests.exceptions import RequestException
import notification_pusher

config = Config
config.WORKER_POOL_SIZE = 1
config.QUEUE_HOST = 1
config.QUEUE_PORT = 1
config.QUEUE_SPACE = 1
config.QUEUE_TUBE = 1
config.QUEUE_TAKE_TIMEOUT = 1
config.HTTP_CONNECTION_TIMEOUT = 1
config.SLEEP = 0
config.SLEEP_ON_FAIL = 0
config.LOGGING = {
    'first': 1,
    'second': 2,
    'version': 1
}


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
                    self.assertTrue(exit_mock.called)

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
            self.assertRaises(OSError, lambda: daemonize())

    def test_daemonize_fork_except_second_time(self):
        fork_mock = mock.Mock()
        fork_mock.side_effect = [0, OSError(1, "I am exception !")]
        setsid_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock, create=True):
                self.assertRaises(OSError, lambda: daemonize())

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
        tarantool_queue_mock = mock.Mock()
        tube_mock = mock.Mock()
        greenlet_mock = mock.Mock()
        worker_mock = mock.Mock()

        tube_mock.take.return_value = True
        worker_mock.start.side_effect = KeyboardInterrupt
        greenlet_mock.return_value = worker_mock

        with mock.patch('notification_pusher.tarantool_queue', tarantool_queue_mock, create=True):
            with mock.patch('notification_pusher.tube', tube_mock, create=True):
                with mock.patch('notification_pusher.Greenlet', greenlet_mock, create=True):
                    self.assertRaises(KeyboardInterrupt, lambda: main_loop(config))

    def test_main_loop_run_app_no_free_workers(self):
        tarantool_queue_mock = mock.Mock()
        tube_mock = mock.Mock()
        pool_mock = mock.Mock()
        worker_pool_mock = mock.Mock()
        done_mock = mock.Mock()

        worker_pool_mock.free_count.return_value = 0
        pool_mock.return_value = worker_pool_mock
        tube_mock.take.return_value = True

        with mock.patch('notification_pusher.tarantool_queue', tarantool_queue_mock, create=True):
            with mock.patch('notification_pusher.tube', tube_mock, create=True):
                with mock.patch('notification_pusher.Pool', pool_mock, create=True):
                    with mock.patch('notification_pusher.done_with_processed_tasks', done_mock, create=True):
                        with mock.patch('notification_pusher.run_application', side_effect=[True, False], create=True):
                            main_loop(config)
                            self.assertFalse(worker_pool_mock.start.called)

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
                        with mock.patch('notification_pusher.run_application', side_effect=[False], create=True):
                            main_loop(config)
                            logger_mock.info.assert_called_with('Stop application loop.')  # Единственный метод в ветке

    def test_stop_handler(self):
        signum = 42
        logger_mock = mock.Mock()
        offset = notification_pusher.SIGNAL_EXIT_CODE_OFFSET
        expected_code = offset + signum
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            exit_code = stop_handler(signum)
            self.assertEqual(expected_code, exit_code)

    def test_done_with_processed_tasks_success(self):
        logger_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        getattr_mock = mock.Mock()
        action_name_mock = mock.Mock()
        task_mock = mock.Mock()

        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.return_value = [task_mock, action_name_mock]
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.task_queue', task_queue_mock, create=True):
                with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                    done_with_processed_tasks(task_queue_mock)
                    getattr_mock.assert_called_once_with(task_mock, action_name_mock)

    def test_done_with_processed_tasks_tarantool_exc(self):
        task_queue_mock = mock.Mock()
        getattr_mock = mock.Mock()
        log_mock = mock.Mock()

        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.return_value = [mock.Mock(), mock.Mock()]
        getattr_mock.side_effect = tarantool.DatabaseError

        with mock.patch('notification_pusher.task_queue', task_queue_mock, create=True):
            with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                    with mock.patch('notification_pusher.logger', log_mock, create=True):
                        self.assertRaises(tarantool.DatabaseError, lambda: done_with_processed_tasks(task_queue_mock))

    def test_done_with_processed_tasks_queue_exc(self):
        logger_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        gevent_queue_mock = mock.Mock()
        getattr_mock = mock.Mock()

        task_queue_mock.qsize.return_value = 0
        task_queue_mock.get_nowait.side_effect = gevent_queue.Empty

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.task_queue', task_queue_mock, create=True):
                with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                    done_with_processed_tasks(task_queue_mock)
                    self.assertEqual(False, getattr_mock.called)

    def execfile_patch(self, filepath, variables):
        variables.update({
            'first': 1,
            'SECOND': 2,
        })

    def test_load_config_from_pyfile_is_upper(self):
        exec_mock = mock.Mock(side_effect=self.execfile_patch)
        with mock.patch('__builtin__.execfile', exec_mock, create=True):
            cfg = load_config_from_pyfile('path')
            self.assertTrue(hasattr(cfg, 'SECOND'))
            self.assertFalse(hasattr(cfg, 'first'))

    def test_notification_worker_all_right(self):
        logger_mock = mock.Mock()
        task_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        json_mock = mock.Mock()
        requests_mock = mock.Mock()

        url = 'http://empty.com'

        task_mock.data.copy.return_value = {'id': 1, 'callback_url': url}
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.json', json_mock, create=True):
                with mock.patch('notification_pusher.requests', requests_mock, create=True):
                    notification_worker(task_mock, task_queue_mock)
                    task_queue_mock.put.assert_called_once_with((task_mock, 'ack'))
                    requests_mock.post.assert_called_once_with(url, data=json_mock.dumps())

    def test_notification_worker_request_exc(self):
        logger_mock = mock.Mock()
        task_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        json_mock = mock.Mock()
        requests_mock = mock.Mock(side_effect=RequestException)
        requests_mock.post.side_effect = RequestException

        url = 'http://empty.com'

        task_mock.data.copy.return_value = {'id': 1, 'callback_url': url}
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.json', json_mock, create=True):
                with mock.patch('notification_pusher.requests', requests_mock, create=True):
                    notification_worker(task_mock, task_queue_mock)
                    task_queue_mock.put.assert_called_once_with((task_mock, 'bury'))

    def test_main_all_right(self):
        load_config_from_pyfile_mock = mock.Mock()
        main_loop_mock = mock.Mock(side_effect=KeyboardInterrupt)
        dictConfig_mock = mock.Mock()

        argv = ['empty', '-c', 'path']

        with mock.patch('notification_pusher.load_config_from_pyfile', load_config_from_pyfile_mock, create=True):
            with mock.patch('notification_pusher.main_loop', main_loop_mock, create=True):
                with mock.patch('notification_pusher.dictConfig', dictConfig_mock, create=True):
                    with self.assertRaises(KeyboardInterrupt):
                        main(argv)

    def test_main_except_daemon(self):
        parse_cmd_args_mock = mock.Mock()
        load_cfg_mock = mock.Mock(side_effect=KeyboardInterrupt)

        daemonize_mock = mock.Mock()

        argv = ['empty', '-c', 'path', '-d']
        parse_cmd_args_mock.return_value = mock.Mock()
        load_cfg_mock.return_value = config

        with mock.patch('notification_pusher.daemonize', daemonize_mock, create=True):
            with mock.patch('notification_pusher.load_config_from_pyfile', load_cfg_mock, create=True):
                with self.assertRaises(KeyboardInterrupt):
                    main(argv)
                    daemonize_mock.assert_called_once_with()

    def test_main_except_pid(self):
        parse_cmd_args_mock = mock.Mock()
        load_cfg_mock = mock.Mock(side_effect=KeyboardInterrupt)
        create_pid_mock = mock.Mock()

        argv = ['empty', '-c', 'path', '--pid', '42']
        parse_cmd_args_mock.return_value = mock.Mock()
        load_cfg_mock.return_value = config

        with mock.patch('notification_pusher.load_config_from_pyfile', load_cfg_mock, create=True):
            with mock.patch('notification_pusher.create_pidfile', create_pid_mock, create=True):
                with self.assertRaises(KeyboardInterrupt):
                    main(argv)
                    create_pid_mock.assert_called_once_with(42)

    def test_main_not_run_app(self):
        parse_cmd_args_mock = mock.Mock()
        logger_mock = mock.Mock()

        argv = ['empty', '-c', 'path']
        parse_cmd_args_mock.return_value = mock.Mock()
        notification_pusher.run_application = False

        with mock.patch('notification_pusher.load_config_from_pyfile', mock.Mock(),
                        create=True):
            with mock.patch('notification_pusher.os', mock.Mock(), create=True):
                with mock.patch('notification_pusher.dictConfig', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.logger', logger_mock, create=True):
                        main(argv)
                        logger_mock.info.assert_called_with('Stop application loop in main.')