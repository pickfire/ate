#!/usr/bin/env node
const fs = require('fs')
const http = require('http')
const zlib = require('zlib')

const url = 'http://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable'
const output = '/dev/stdout'
const intake = 'UCMP1808'

function icalDate (date) {
  let out = ''
  out += date.getFullYear()
  out += ('0' + (date.getMonth() + 1)).slice(-2)
  out += ('0' + date.getDate()).slice(-2)
  out += 'T'
  out += ('0' + date.getHours()).slice(-2)
  out += ('0' + date.getMinutes()).slice(-2)
  out += ('0' + date.getSeconds()).slice(-2)
  return out
}

function parseTime (date, time) {
  const [clock, meridiem] = time.split(' ')
  const [hours, minutes] = clock.split(':')
  date.setHours(+hours + (meridiem === 'PM' ? 12 : 0))
  date.setMinutes(+minutes)
  return date
}

function ical (data) {
  let out = ''
  out += 'BEGIN:VCALENDAR\r\n'
  out += 'VERSION:2.0\r\n'
  out += `PRODID:-//${intake} timetable////\r\n`

  const now = new Date()

  for (const item of data) {
    if (item.INTAKE === intake) {
      const date = new Date(item.DATESTAMP_ISO)
      out += 'BEGIN:VEVENT\r\n'
      out += `UID:${icalDate(parseTime(date, item['TIME_FROM']))}-intake-timetable\r\n`
      out += `LOCATION:${item.ROOM}\r\n`
      out += `SUMMARY:${item.MODID}\r\n`
      out += `DTSTAMP:${icalDate(now)}\r\n`
      out += `DTSTART:${icalDate(parseTime(date, item['TIME_FROM']))}\r\n`
      out += `DTEND:${icalDate(parseTime(date, item['TIME_TO']))}\r\n`
      out += 'END:VEVENT\r\n'
    }
  }

  out += 'END:VCALENDAR\r\n'
  return out
}

function write (fileName, data) {
  let fd
  try {
    fd = fs.openSync(fileName, 'w')
    fs.writeSync(fd, data, undefined, 'utf-8')
  } finally {
    if (fd !== undefined) {
      fs.closeSync(fd)
    }
  }
}

http.get(url, (res) => {
  const { statusCode } = res
  const contentType = res.headers['content-type']

  let error
  if (statusCode !== 200) {
    error = new Error('Request Failed.\n' +
                      `Status Code: ${statusCode}`)
  } else if (!/^application\/json/.test(contentType)) {
    error = new Error('Invalid content-type.\n' +
                      `Expected application/json but received ${contentType}`)
  }
  if (error) {
    console.error(error.message)
    // consume response data to free up memory
    res.resume()
    return
  }

  let gunzip = zlib.createGunzip()
  res.pipe(gunzip)

  let buffer = []
  gunzip.setEncoding('utf8')
    .on('data', (chunk) => buffer.push(chunk))
    .on('end', () => {
      try {
        const parsedData = JSON.parse(buffer.join(''))
        write(output, ical(parsedData))
      } catch (e) {
        console.error(e.message)
      }
    })
    .on('error', (e) => {
      console.error(`Got error: ${e.message}`)
    })
}).on('error', (e) => {
  console.error(`Got error: ${e.message}`)
})
