#!/usr/bin/env python
# coding=utf8

import optparse
import daemon
import dateutil.rrule
import logging

log = logging.getLogger('podloader')
debug = log.debug
info = log.info

p = optparse.OptionParser()
p.add_option('-F','--foreground',help="Do not daemonize",action="store_true")
p.add_option('-i','--interval',help="Wait this long before refreshing",default="1 hour")
p.add_option('-d','--debug',help="enable debugging output",action="store_true")

(opts, args) = p.parse_args()

logging.basicConfig(level = logging.INFO if not opts.debug else logging.DEBUG)

intervals = {
	's': dateutil.rrule.SECONDLY,
	'm': dateutil.rrule.MINUTELY,
	'h': dateutil.rrule.HOURLY,
	'd': dateutil.rrule.DAILY,
	'w': dateutil.rrule.WEEKLY,
	'o': dateutil.rrule.MONTHLY,
	'y': dateutil.rrule.YEARLY
}
def parse_interval(s, default_step = dateutil.rrule.MINUTELY):
	debug('parsing interval string %s', s)
	parts = s.lower().strip().split()

	if len(parts) > 2:
		raise "Could not parse '%s' into meaningful interval"

	step = int(parts[0])
	step_unit = default_step

	if len(parts) > 1:
		p = parts[1]

		if p.startswith('month'): p = 'o'
		step_unit = intervals[p[0]]

	rv = dateutil.rrule.rrule(step_unit, interval = step)
	if opts.debug:
		i = rv.__iter__()
		debug('next steps in rrule: %s %s %s', i.next(), i.next(), i.next())
	return rv

def main(ival):
	debug('started')

if '__main__' == __name__:
	# parse options
	ival = parse_interval(opts.interval)
	if not opts.foreground:
		with daemon.DaemonContext():
			debug('daemonized')
			main(ival)
	else:
		main(ival)
