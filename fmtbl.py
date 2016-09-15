#!/usr/bin/env python
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import re
import os
import sys
import copy
import operator
from fwclasses import fwProject, fwSegment, fwSegmentForProject, fwTable, fwEntry, fwField, fwUnion, fwCodedef
from guifw import GUIapp, showInfo

def isName(l):
	"""
	check if the string has the format on a legal variable
	"""
	name = re.match(r'[A-Za-z_][A-Za-z_0-9]*',l)
	try:
		n = name.group(0)
		if n==l:
			return True
		return False
	except AttributeError:
		return False

def parse_field(w):
	subunion = None
	isarray = False
	number = 1
	codedef = None
	if not isName(w.attrib['name']):
		print "ERROR: Field '%s' has an invalid name" % (w.attrib['name'])
		return None
	if not unicode(w.attrib['size']).isdecimal():
		print "ERROR: Field '%s' has an invalid size(%s)" % (w.attrib['name'],w.attrib['size'])
		return None
	if 'array_num_entries' in w.attrib.keys():
		number = w.attrib['array_num_entries']
		if not unicode(number).isdecimal():
			print "ERROR: Field '%s' has an invalid array_num_entries(%s)" % (w.attrib['name'],number)
			return None
	if 'codedef' in w.attrib.keys():
		codedef = w.attrib['codedef']
		if not isName(codedef):
			print "WARNING: Field '%s' has an invalid codedef(%s)" % (w.attrib['name'],codedef)
	if 'sub_union' in w.attrib.keys():
		subunion = w.attrib['sub_union']
		#if not isName(subunion):
		#	print "WARNING: Field '%s' has an invalid subunion(%s)" % (w.attrib['name'],subunion)
	if 'is_array' in w.attrib.keys():
		if w.attrib['is_array'].upper() == "TRUE":
			isarray = True
			s = int(w.attrib['size'])
			if s != 8 and s != 16 and s != 32:
				print "ERROR: Field '%s' is an array; its size must be 8 or 16 or 32 bits, and it is %s" % (w.attrib['name'],w.attrib['size'])
				return None
	return fwField(w.attrib['name'],w.attrib['size'],number,isarray,codedef,subunion)

def parse_segment(w):

	genptr = None
	devaddr = None
	start = "0x0"
	end = "0xffffffff"
	if not isName(w.attrib['name']):
		print "ERROR: Segment '%s' has an invalid name" % (w.attrib['name'])
		return None
	if 'start_address' in w.attrib.keys():
		start = w.attrib['start_address']
	if 'end_address' in w.attrib.keys():
		end = w.attrib['end_address']
	if 'generate_pointers' in w.attrib.keys():
		genptr = w.attrib['generate_pointers'].upper()
		if genptr != 'TRUE' and genptr != 'FALSE':
			print "WARNING: Segment '%s' , 'generate_pointers' has an incorrect value(%s). It will be considered 'FALSE'" % (w.attrib['name'],
				w.attrib['generate_pointers'])
			genptr = "FALSE"
	if 'device_address' in w.attrib.keys():
		devaddr = w.attrib['device_address']
		if not isName(devaddr):
			print "ERROR: Segment '%s' has an invalid device address %s" % (w.attrib['name'],devaddr)
			return None
	return fwSegment(w.attrib['name'],start,end,genptr,devaddr)

def parse_entry(w):
	generate = None
	used = None
	if not isName(w.attrib['name']):
		print "ERROR: Entry '%s' has an invalid name" % (w.attrib['name'])
		return None
	if 'generate_local_macros' in w.attrib.keys():
		generate = w.attrib['generate_local_macros'].upper()
		if generate != 'TRUE' and genptr != 'FALSE':
			print "WARNING: Entry '%s' , 'generate_pointers' has an incorrect value(%s). It will be considered 'FALSE'" % (w.attrib['name'],
				w.attrib['generate_local_macros'])
			generate = "FALSE"
	if 'used' in w.attrib.keys():
		used = w.attrib['used'].upper()
		if used != 'NO':
			used = 'YES'
	projects = ['DEFAULT']
	if 'project' in w.attrib.keys():
		# any alphabetic matches 1 or more times
		projects = re.findall(r"[\w]+", w.attrib['project'])
	return fwEntry(w.attrib['name'],projects,generate,used)

