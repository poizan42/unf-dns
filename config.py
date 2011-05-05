def find(f, seq):
	for item in seq:
		if f(item): 
			return item

class ConfigFile:
	def __init__(self, options, records):
		self.options = options
		self.records = records
	
	def __repr__(self):
		return "ConfigFile(options="+repr(self.options)+\
		       ", records="+repr(self.records)+")"

class ConfigSection:
	def __init__(self, name, id=None, options=None, values=None):
		self.name = name
		self.id = id
		if options == None:
			self.options = {}
		else:
			self.options = options
		if values == None:
			self.values = []
		else:
			self.values = values

	def __repr__(self):
		return "ConfigSection(name="+repr(self.name)+\
		       ", id="+repr(self.id)+\
		       ", options="+repr(self.options)+\
		       ", values="+repr(self.values)+")"

class RecordSection:
	def __init__(self, name, types, text=None, ip=None, ip6=None, options=None, values=None):
		self.name = name
		self.types = types
		self.text = text
		self.ip = ip
		self.ip6 = ip6
		if options == None:
			self.options = {}
		else:
			self.options = options
		if values == None:
			self.values = []
		else:
			self.values = values

	def __repr__(self):
		return "RecordSection(name="+repr(self.name)+\
		       ", types="+repr(self.types)+\
		       ", text="+repr(self.text)+\
		       ", ip="+repr(self.ip)+\
		       ", ip6="+repr(self.ip6)+\
		       ", options="+repr(self.options)+\
		       ", values="+repr(self.values)+")"

def parse_config(f):
	id = 0
	sections = []
	section = ConfigSection(None, 0)
	while True:
		line = f.readline()
		eof = line == ""
		line = line.strip()
		is_section = line != "" and line[0] == "[" and line[-1] == "]"
		if eof or is_section:
			sections.append(section)
		if eof:
			break
		if line == "" or line[0] == "#":
			continue
		if is_section:
			id += 1
			section = ConfigSection(line[1:-1], id)
			continue
		if line.find("=") != -1:
			(key,val) = line.split("=", 1)
			section.options[key] = val
		else:
			section.values.extend(line.split())
	return sections


def expand_value(value,ipidx,sections,servers,lists,exp_sections,path):
	if len(value) < 2 or value[0] != '@':
		return value
	name = value[1:]
	section = find(lambda s: s.name == value, sections)
	if not section:
		raise Exception("Unknown reference: "+value)
	expand_section(section,sections,servers,lists,exp_sections,path)
	return servers[name][ipidx]
	

def expand_section(section,sections,servers,lists,exp_sections,path):
	if exp_sections.has_key(section.id):
		return exp_sections[section.id]
	if section.id in path:
		raise Exception("Recursive declaration!")
	path = path.copy()
	path.add(section.id)
	if section.name == None:
		exp_sections[section.id] = None
		return None
	if section.name[0:1] == '@' and section.name[1:2] != '@':
		name = section.name[1:]
		ip = section.options.get('ip')
		ip6 = section.options.get('ip6')
		if ip:
			ip = expand_value(ip, 0, sections,servers,lists,exp_sections,path)
		else:
			ip = None
		if ip6:
			ip6 = expand_value(ip6, 1, sections,servers,lists,exp_sections,path)
		else:
			ip6 = None
		servers[name] = (ip,ip6)
		exp_sections[section.id] = None
		return None
	elif section.name[0:2] == '@@':
		name = section.name[2:]
		is_list = True
		values = []
	else:
		is_list = False
		(typestr,text) = section.name.split(':', 1)
		types = [t.strip() for t in typestr.split('+')]
		text = text.strip()
		ip = None
		ip6 = None
		if len(text) >= 2 and text[0:1] == '@':
			ip = expand_value(text,0,sections,servers,lists,exp_sections,path)
			ip6 = expand_value(text,1,sections,servers,lists,exp_sections,path)
		new_section = RecordSection(section.name, types, text, ip, ip6, \
		                            section.options)
		values = new_section.values
	for v in section.values:
		if v[0:2] == '@@':
			n = v[2:]
			section = find(lambda s: s.name == v, sections)
			if not section:
				raise Exception("Unknown reference: "+v)
			values.extend(lists[n])
		else:
			values.append(v)
	if is_list:
		lists[name] = values
		exp_sections[section.id] = None
	else:
		exp_sections[section.id] = new_section
	return exp_sections[section.id]

def expand_sections(c):
	servers = {}
	lists = {}
	exp_sections = {}
	record_sections = []
	for section in c:
		s = expand_section(section,c,servers,lists,exp_sections,set())
		if s != None:
			record_sections.append(s)
	return record_sections

def load_config(f):
	sections = parse_config(f)
	records = expand_sections(sections)
	options_section = find(lambda s: s.name == None, sections)
	if options_section == None:
		options = []
	else:
		options = options_section.options
	return ConfigFile(options, records)
