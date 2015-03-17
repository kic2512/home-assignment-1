import unittest
import mock
import redirect_checker


class Config():
    WORKER_POOL_SIZE = 0
    SLEEP = 0
    CHECK_URL = 'url'
    HTTP_TIMEOUT = 0
    LOGGING = {'version': 1}
    EXIT_CODE = 100

    INPUT_QUEUE_HOST = 1
    INPUT_QUEUE_PORT = 1
    INPUT_QUEUE_SPACE = 0
    INPUT_QUEUE_TUBE = 0
    OUTPUT_QUEUE_HOST = 1
    OUTPUT_QUEUE_PORT = 1
    OUTPUT_QUEUE_SPACE = 0
    OUTPUT_QUEUE_TUBE = 0

config = Config()

class RedirectCheckerTestCase(unittest.TestCase):

    def test_main_loop_check_network_status_false(self):

        logger = mock.Mock()
        child = mock.Mock()
        sleep = mock.Mock(side_effect=KeyboardInterrupt)

        with mock.patch('redirect_checker.logger', logger, create=True):
            with mock.patch('redirect_checker.sleep', sleep, create=True):
                with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=False)):
                    with mock.patch('redirect_checker.active_children', mock.Mock(return_value=(child, child))):
                        with self.assertRaises(KeyboardInterrupt):
                            redirect_checker.main_loop(config)
        logger.critical.assert_called_once_with("Network is down. stopping workers")
        child.terminate.assert_has_calls([mock.call, mock.call])

    def test_main_loop_check_network_status_true(self):
        config.WORKER_POOL_SIZE = 1
        logger = mock.Mock()
        sleep = mock.Mock(side_effect=KeyboardInterrupt)
        spawn_workers = mock.Mock()

        with mock.patch('redirect_checker.logger', logger, create=True):
            with mock.patch('redirect_checker.sleep', sleep, create=True):
                with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with mock.patch('redirect_checker.spawn_workers', return_value=None):
                        with self.assertRaises(KeyboardInterrupt):
                            redirect_checker.main_loop(config)
        logger.info.assert_called_with(
            'Spawning ' + str(config.WORKER_POOL_SIZE) + ' workers')
        config.WORKER_POOL_SIZE = 0

    def test_main_loop_check_network_status_true_without_if(self):
        logger = mock.Mock()
        sleep = mock.Mock(side_effect=KeyboardInterrupt)

        with mock.patch('redirect_checker.logger', logger, create=True):
            with mock.patch('redirect_checker.sleep', sleep, create=True):
                with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with self.assertRaises(KeyboardInterrupt):
                        redirect_checker.main_loop(config)
        logger.info.assert_called_once_with(
            u'Run main loop. Worker pool size=' +
            str(config.WORKER_POOL_SIZE) + '. Sleep time is ' +
            str(config.SLEEP) + '.')

    def test_main_daemon_true(self):
        daemon = mock.Mock()

        with mock.patch('redirect_checker.daemonize', daemon, create=True):
            redirect_checker.main(['', '-c smth', '-d'])
        daemon.assert_any_call()

    def test_main_pidfile_true(self):
        pidfile = mock.mock_open()

        with mock.patch('redirect_checker.create_pidfile', pidfile, create=True):
            with mock.patch('redirect_checker.load_config_from_pyfile', mock.Mock(return_value=config)):
                with mock.patch('redirect_checker.main_loop', mock.Mock()):
                    self.assertEqual(redirect_checker.main(['', '-c path', '-P file']), config.EXIT_CODE)
        pidfile.assert_called_once_with(' file')

    def test_main_daemonize_false_pidfile_false(self):
        with mock.patch('redirect_checker.load_config_from_pyfile', mock.Mock(return_value=config)):
            with mock.patch('redirect_checker.main_loop', mock.Mock()):
                self.assertEqual(redirect_checker.main(['', '-c path']), config.EXIT_CODE)

