def parse_table(w):
	union = None
	size = None
	size2 = None
	size3 = None
	if not isName(w.attrib['name']):
		print "ERROR: Table '%s' has an invalid name" % (w.attrib['name'])
		return None
	if 'size' in w.attrib.keys():
		size = w.attrib['size']
		if not unicode(size).isdecimal():
			print "ERROR: Table '%s' has an invalid size(%s)" % (w.attrib['name'],size)
			return None
	if 'size2' in w.attrib.keys():
		size2 = w.attrib['size2']
		if not unicode(size2).isdecimal():
			print "ERROR: Table '%s' has an invalid size2(%s)" % (w.attrib['name'],size2)
			return None
	if 'size3' in w.attrib.keys():
		size3 = w.attrib['size3']
		if not unicode(size3).isdecimal():
			print "ERROR: Table '%s' has an invalid size3(%s)" % (w.attrib['name'],size3)
			return None
	if 'union_name' in w.attrib.keys():
		union = w.attrib['union_name']
		if not isName(union):
			print "ERROR: Table '%s' has an invalid union name(%s)" % (w.attrib['name'],union)
			return None
	return fwTable(w.attrib['name'],size,size2,size3,union)

def parse_table_property(w,tab):
	length = None
	length2 = None
	length3 = None
	anchor = None
	shared = None
	align_type = None
	align = None
	prefix = None
	module = None
	tbldmp = None
	if 'anchor' in w.attrib.keys():
		anchor = w.attrib['anchor']
	if 'shared_id' in w.attrib.keys():
		shared = w.attrib['shared_id']
	if 'size' in w.attrib.keys():
		length = w.attrib['size']
		if not unicode(length).isdecimal():
			print "ERROR: Table %s has property with invalid size(%s)" % (tab.name,length)
			return False
	if 'size2' in w.attrib.keys():
		length2 = w.attrib['size2']
		if not unicode(length2).isdecimal():
			print "ERROR: Table %s has property with invalid size2(%s)" % (tab.name,length2)
			return False
	if 'size3' in w.attrib.keys():
		length3 = w.attrib['size3']
		if not unicode(length3).isdecimal():
			print "ERROR: Table %s has property with invalid size3(%s)" % (tab.name,length3)
			return False
	if 'align_type' in w.attrib.keys():
		align_type = w.attrib['align_type']
		if not isName(align_type):
			print "WARNING: Table %s has property eith align_type not valid. It will be considered 'regular'" % (tab.name,align_type)
	if 'alignment' in w.attrib.keys():
		align = w.attrib['alignment']
		if not unicode(align).isdecimal():
			print "ERROR: Table %s has property with invalid alignment(%s)" % (tab.name,align)
			return False	
	if 'address_prefix' in w.attrib.keys():
		prefix = w.attrib['address_prefix']
		if not isName(prefix):
			print "WARNING: Table %s has property with invalid prefix(%s)" % (tab.name,prefix)
			prefix = None
	if 'module_name' in w.attrib.keys():
		module = w.attrib['module_name']
		if not isName(module):
			print "WARNING: Table %s has property with invalid module name(%s)" % (tab.name,module)
			module = None
	if 'tbldmp' in w.attrib.keys():
		tbldmp = w.attrib['tbldmp'].upper()
		if tbldmp != 'TRUE' and tbldmp != 'FALSE':
			print "WARNING: Segment '%s' , 'tbldmp' has an incorrect value(%s). It will be considered 'FALSE'" % (w.attrib['name'],
				w.attrib['tbldmp'])
			tbldmp = "FALSE"
	tab.add_properties(w.attrib['address'],length,length2,length3,anchor,shared,align_type,align,prefix,module,tbldmp)
	return True

def help():
	print 'Parameters: <XML file> [options]'
	print 'Options: - any combination of the bellow'
	print '\t-v    = validate'
	print '\t-f    = put generated files in ../files/fw_<date_hour_min>' 
	print '\t   otherwise, it put the files into the same directory as the XML file'
	print '\t-g    = generate'
	print '\t-ds   = display short : project->segment->tables'
	print '\t-dl   = display short : project->segment->tables->entries->fields'
	print '\t-c    = generate code'
	print '\t-gui  = graphics [-p <project> [-s <segment> [-t <table> [-e <entry]]]]'
	print '\t-mgui = graphics, same options as -gui and modidy fields'
	print '\t\t functions:  Insert,Delete,PageUp,PageDown'
	print '\t\t limitation: cannot define/change an union - but only its fields'
	print '\t\t             cannot move a field in/out an union from/to regular fields'
	print '\t-h    = help'

