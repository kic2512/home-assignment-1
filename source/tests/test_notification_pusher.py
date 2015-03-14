import unittest
import mock
from notification_pusher import create_pidfile, daemonize
from mock import call


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
                    assert exit_mock.called

    def test_daemonize_cant_fork_any_times(self):
        fork_mock = mock.Mock()
        fork_mock.return_value = 1
        exit_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os._exit', exit_mock, create=True):
                daemonize()
                assert exit_mock.called

    def test_daemonize_fork_except_first_time(self):
        fork_mock = mock.Mock()
        fork_mock.side_effect = OSError(1, "I am exception !")
        with mock.patch('os.fork', fork_mock, create=True):
            self.assertRaises(Exception, lambda: daemonize())

    def test_daemonize_fork_except_second_time(self):
        fork_mock = mock.Mock()
        fork_mock.side_effect = [0, OSError(1, "I am exception !")]
        setsid_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock, create=True):
                self.assertRaises(Exception, lambda: daemonize())