# SMTPush

## Description
Simple async smtp sender with redis as broker.

## Requirements
- [python 3.4+](https://www.python.org/download/releases/3.4.0/)
- [redis](http://redis.io/download)

## Installation
```bash
$ git clone https://github.com/AHAPX/smtpush
$ cd smtpush
$ pip install -r requirements.txt
```

## Usage

### Run server
```bash
$ python smtpush.py -c ~/config.cfg
```

### Send mail
```
$ redis-cli
> PUBLISH smtp-channel '{"to": ["mail@host"], "subj": "test", "body": "hello"}'
```

## Config file
Config has [ini format](https://en.wikipedia.org/wiki/INI_file), i.e.

```ini
[main]
debug = false

[smtp]
host = mail.host
port = 587
username = user
passwor = password
from = info@host
tls = true

[redis]
host = localhost
port = 6379
db = 1
channel = smtp-channel
```

## Command line arguments
- config - path to [config file](#config-file)
- host - smtp host
- port - smtp port, default=25
- username - smtp username
- password - smtp password
- from - sender email
- tls - using tls
- rhost - host of redis broker, default=locahost
- rport - port of redis broker, default=6379
- rdb - number of redis db, default=0
- rchannel - redis channel for subscription, default=ws-channel
- debug - debug mode

## Testing
```bash
$ python -m unittest
```

## API
### Server
SMTPush server subscribes to channel and wait messages. Message must be valid JSON.
It should consist keys:

- to - recipients (array, required)
- subj - subject (string, required)
- body - body (string, required)
- from - sender email (email)
- cc - CC (array)
- bcc - BCC (array)
- html - body is html/text (boolean)