def main(argv):
	options = ['-v','-dl','-ds','-n','-g','-c','-gui','-mgui','-d', '-f','-h','-p','-s','-t','-e']
	if len(argv) <= 1:
		help()
		return
	if not argv[1].endswith(".xml"):
		print ("the file must be a '.xml' one")
		return
	option = ["-n"]
	if len(argv) > 2:
		option = argv[2:]
	if '-h' in option:
		help()
	for o in option:
		if o not in options and o.startswith('-'):
			help()
			return
	FWprojects = [] # contains tables_unified : specific tables and all DEFAULT tables
	FWsegments = [] # contains tables per segment - as they are defined
	try:
		tree = ET.parse(argv[1])
	except IOError:
		print "Cannot open '%s' file" % (argv[1])
		return
	except ParseError as e:
		print "XML Error in '%s' file : %s" % (argv[1],e)
		return
	root = tree.getroot()
	# list of elements 'data_segment' which are segments' definition
	seg_definition = root.findall('data_segment[@start_address]')
	# list of all elements 'project', project definitions
	projects = root.findall("project")
	# parse over all 'project' definitions
	for p in projects:
		if not isName(p.attrib['name']):
			print "ERROR: Project '%s' has not a valid name" % (p.attrib['name'])
			continue
		# create project object
		current_project = fwProject(p.attrib['name'])
		# list of all elements 'project_data_segment', segments definitions under one project
		segments = p.findall("project_data_segment")
		# parse all segments definition under project
		for s in segments:
			# s.attrib['name'] is segment name under project
			# i need data segment of segment definition with the name from attrib
			working_list = [x for x in seg_definition if s.attrib['name'] == x.attrib['name']]
			if len(working_list) > 1:
				print "ERROR : more than one segment with the same name : project="+p.attrib['name']+" segment="+s.attrib['name']
				continue
			if len(working_list) < 1:
				print "ERROR : no segment for : project="+p.attrib['name']
				continue
			# create segment object, from definitions
			crt_seg = parse_segment(working_list[0])
			if crt_seg:
				# create segment ForProject object - same basic definitions, but connected to FWprojects list
				crt_seg_for_project = fwSegmentForProject(crt_seg.name,crt_seg.start_address,crt_seg.end_address,
					crt_seg.generate_pointer,crt_seg.device)
				already_defined_segs = [x for x in current_project.segments if x.name == crt_seg.name]
				if len(already_defined_segs) == 0:
					# add segment to project
					current_project.add_segment(crt_seg_for_project)
				already_defined_segs = [x for x in FWsegments if x.name == crt_seg.name]
				if len(already_defined_segs) == 0:
					# add segment to FWsegments list
					FWsegments.append(crt_seg)
			else:
				return
		# add project to FWprojects
		FWprojects.append(current_project)
	# list of elements 'data_segment' which are entries' definition
	entry_definition = root.findall('data_segment[@name="entries"]')
	if len(entry_definition) > 1:
		print "ERROR : more than one entries section"
		return
	# dict with entry name as key, value list of tuples (entry obj, list of projects)
	tables_entries = []
	# list of all defined entries
	entry_definition = entry_definition[0].findall('entry')
	# parse every defined entry
	for e in entry_definition:
		ent = parse_entry(e)
		if not ent:
			return
		# store entry object
		tables_entries.append(ent)
		# all childeren of an entry : fields and union_fields
		fields = e.findall('*')
		for f in fields:
			if f.tag == 'field':
				field = parse_field(f)
				if not field:
					return
				ent.add_field(field)
			else:
				if not isName(f.attrib['union_name']):
					print "WARNING: Field %s has an invalid union name" % (f.attrib['union_name'])
					continue
				if not unicode(f.attrib['union_size']).isdecimal():
					print "WARNING: Field %s has an invalid union size(%s)" % (f.attrib['union_name'],f.attrib['union_size'])
					continue
				union = fwUnion(f.attrib['union_name'],f.attrib['union_size'],ent)
				unionfields = f.findall('field')
				for u in unionfields:
					field = parse_field(u)
					if not field:
						return
					if field.bits > union.bits:
						print "ERROR: Field '%s' has size(%s) greater than union '%s' size(%s)" % (field.name,field.bits,union.name,union.bits)
					else:
						union.add_field(field)
				ent.add_field(union)
		# calculate all the lenght into an entry : per field its word,hword,dword and entry's length
		ent.calculate_length()

	# list of elements 'data_segment' which are tables' definition
	tab_definition = root.findall('data_segment[@name="tables"]')
	if len(tab_definition) > 1:
		print "ERROR : more than one tables section"
		return
	# list of tables
	tab_definition = tab_definition[0].findall('table')
	# parse all tables definitions
	for t in tab_definition:
		# list off all 'table_properties' tags under a table definition
		tab_properties = t.findall('table_properties')
		# list off all 'entry' tags under a table definition
		entries = t.findall('entry')
		# create basic table object
		current_tab = parse_table(t)
		if not current_tab:
			return
		# for each table_properities definition, creates a clone table fron the basic
		# entries is a list with all entries elements of the table
		for tp in tab_properties:
			clone_tab = copy.deepcopy(current_tab)
			# add properties
			if not parse_table_property(tp,clone_tab):
				continue
			projects = ['DEFAULT']
			if 'project' in tp.attrib.keys():
				# any alphabetic matches 1 or more times - list of all projects the table belongs
				projects = re.findall(r"[\w]+", tp.attrib['project'])
			segment = None
			if 'data_segment_name' in tp.keys():
				segment = tp.attrib['data_segment_name']
			if not segment:
				print 'ERROR: Table '+current_tab.name+'does not have defined segment'
				return
			# add projects to table - default is DEFAULT
			clone_tab.add_project_segment(projects,segment)
			tmp = [x for x in FWsegments if x.name == segment]
			# tmp is the list of segments to add the table
			if tmp:
				#add table to tables in segment
				tmp[0].add_table(clone_tab)
			# if there are specific projects defined - add the table to the correspondent segment
			for p in projects:
				tmp = [x for x in FWprojects if x.name == p]
				for s in tmp[0].segments:
					if s.name == segment:
						#add table in tables_unified in project
						s.add_table(clone_tab)
			# all table entries
			for tabent in entries:
				tmp = [x for x in tables_entries if x.name == tabent.attrib['name']]
				# if table is DEFAULT - add all its entries (even if there are entries defined for other projects)
				if projects[0] == 'DEFAULT':
					for tmpentry in tmp:
						clone_tab.add_entry(tmpentry)
				else:
					# if the table is specific - add the entry defined for the specific projects
					for tmpentry in tmp:
						common = [x for x in projects if x in tmpentry.projects]
						if tmpentry.projects[0] == 'DEFAULT' or len(common) > 0:
							clone_tab.add_entry(tmpentry)
	# parse enumerations
	codedefs = root.findall('data_segment[@name="codedefs"]')
	if len(codedefs) > 1:
		print "ERROR : more than one codedefs section"
		return
	if len(codedefs) > 0:
		codedefs = codedefs[0].findall('codedef')
		for cdef in codedefs:
			if not isName(cdef.attrib['name']):
				print "ERROR: Codefdef '%s' has an invalid name" % (cdef.attrib['name'])
				continue
			crt_codedef = fwCodedef(cdef.attrib['name'])
			projects = []
			if 'project' in cdef.attrib.keys():
				projects = re.findall(r"[\w]+", cdef.attrib['project'])
			values = cdef.findall('code')
			for v in values:
				if not isName(v.attrib['name']):
					print "ERROR: Codefdef '%s' has an invalid code(%s)" % (cdef.attrib['name'],v.attrib['name'])
					continue
				if not unicode(v.attrib['value']).isdecimal():
					print "ERROR: Codefdef '%s' has an invalid value(%s) for code(%s)" % (cdef.attrib['name'],v.attrib['value'],v.attrib['name'])
					continue
				crt_codedef.add_value(v.attrib['name'],v.attrib['value'])
			if len(projects) > 0:
				# add the enumeration list to specified projects
				for p in projects:
					tmp = [x for x in FWprojects if x.name == p]
					try:
						tmp[0].add_codedef(crt_codedef)
					except KeyError:
						print "ERROR: project %s does not exist" % (p)
			else:
				# no specific project - add it to DEFAULT
				tmp = [x for x in FWprojects if x.name == 'DEFAULT']
				tmp[0].add_codedef(crt_codedef)
	# make all the needed computation
	defprj = [x for x in FWprojects if x.name.upper() == 'DEFAULT']
	otherprj = [x for x in FWprojects if x.name.upper() != "DEFAULT"]
	# sort upon base address, the DEFAULT project tables, for every segment	
	for s in defprj[0].segments:
		s.build_sorted_tables()
	# for all the other projects - add the DEFAULT tables and sort then by their base address
	for p in otherprj:
		for s in p.segments:
			# list of segments in default project which are common to current project
			bb = [x for x in defprj[0].segments if x.name == s.name]
			# copy tables from DEFAULT into same segment of other projects
			for t in bb[0].tables_unified:
				s.add_table(t)
			s.build_sorted_tables()	
	# sort tables into the second data base : FWsegments
	for s in FWsegments:
		s.build_sorted_tables()
	# sort enumerations, by value, for each projects
	for p in FWprojects:
		for enum in p.codedefs:
			enum.sortedcode = sorted(enum.values.iteritems(), key=operator.itemgetter(1))
		for s in p.segments:
			# for each table per segment - calculate entries/table length in bytes, for each project
			for ti in range(len(s.tables_unified)):
				s.tables_unified[ti].get_table_bytes()

	# now, data bases are made - look for requests
	gui = False
	mgui = False
	if "-gui" in option:
		gui = True
		option.remove("-gui")
	if "-mgui" in option:
		mgui = True
		gui = False
		option.remove("-mgui")
	
	pathname = None
	for o in option:
		if o == '-dl':
			for s in FWsegments:
				s.print_segment(False)
				print '=============================================='
		if o == '-ds':
			for p in FWprojects:
				if p.name == 'DEFAULT':
					continue
				p.print_project(True)
		if o == '-v': # validation
			if validate(FWsegments,FWprojects):
				print "Data Base has no error !!!"
		if o == '-g': # generate h files
			pathnamet = generateHfiles(FWsegments,FWprojects,tables_entries,option,argv[1])
			showInfo(pathnamet,False)
		if o == '-c': # generate c code files
			pathnamet = generateCfiles(FWsegments,FWprojects,tables_entries,option,argv[1])
			showInfo(pathnamet,False)
	if gui or mgui:
		p = None
		s = None
		t = None
		e = None
		for en in tables_entries:
			en.done = False
		if '-p' in option:
			i = option.index('-p')
			p = option[i+1].upper()
		if '-s' in option:
			i = option.index('-s')
			s = option[i+1].upper()
		if '-t' in option:
			i = option.index('-t')
			t = option[i+1].upper()
		if '-e' in option:
			i = option.index('-e')
			e = option[i+1].upper()
		if gui:
			GUIapp(False,FWprojects,FWsegments,tables_entries,p,s,t,e,validate,generateHfiles,generateCfiles,argv[1])
		else: # option which permits field modifications
			GUIapp(True,FWprojects,FWsegments,tables_entries,p,s,t,e,validate,generateHfiles,generateCfiles,argv[1])

