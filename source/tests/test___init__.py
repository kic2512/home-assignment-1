import unittest
from urlparse import ParseResult
import mock
import lib

__author__ = 'My'

url = 'url'
error = 'ERROR'
EXIT_CODE = 100


class InitTestCase(unittest.TestCase):

    def test_to_unicode_not_unicode(self):
            self.assertEqual(lib.to_unicode(chr(97)), 'a')

    def test_to_unicode_unicode(self):
            self.assertEqual(lib.to_unicode(unichr(97)), 'a')

    def test_to_str_unicode(self):
        self.assertEqual(lib.to_str(unichr(97)), 'a')

    def test_to_str_not_unicode(self):
        self.assertEqual(lib.to_str(chr(97)), 'a')

    def test_get_counters(self):
        temp_buffer = lib.COUNTER_TYPES
        lib.COUNTER_TYPES = ((None, 'pattern'), (None, 'pattern'))

        with mock.patch('lib.re.match', mock.Mock(return_value=True)):
            self.assertEqual(lib.get_counters(None), [None, None])
        lib.COUNTER_TYPES = temp_buffer

    def test_get_counters_not_if(self):
        temp_buffer = lib.COUNTER_TYPES
        lib.COUNTER_TYPES = ((None, 'pattern'), (None, 'pattern'))

        with mock.patch('lib.re.match', mock.Mock(return_value=False)):
            self.assertEqual(lib.get_counters(None), [])
        lib.COUNTER_TYPES = temp_buffer

    def test_check_for_meta_len_not_2(self):
        html = '<meta content="" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost'), None)

    def test_check_for_meta_all(self):
        html = '<meta content=";url=index.html" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), 'http://localhost/index.html')

    def test_check_for_meta_not_m(self):
        html = '<meta content=";" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), None)

    def test_check_for_meta_none(self):
        html = '<>'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), None)

    def test_fix_market_url(self):
        self.assertEqual(lib.fix_market_url('index.html'), 'http://play.google.com/store/apps/index.html')

    def test_make_pycurl_request(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = url

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, None, 'user_agent'), ('', url))

    def test_make_pycurl_request_without_user_agent(self):
        curl = mock.Mock()
        curl.getinfo.return_value = url

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, None, None), ('', url))

    def test_make_pycurl_request_redirect_url_is_none(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = None

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, None, 'user_agent'), ('', None))

    def test_make_pycurl_request_without_if(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = None

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, None, None), ('', None))

    def test_get_url_exception(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            self.assertEqual(lib.get_url(None, None, None), (None, 'ERROR', None))

    def test_get_url_new_redirect_url_ok_redirect_true(self):
        redirect = mock.Mock()
        redirect.match.return_value = True
        temp_buffer = lib.OK_REDIRECT
        lib.OK_REDIRECT = redirect
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, url))):
            self.assertEqual(lib.get_url(None, None, None), (None, None, None))
        lib.OK_REDIRECT = temp_buffer

    def test_get_url_new_redirect_url_true(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, url))):
            self.assertEqual(lib.get_url(None, None, None), (url, 'http_status', None))

    def test_get_url_new_redirect_url_true_urlsplit_true(self):
        request = ParseResult(scheme='market', netloc='localhost', path='path',
            params='', query='', fragment='')
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, url))):
            with mock.patch('lib.urlsplit', mock.Mock(return_value=request)):
                self.assertEqual(lib.get_url(None, None, None), (u'http://play.google.com/store/apps/url', 'http_status', None))

    def test_get_url_new_redirect_url_false(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, None))):
            with mock.patch('lib.check_for_meta', mock.Mock(return_value=url)):
                self.assertEqual(lib.get_url(None, None, None), (url, 'meta_tag', None))

    def test_get_url_new_redirect_url_false_and_false(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, None))):
            with mock.patch('lib.check_for_meta', mock.Mock(return_value=None)):
                self.assertEqual(lib.get_url(None, None, None), (None, None, None))

    def test_get_url_new_redirect_url_false_then_true(self):
        request = ParseResult(scheme='market', netloc='localhost', path='path',
            params='', query='', fragment='')
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, url))):
            with mock.patch('lib.urlsplit', mock.Mock(return_value=request)):
                self.assertEqual(lib.get_url(None, None, None),
                                 (u'http://play.google.com/store/apps/url', 'http_status', None))

    def test_get_redirect_history_re_match_true(self):
        with mock.patch('lib.re.match', mock.Mock(return_value=True)):
            self.assertEqual(lib.get_redirect_history(url, None), ([], [url], []))

    def test_get_redirect_history_not_redirect_url(self):
        with mock.patch('lib.re.match', mock.Mock(return_value=False)):
            with mock.patch('lib.get_url', mock.Mock(return_value=(None, None, None))):
                self.assertEqual(lib.get_redirect_history(url, None), ([], [url], []))

    def test_get_redirect_history_redirect_type_error(self):
        with mock.patch('lib.re.match', mock.Mock(return_value=False)):
            with mock.patch('lib.get_url', mock.Mock(return_value=(url, error, True))):
                self.assertEqual(lib.get_redirect_history(url, None), ([error], [url, url], []))

    def test_get_redirect_history(self):
        with mock.patch('lib.re.match', mock.Mock(return_value=False)):
            with mock.patch('lib.get_url', mock.Mock(return_value=(url, None, None))):
                self.assertEqual(lib.get_redirect_history(url, None), ([None], [url, url], []))

    def test_prepare_url_is_none(self):
        self.assertEqual(lib.prepare_url(None), None)

    def test_prepare_url_not_none(self):
        with mock.patch('lib.urlunparse', mock.Mock(return_value=EXIT_CODE)):
            self.assertEqual(lib.prepare_url('url'), EXIT_CODE)

    def test_prepare_url_exception(self):
        with mock.patch("lib.urlparse", mock.Mock(return_value=(None, u'.', None, None, None, None))):
            with mock.patch("lib.quote", mock.Mock()):
                with mock.patch("lib.quote_plus", mock.Mock()):
                    with mock.patch("lib.urlunparse", mock.Mock(return_value=EXIT_CODE)):
                        self.assertEqual(lib.prepare_url(''), EXIT_CODE)

























