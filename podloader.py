#!/usr/bin/env python
# coding=utf8

import optparse
import daemon
import dateutil.rrule
import logging
import sys
import feedparser
import urllib
import urllib2
import time
import os

log = logging.getLogger('podloader')
debug = log.debug
info = log.info
warn = log.warn
fatal = log.fatal

p = optparse.OptionParser(usage = '%prog [options] TARGETDIR URL')
p.add_option('-F','--foreground',help="Do not daemonize",action="store_true")
p.add_option('-i','--interval',help="Wait this long before refreshing",default="1 hour")
p.add_option('-d','--debug',help="enable debugging output",action="store_true")
p.add_option('-l','--limit',help="only consider latest n entries",type="int",default=-1)
p.add_option('-L','--logfile',help="logfile",default="podloader.log")
p.add_option('-m','--umask',help="set umask at program start",type="string")

(opts, args) = p.parse_args()

if not len(args) == 2:
	p.print_usage()
	sys.exit(1)

targetdir, url = args

logging.basicConfig(level = logging.INFO if not opts.debug else logging.DEBUG,
                    filename = opts.logfile)

intervals = {
	's': 1,
	'm': 60,
	'h': 60*60,
	'd': 60*60*24,
	'w': 60*60*24*7,
}
def parse_interval(s, default_step = intervals['h']):
	debug('parsing interval string %s', s)
	parts = s.lower().strip().split()

	if len(parts) > 2:
		raise "Could not parse '%s' into meaningful interval"

	step = int(parts[0])
	step_unit = default_step

	if len(parts) > 1: step_unit = intervals[parts[1][0]]

	return step*step_unit

def main(ival):
	debug('started')
	debug('ival: %d', ival)

	while True:
		try:
			debug('downloading feed')
			data = urllib2.urlopen(url).read()
			debug('parsing feed')
			d = feedparser.parse(data)
			info('updated feed %s', d['feed']['title'])
		except urllib2.URLError, e:
			warn('error downloading feed: %s', e)

		for e in reversed(d['entries'][:opts.limit]):
			for encl in e.enclosures:
				debug('handling %s: %s', e['title'], encl['url'])

				# check if file exists
				filename = os.path.basename(encl['url'])
				filepath = os.path.join(targetdir, filename)
				if os.path.exists(filepath):
					debug('skipping, %s exists', filepath)
				else:
					info('%s: downloading %s to %s', e['title'], encl['url'], filepath)
					urllib.urlretrieve(encl['url'], filepath)
					info('finished downloading')

		debug('done, sleeping')
		time.sleep(ival)

if '__main__' == __name__:
	# parse options
	ival = parse_interval(opts.interval)

	if opts.umask:
		umask = int(opts.umask, 8)
		old_umask = os.umask(umask)
		debug('umask now %o, from %o', umask, old_umask)
	try:
		if not opts.foreground:
			with daemon.DaemonContext():
				debug('daemonized')
				main(ival)
		else:
			main(ival)
	except Exception, e:
		fatal('Exception: %s', e)
		raise