def validate(segments,projects):
	result = True
	result1 = True
	for p in projects:
		if p.name == 'DEFAULT':
			continue
		if not p.validate():
			result = False
		for seg in segments:
			if not seg.check_fields_codedef(p.name,p.codedefs):
				result1 = False
	return result and result1

def generateHfiles(segments,projects,tables_entries,option,arg1):
	import generateH
	for e in tables_entries:
		e.done = False
	if '-f' in option:
		import datetime
		datestr=datetime.datetime.now().replace(microsecond=0).strftime("%d.%m.%Y_%H_%M")
		pathname = '../files/fw_'+datestr
		if not os.path.exists(pathname):
			os.makedirs(pathname)
	else:
		pathname = os.path.dirname(arg1)
		if pathname == '':
			pathname = '.'
	pathname += '/'
	# generate h files for software - code and runner driver
	generateH.generate(projects,segments,pathname)
	# check if all entries are generated
	err = []
	for e in tables_entries:
		if not e.done and e.usage:
			err.append("WARNING: Entry %s is not part of any table" % (e.name))
		e.done = False
	# generate h files for firmware
	generateH.gen_fw_defs_auto(projects,tables_entries,pathname)
	return (pathname,err)

def generateCfiles(segments,projects,tables_entries,option,arg1):
	import generateC
	for e in tables_entries:
		e.done = False
	if '-f' in option:
		import datetime
		datestr=datetime.datetime.now().replace(microsecond=0).strftime("%d.%m.%Y_%H_%M")
		pathname = '../files/fw_'+datestr
		if not os.path.exists(pathname):
			os.makedirs(pathname)
	else:
		pathname = os.path.dirname(arg1)
	generateC.generateCode(projects,segments,pathname)
	err = []
	for e in tables_entries:
		if not e.done and e.usage:
			err.append("WARNING: Entry %s is not part of any table" % (e.name))
	return (pathname,err)

def debug(db,kind):
	if kind == 1:
		for s in db:
			for t in s.tables:
				print s.name+':'+t.prefix+t.name+':'+t.projects[0]
				#for e in t.entries:
					#print s.name+':'+t.prefix+t.name+':'+e.name
					#print e
	else:
		for p in db:
			for s in p.segments:
				for t in s.tables_unified:
					for e in t.entries:
						print p.name+'-'+s.name+'-'+t.name+'-'+e.name
						print e
					 
if __name__ == '__main__':
	from sys import argv
	strpos = sys.version
	posl = strpos.split()
	pos1 = posl[0].rfind('.')
	print 'Python version='+posl[0]
	if posl[0][0:pos1] != '2.7':
		print 'Sorry !! you need Python version 2.7.x and you have ' + posl[0][0:pos1]
	else:
		main(argv)



