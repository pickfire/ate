#!/usr/bin/env python
try:  # python 3
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen
import contextlib
import datetime
import json
import io


def parse_dt(item, end=False):
    d = datetime.datetime.strptime(item['DATESTAMP'], '%d-%b-%y').date()
    s = ['TIME_FROM', 'TIME_TO'][end]
    t = datetime.datetime.strptime(item[s], '%H:%M %p').time()
    return datetime.datetime.combine(d, t).strftime('%Y%m%dT%H%M%S')


def cli():
    import argparse
    parser = argparse.ArgumentParser(description='Export timetable into .ical')
    parser.add_argument(
        '--url',
        default='https://ws.apiit.edu.my/web-services/index.php/open/weektimetable',
        help='url of apu open api')
    parser.add_argument('-i', required=True, help='intake code', dest='intake')
    parser.add_argument('-o', default='/dev/stdout',
                        help='output', metavar='/dev/stdout', dest='output')
    return parser.parse_args()


def main(parser=None):
    with contextlib.closing(urlopen(parser.url)) as url:
        data = json.loads(url.read())
    now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

    with io.open(parser.output, 'w', newline='\r\n') as f:
        f.write(u'BEGIN:VCALENDAR\n')
        f.write(u'VERSION:2.0\n')
        f.write(u'PRODID:-//%s timetable////\n' % parser.intake)

        for item in filter(lambda i: i['INTAKE'] == parser.intake, data):
            f.write(u'BEGIN:VEVENT\n')
            f.write(u'UID:%s\n' % (parse_dt(item) + '-intake-timetable'))
            f.write(u'LOCATION:%s\n' % item['ROOM'])
            f.write(u'SUMMARY:%s\n' % item['MODID'])
            f.write(u'DTSTAMP:%s\n' % now)
            f.write(u'DTSTART:%s\n' % parse_dt(item, end=False))
            f.write(u'DTEND:%s\n' % parse_dt(item, end=True))
            f.write(u'END:VEVENT\n')

        f.write(u'END:VCALENDAR')


if __name__ == '__main__':
    main(cli())
