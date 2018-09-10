#!/usr/bin/env python
import urllib.request
import datetime
import gzip
import json


def parse_dt(item, end=False):
    d = datetime.datetime.strptime(item['DATESTAMP'], '%d-%b-%y').date()
    s = ['TIME_FROM', 'TIME_TO'][end]
    t = datetime.datetime.strptime(item[s], '%I:%M %p').time()
    return datetime.datetime.combine(d, t).strftime('%Y%m%dT%H%M%S')


def cli():
    import argparse
    parser = argparse.ArgumentParser(description='Export timetable into .ical')
    parser.add_argument(
        '--url',
        default='http://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable',
        help='url of apu open api')
    parser.add_argument('-i', dest='intake', help='intake code', required=True)
    parser.add_argument('-o', dest='output', default='/dev/stdout',
                        help='output destination', metavar='/dev/stdout')
    return parser.parse_args()


def main(parser=None):
    with gzip.open(urllib.request.urlopen(parser.url)) as url:
        data = json.loads(url.read())
    now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

    with open(parser.output, 'w', newline='\r\n') as f:
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

        f.write(u'END:VCALENDAR\n')


if __name__ == '__main__':
    main(cli())
