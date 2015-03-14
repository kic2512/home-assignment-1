import unittest
import mock
from lib import utils

__author__ = 'My'

class UtilsTestCase(unittest.TestCase):

    def test_daemonize_create_daemon(self):
        fork_mock = mock.Mock(return_value=0)
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', mock.Mock()):
                utils.daemonize()
                fork_mock.assert_has_calls([mock.call(), mock.call()])

    def test_daemonize_cant_fork_twice(self):
        fork_mock = mock.Mock(side_effect=[0, 1])
        exit_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', mock.Mock()):
                with mock.patch('os._exit', exit_mock, create=True):
                    utils.daemonize()
        exit_mock.assert_called_once_with(0)

    def test_daemonize_cant_fork_any_times(self):
        fork_mock = mock.Mock(return_value=1)
        exit_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os._exit', exit_mock, create=True):
                utils.daemonize()
        exit_mock.assert_called_once_with(0)

    def test_daemonize_fork_except_first_time(self):
        fork_mock = mock.Mock(side_effect=OSError(1, "I am exception !"))
        fork_mock.side_effect = OSError(1, "I am exception !")
        with mock.patch('os.fork', fork_mock, create=True):
            with self.assertRaises(Exception):
                utils.daemonize()

    def test_daemonize_fork_except_second_time(self):
        fork_mock = mock.Mock(side_effect=[0, OSError(1, "I am exception !")])
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', mock.Mock()):
                with self.assertRaises(Exception):
                    utils.daemonize()

    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('path')

        m_open.assert_called_once_with('path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    # TODO load_config_from_pyfile

    def test_parse_cmd_args(self):
        parser = mock.Mock()
        parser.parse_args.return_value = True

        with mock.patch('lib.utils.argparse.ArgumentParser', mock.Mock(return_value=parser)):
            utils.parse_cmd_args('arguments')

        parser.parse_args.assert_called_once_with(args='arguments')

    def test_get_tube(self):
        class Queue():
            def tube(self, name):
                return name
        queue = Queue()

        with mock.patch('lib.utils.tarantool_queue.Queue', mock.Mock(return_value=queue)):
            self.assertEqual(utils.get_tube(None, None, None, 'name'), 'name')

    def test_spawn_workers(self):
        process = mock.Mock()
        process.start.return_value = None

        with mock.patch('lib.utils.Process', mock.Mock(return_value=process)):
            utils.spawn_workers(1, None, None, None)

        process.start.assert_called_once_with()

    def test_check_network_status_true(self):
        with mock.patch('lib.utils.urllib2.urlopen', mock.Mock()):
            self.assertEqual(utils.check_network_status(None, None), True)

    def test_check_network_status_false(self):

        with mock.patch('lib.utils.urllib2.urlopen', mock.Mock(side_effect=Exception)):
            with self.assertRaises(Exception):
                self.assertEqual(utils.check_network_status(None, None), False)
        # TODO Exit after exception. Return false unusable.



