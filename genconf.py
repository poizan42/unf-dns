#!/bin/env python2.4
import sys
import config
from datetime import date

if len(sys.argv) != 2:
	print "Usage: genconf.py configfile"
	sys.exit(1)

def mkemail(email):
	atpos = email.find('@')
	return email[:atpos]+'.'+email[atpos+1:]+'.'

def gencfgline(domain, type, record):
	if type == 'NS':
		return domain+" IN NS     "+record.text
	elif type == 'MX':
		return domain+" IN MX     "+record.options['preference']+" "+\
		       record.text
	elif type == 'A':
		if record.ip:
			return domain+" IN A      "+record.ip
		else:
			return "; ("+domain+") no ipv4 address for "+record.text
	elif type == 'AAAA':
		if record.ip6:
			return domain+" IN AAAA   "+record.ip6
		else:
			return "; ("+domain+") no ipv6 address for "+record.text
	elif type == 'TXT':
		return domain+" IN TXT    "+record.text

cfg = config.load_config(open(sys.argv[1], 'rb'));
o = cfg.options
serfile = open(o['serial'], 'rb')
sernum = int(serfile.read().strip())
serfile.close()
serfile = open(o['serial'], 'w')
serfile.write(str(sernum+1 % 100))
serfile.close()
serial = date.today().strftime('%Y%m%d')
serial += '%.2d' % sernum
print "$TTL    "+cfg.options['TTL']
print "@       IN      SOA     "+o['authDNS']+" "+mkemail(o['email'])+" ("
print "  "+str(serial)+"        ; Serial"
print "  "+o['refresh']+"       ; Refresh"
print "  "+o['retry']+"       ; Retry"
print "  "+o['expire']+"       ; Expire"
print "  "+o['NC-TTL']+" )     ; Negative caching TTL"
print ""
print "localhost       IN      A      127.0.0.1"
print "localhost       IN      AAAA   ::1"
print ""
#@       IN      NS      ns.lol.poizan.dk.

for r in cfg.records:
	for v in r.values:
		for t in r.types:
			if r.options.has_key('prefixes'):
				domains = []
				for p in r.options['prefixes'].split():
					p = p.strip()
					if p == '@':
						domains.append(v)
					else:
						domains.append(p+v)
			else:
				domains = [v]
			for d in domains:
				print gencfgline(d, t, r)
