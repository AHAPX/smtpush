from unittest import TestCase
from unittest.mock import MagicMock, patch
import logging

import trafaret

from smtpush import validate, redis_receiver, sendmail


class TestSMTPush(TestCase):

    def test_validate_errors(self):
        with self.assertRaises(trafaret.DataError):
            validate({})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@m.com'], 'body': 'b'})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@m.com'], 'subj': 's'})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@g'], 'body': 'b', 'subj': 's'})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@g.com'], 'body': 'b', 'subj': 's', 'from': 'f'})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@g.com'], 'body': 'b', 'subj': 's', 'cc': 'c@g.com'})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@g.com'], 'body': 'b', 'subj': 's', 'bcc': 'c@g.com'})
        with self.assertRaises(trafaret.DataError):
            validate({'to': ['t@g.com'], 'body': 'b', 'subj': 's', 'html': True})

    def test_validate_success(self):
        # short
        data = {'to': ['t@g.com'], 'body': 'b', 'subj': 's'}
        self.assertEqual(validate(data), data)
        # full
        data = {
            'to': ['t@g.com'],
            'body': 'b', 
            'subj': 's',
            'from': 'f@g.com',
            'cc': ['c@g.com'],
            'bcc': ['b@g.com'],
            'html': '<h1>h</h1>',
        }
        res = {
            'to': ['t@g.com'],
            'body': 'b', 
            'subj': 's',
            'sender': 'f@g.com',
            'cc': ['c@g.com'],
            'bcc': ['b@g.com'],
            'html': '<h1>h</h1>',
        }
        self.assertEqual(validate(data), res)

    def test_redis_receiver(self):
        with self.assertLogs('smtpush', logging.ERROR) as cm:
            list(redis_receiver('{"to": "t@g.com"}', None))
            self.assertIn('DataError', cm.output[0])
        with self.assertLogs('smtpush', logging.ERROR) as cm:
            list(redis_receiver('nojson', None))
            self.assertIn('is not valid json', cm.output[0])
        with self.assertLogs('smtpush', logging.INFO) as cm:
            sendmail.return_value = yield None
            data = '{"to": ["t@g.com"], "body": "b", "subj": "s"}'
            list(redis_receiver(data, None))
            self.assertIn('send to', cm.output[0])

    @patch('smtpush.SMTP')
    def test_sendmail_1(self, mock):
        config = {
            'host': 'localhost',
            'port': 25,
            'username': 'user',
            'password': 'pass',
        }
        smtp = MagicMock()
        mock.return_value = smtp
        list(sendmail(['a@g.com'], 'subj', 'body', config=config))
        smtp.ehlo.assert_called_once_with()
        self.assertFalse(smtp.starttls.called)
        smtp.login.assert_called_once_with(user=config['username'], password=config['password'])
        smtp.sendmail.assert_called_once()
        smtp.close.assert_called_once_with()

    @patch('smtpush.SMTP')
    def test_sendmail_2(self, mock):
        config = {
            'host': 'localhost',
            'port': 25,
            'username': 'user',
            'password': 'pass',
            'tls': True,
        }
        smtp = MagicMock()
        mock.return_value = smtp
        list(sendmail(['a@g.com'], 'subj', 'body', 'html', 's@g.com', ['b@g.com'], config=config))
        smtp.ehlo.assert_called_once_with()
        smtp.starttls.assert_called_once_with()
        smtp.login.assert_called_once_with(user=config['username'], password=config['password'])
        smtp.sendmail.assert_called_once()
        smtp.close.assert_called_once_with()
