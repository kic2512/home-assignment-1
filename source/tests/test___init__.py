import unittest
from urlparse import ParseResult
import mock
import lib

__author__ = 'My'

url = 'url'
error = 'ERROR'
EXIT_CODE = 100


class InitTestCase(unittest.TestCase):

    def test_get_counters(self):
        temp_buffer = lib.COUNTER_TYPES
        lib.COUNTER_TYPES = ((None, 'pattern'), (None, 'pattern'))

        with mock.patch('lib.re.match', mock.Mock(return_value=True)):
            self.assertEqual(lib.get_counters(None), [None, None])
        lib.COUNTER_TYPES = temp_buffer


    # def test_check_for_meta(self):
    #     # value = mock.Mock()
    #     # value.lawer.return_value = 'refresh'
    #
    #     result = mock.Mock(return_value=None)
    #     result.attrs.return_value = {'content': None}
    #     # result.attrs.items.return_value = [('http_equiv', value)]
    #
    #     soup = mock.Mock()
    #     soup.find = result
    #
    #     with mock.patch('lib.BeautifulSoup', mock.Mock(return_value=soup)):
    #         lib.check_for_meta(None, None)

    def test_make_pycurl_request(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = url

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, None, 'user_agent'), ('', url))

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

    def test_get_url_new_redirect_url_false(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, None))):
            with mock.patch('lib.check_for_meta', mock.Mock(return_value=url)):
                self.assertEqual(lib.get_url(None, None, None), (url, 'meta_tag', None))

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

    # TODO prepare_url encode exception

























