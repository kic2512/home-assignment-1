import unittest
import mock
import lib

__author__ = 'My'

FAKE_URL = 'url'
ERROR = 'ERROR'
EXIT_CODE = 100
TIMEOUT = 3


class InitTestCase(unittest.TestCase):

    def test_to_unicode_not_unicode(self):
        result = lib.to_unicode('string')
        assert result == 'string'
        assert isinstance(result, unicode)

    def test_to_unicode_unicode(self):
        result = lib.to_unicode(u'string')
        assert result == 'string'
        assert isinstance(result, unicode)

    def test_to_str_unicode(self):
        result = lib.to_str('string')
        assert result == 'string'
        assert isinstance(result, str)

    def test_to_str_not_unicode(self):
        result = lib.to_str(u'string')
        assert result == 'string'
        assert isinstance(result, str)


    def test_get_counters(self):
        content = ("google-analytics.com/ga.js"
                   "mc.yandex.ru/metrika/watch.js"
                   "top-fwz1.mail.ru/counter"
                   "top.mail.ru/jump?from")

        self.assertEqual(lib.get_counters(content),
                         ['GOOGLE_ANALYTICS', 'YA_METRICA', 'TOP_MAIL_RU', 'TOP_MAIL_RU'])

    def test_get_counters_not_if(self):
        self.assertEqual(lib.get_counters(''), [])


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

    def test_fix_market_url_without_market(self):
        self.assertEqual(lib.fix_market_url('index.html'),
                         'http://play.google.com/store/apps/index.html')

    def test_fix_market_url_market(self):
        self.assertEqual(lib.fix_market_url('market://index.html'),
                         'http://play.google.com/store/apps/index.html')

    def test_make_pycurl_request(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = FAKE_URL

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, TIMEOUT, 'user_agent'), ('', FAKE_URL))

        curl.setopt.assert_any_call(curl.USERAGENT, 'user_agent')
        curl.setopt.assert_any_call(curl.TIMEOUT, TIMEOUT)
        curl.getinfo.assert_called_with(curl.REDIRECT_URL)

    def test_make_pycurl_request_without_user_agent(self):
        curl = mock.Mock()
        curl.getinfo.return_value = FAKE_URL

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, TIMEOUT), ('', FAKE_URL))

        curl.getinfo.assert_called_with(curl.REDIRECT_URL)

    def test_make_pycurl_request_redirect_url_is_none(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = None

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, TIMEOUT, 'user_agent'), ('', None))

        curl.setopt.assert_any_call(curl.USERAGENT, 'user_agent')
        curl.setopt.assert_any_call(curl.TIMEOUT, TIMEOUT)
        curl.getinfo.assert_called_with(curl.REDIRECT_URL)

    def test_make_pycurl_request_without_if(self):
        curl = mock.Mock()
        curl.setopt.return_value = None
        curl.getinfo.return_value = None

        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl)):
            self.assertEqual(lib.make_pycurl_request(None, TIMEOUT), ('', None))

        curl.setopt.assert_any_call(curl.TIMEOUT, TIMEOUT)
        curl.getinfo.assert_called_with(curl.REDIRECT_URL)

    def test_get_url_exception(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            self.assertEqual(lib.get_url(FAKE_URL, TIMEOUT), (FAKE_URL, ERROR, None))

    def test_get_url_new_redirect_url_ok_redirect_true(self):
        url = 'http://odnoklassniki.ru/st.redirect'
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(FAKE_URL, url))):
            self.assertEqual(lib.get_url(None, TIMEOUT), (None, None, FAKE_URL))

    def test_get_url_new_redirect_url_true(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(FAKE_URL, 'other_url'))):
            self.assertEqual(lib.get_url(None, TIMEOUT), ('other_url', 'http_status', FAKE_URL))

    def test_get_url_new_redirect_url_true_urlsplit_true(self):
        url = 'market://localhost/index.html'
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(None, url))):
            self.assertEqual(lib.get_url(None, TIMEOUT),
                             (u'http://play.google.com/store/apps/localhost/index.html', 'http_status', None))

    def test_get_url_new_redirect_url_false(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=('other_url', None))):
            with mock.patch('lib.check_for_meta', mock.Mock(return_value=FAKE_URL)):
                self.assertEqual(lib.get_url(None, TIMEOUT), (FAKE_URL, 'meta_tag', 'other_url'))

    def test_get_url_new_redirect_url_false_and_false(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=('other_url', None))):
            with mock.patch('lib.check_for_meta', mock.Mock(return_value=None)):
                self.assertEqual(lib.get_url(None, TIMEOUT), (None, None, 'other_url'))

    def test_get_url_new_redirect_url_false_then_true(self):
        url = 'http://localhost/index.html'
        with mock.patch('lib.make_pycurl_request', mock.Mock(return_value=(FAKE_URL, url))):
            self.assertEqual(lib.get_url(None, TIMEOUT),
                             (url, 'http_status', FAKE_URL))

    def test_get_redirect_history_re_match_true(self):
        url = 'http://odnoklassniki.ru/'
        self.assertEqual(lib.get_redirect_history(url, None),
                         ([], [url], []))

    def test_get_redirect_history_not_redirect_url(self):
        with mock.patch('lib.get_url', mock.Mock(return_value=(None, None, None))):
            self.assertEqual(lib.get_redirect_history(FAKE_URL, None),
                             ([], [FAKE_URL], []))

    def test_get_redirect_history_redirect_type_error(self):
        with mock.patch('lib.get_url', mock.Mock(return_value=(FAKE_URL, ERROR, 'google-analytics.com/ga.js'))):
            self.assertEqual(lib.get_redirect_history(FAKE_URL, None),
                             ([ERROR], [FAKE_URL, FAKE_URL], ['GOOGLE_ANALYTICS']))

    def test_get_redirect_history(self):
        with mock.patch('lib.get_url', mock.Mock(return_value=(FAKE_URL, None, None))):
            self.assertEqual(lib.get_redirect_history(FAKE_URL, None),
                             ([None], [FAKE_URL, FAKE_URL], []))

    def test_prepare_url_is_none(self):
        self.assertEqual(lib.prepare_url(None), None)

    def test_prepare_url_not_none(self):
        with mock.patch('lib.urlunparse', mock.Mock(return_value=EXIT_CODE)):
            self.assertEqual(lib.prepare_url(FAKE_URL), EXIT_CODE)

    def test_prepare_url_exception(self):
        with mock.patch("lib.urlparse", mock.Mock(return_value=(None, u'.', None, None, None, None))):
            with mock.patch("lib.quote", mock.Mock()):
                with mock.patch("lib.quote_plus", mock.Mock()):
                    with mock.patch("lib.urlunparse", mock.Mock(return_value=EXIT_CODE)):
                        self.assertEqual(lib.prepare_url(''), EXIT_CODE)

























