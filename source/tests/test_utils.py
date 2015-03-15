import unittest
import mock
from lib import utils

__author__ = 'My'

class UtilsTestCase(unittest.TestCase):

    def test_daemonize_pid_0_pid_0(self):
        fork_mock = mock.Mock(return_value=0)
        setsid_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock):
                utils.daemonize()
        fork_mock.assert_has_calls([mock.call(), mock.call()])
        setsid_mock.assert_called_once_with()

    def test_daemonize_pid_0_pid_1(self):
        fork_mock = mock.Mock(side_effect=[0, 1])
        setsid_mock = mock.Mock()
        exit_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock):
                with mock.patch('os._exit', exit_mock, create=True):
                    utils.daemonize()
        fork_mock.assert_has_calls([mock.call(), mock.call()])
        setsid_mock.assert_called_once_with()
        exit_mock.assert_called_once_with(0)


    def test_daemonize_pid_1(self):
        fork_mock = mock.Mock(return_value=1)
        exit_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os._exit', exit_mock, create=True):
                utils.daemonize()
        fork_mock.assert_called_once_with()
        exit_mock.assert_called_once_with(0)

    def test_daemonize_exception(self):
        fork_mock = mock.Mock(side_effect=OSError(1, "I am exception!"))
        with mock.patch('os.fork', fork_mock, create=True):
            with self.assertRaises(Exception):
                utils.daemonize()

    def test_daemonize_pid_0_exception(self):
        fork_mock = mock.Mock(side_effect=[0, OSError(1, "I am exception !")])
        setsid_mock = mock.Mock()
        with mock.patch('os.fork', fork_mock, create=True):
            with mock.patch('os.setsid', setsid_mock, create=True):
                with self.assertRaises(Exception):
                    utils.daemonize()
        setsid_mock.assert_called_once_with()

    def test_create_pidfile_example(self):
        pid = 10
        m_open = mock.mock_open()
        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('path')
        m_open.assert_called_once_with('path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def execfile_patch(self, filepath, varaibles):
        varaibles.update({
            'A': '1',
        })

    def test_load_config_from_pyfile(self):
        confid = utils.Config()

        with mock.patch('__builtin__.execfile', mock.Mock(side_effect=self.execfile_patch)):
            self.assertEqual(type(utils.load_config_from_pyfile('filepath')), type(confid))


    def test_parse_cmd_args(self):
        args = 'arguments'
        parser = mock.Mock()

        with mock.patch('lib.utils.argparse.ArgumentParser', mock.Mock(return_value=parser)):
            utils.parse_cmd_args(args)
        parser.parse_args.assert_called_once_with(args=args)

    def test_get_tube(self):
        name = 'name'
        class Queue():
            def tube(self, name):
                return name
        queue = Queue()

        with mock.patch('lib.utils.tarantool_queue.Queue', mock.Mock(return_value=queue)):
            self.assertEqual(utils.get_tube(None, None, None, name), name)

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



