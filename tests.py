from unittest import TestCase

import trafaret

from smtpush import validate


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
