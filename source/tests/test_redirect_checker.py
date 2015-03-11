import unittest
import mock
import redirect_checker


class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_loop_check_network_status_false(self):
        config = mock.Mock(WORKER_POOL_SIZE=0, SLEEP=0, CHECK_URL='url', HTTP_TIMEOUT=0)
        logger = mock.Mock()
        sleep = mock.Mock(side_effect=KeyboardInterrupt)

        with mock.patch('redirect_checker.logger', logger, create=True):
            with mock.patch('redirect_checker.sleep', sleep, create=True):
                with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=False)):
                    with self.assertRaises(KeyboardInterrupt):
                        redirect_checker.main_loop(config)

        logger.critical.assert_called_once_with("Network is down. stopping workers")

    def test_main_loop_check_network_status_true(self):

        config = mock.Mock(WORKER_POOL_SIZE=1, SLEEP=0, CHECK_URL='url', HTTP_TIMEOUT=0)
        logger = mock.Mock()
        sleep = mock.Mock(side_effect=KeyboardInterrupt)

        with mock.patch('redirect_checker.logger', logger, create=True):
            with mock.patch('redirect_checker.sleep', sleep, create=True):
                with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with self.assertRaises(KeyboardInterrupt):
                        redirect_checker.main_loop(config)

        logger.info.assert_called_with("Spawning 1 workers")

    def test_main_loop_check_network_status_true_without_if(self):

        config = mock.Mock(WORKER_POOL_SIZE=0, SLEEP=0, CHECK_URL='url', HTTP_TIMEOUT=0)
        logger = mock.Mock()
        sleep = mock.Mock(side_effect=KeyboardInterrupt)

        with mock.patch('redirect_checker.logger', logger, create=True):
            with mock.patch('redirect_checker.sleep', sleep, create=True):
                with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with self.assertRaises(KeyboardInterrupt):
                        redirect_checker.main_loop(config)

    def test_main_daemon_true(self):
        daemon = mock.Mock()

        with mock.patch('redirect_checker.daemonize', daemon, create=True):
            redirect_checker.main(['', '-c smth', '-d'])

        daemon.assert_called_once_with()

    # def test_main_pidfile_true(self):
    #
    #     pidfile = mock.mock_open()
    #
    #     with mock.patch('redirect_checker.create_pidfile', pidfile, create=True):
    #         redirect_checker.main(['', '-c path', '-P file'])
    #
    #     pidfile.assert_called_once_with('True')











