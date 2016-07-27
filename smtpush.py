import sys
import traceback
import json
import logging
import argparse
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formatdate
from smtplib import SMTP

import asyncio
import trafaret as tf
from subscriber import add_params, handlers


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addHandler(logging.StreamHandler())


def sendmail(to, subj, body, html=None, sender=None, cc=None, bcc=None, config={}):
    sendto = to

    msg = MIMEMultipart('alternative')

    msg.attach(MIMEText(body, 'plain'))
    if html:
        msg.attach(MIMEText(html, 'html'))

    msg['To'] = ','.join(to)
    msg['From'] = sender or config.get('from', '')
    msg['Subject'] = subj
    msg['Message-ID'] = make_msgid()
    msg['Date'] = formatdate()

    if cc is not None:
        msg['cc'] = ','.join(cc)
        sendto += cc
    if bcc is not None:
        msg['bcc'] = ','.join(bcc)
        sendto += bcc

    smtp = SMTP(host=config['host'], port=config['port'])
    smtp.ehlo()
    if config.get('tls'):
        smtp.starttls()
    smtp.login(user=config['username'], password=config['password'])
    smtp.sendmail(sender or config.get('from') or config.get('username'), sendto, msg.as_string())
    smtp.close()
    yield


validate = tf.Dict({
    tf.Key('to'): tf.List(tf.Email),
    tf.Key('subj'): tf.String,
    tf.Key('body'): tf.String,
    tf.Key('from', optional=True) >> 'sender': tf.Email,
    tf.Key('cc', optional=True): tf.List(tf.Email),
    tf.Key('bcc', optional=True): tf.List(tf.Email),
    tf.Key('html', optional=True): tf.String,
})


def redis_receiver(message, config):
    try:
        msg = validate(json.loads(message))
    except tf.DataError as exc:
        logger.error(exc)
    except ValueError:
        logger.error('"{}" is not valid json'.format(message))
    else:
        logger.info('send to {}'.format(msg['to']))
        try:
            yield from sendmail(config=config, **msg)
        except Exception as exc:
            logger.error('\n'.join(traceback.format_tb(sys.exc_info()[2])))
    yield


def run(config):
    logger.info('smtpush server started')
    asyncio.async(
        handlers.redis(
            add_params(config=config)(redis_receiver),
            host=config['rhost'],
            port=config['rport'],
            db=config['rdb'],
            channel=config['rchannel'],
        )
    )
    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple smtp server', add_help=False)
    # main args
    parser.add_argument('--help', action='help', help='show this help message and exit')
    parser.add_argument('--config', '-c', type=str, help='config file')
    parser.add_argument('--debug', '-D', help='debug mode', action='store_true')
    # smtp args
    parser.add_argument('--host', '-h', type=str, help='host')
    parser.add_argument('--port', '-p', type=int, help='port', default=25)
    parser.add_argument('--username', '-u', type=str, help='smtp username')
    parser.add_argument('--password', '-P', type=str, help='smtp password')
    parser.add_argument('--from', '-f', type=str, help='sender email')
    parser.add_argument('--tls', help='use tls', action='store_true')
    # redis args
    parser.add_argument('--rhost', type=str, help='redis host', default='localhost')
    parser.add_argument('--rport', type=int, help='redis port', default=6379)
    parser.add_argument('--rdb', type=int, help='redis db', default=0)
    parser.add_argument('--rchannel', type=str, help='redis channel', default='smtp-channel')

    args = parser.parse_args()
    settings = vars(args)
    if args.config:
        config = configparser.ConfigParser()
        config.read(args.config)
        settings['debug'] = config.getboolean('main', 'debug', fallback=settings['debug'])
        settings['host'] = config.get('smtp', 'host', fallback=settings['host'])
        settings['port'] = config.getint('smtp', 'port', fallback=settings['port'])
        settings['username'] = config.get('smtp', 'username', fallback=settings['username'])
        settings['password'] = config.get('smtp', 'password', fallback=settings['password'])
        settings['from'] = config.get('smtp', 'from', fallback=settings['from'])
        settings['tls'] = config.getboolean('smtp', 'tls', fallback=settings['tls'])
        settings['rhost'] = config.get('redis', 'host', fallback=settings['rhost'])
        settings['rport'] = config.getint('redis', 'port', fallback=settings['rport'])
        settings['rdb'] = config.getint('redis', 'db', fallback=settings['rdb'])
        settings['rchannel'] = config.get('redis', 'channel', fallback=settings['rchannel'])

    if settings['debug']:
        logger.setLevel(logging.DEBUG)

    run(settings)
