FROM python:3.5

MAINTAINER AHAPX
MAINTAINER anarchy.b@gmail.com

RUN git clone https://github.com/AHAPX/smtpush.git /smtpush
RUN pip install -U pip
RUN pip install -r /smtpush/requirements.txt

VOLUME /smtpush
WORKDIR /smtpush

CMD python smtpush.py -c config.cfg

