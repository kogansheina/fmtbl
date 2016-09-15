#!/usr/bin/env python
import os
from fwclasses import fwProject, fwSegment, fwTable, fwEntry, fwField, fwUnion, fwCodedef
import genUtil

def generateCSV(project,filename):
	'''
	generates csv file for project
	'''
	filetoopen = filename+project.name+'_maps.csv'
	try:
		fcsv = open(filetoopen,'w')
		fcsv.write("/* This is an automated file. Do not edit its contents. */\n\n")
		fcsv.write("Data Item, Size(DEC), Start Address(HEX), End Address(HEX), color\n\n")
		totalfree = 0
		prev = 0 
		# run over all project'segments
		for s in project.segments:
			tab = None
			fcsv.write("\n")
			# for every table in segment
			for t in range(len(s.tables_unified)):
				try:
					tab = s.tables_unified[t]
					doit = False
					# determine if this project contains this table, according to table definition
					if project.name in tab.length.keys():
						doit = True
						pj = project.name
					if not doit and 'DEFAULT' in tab.length.keys():
						doit = True
						pj = 'DEFAULT'
					if doit:
						if tab.prefix != "":
							tabname = tab.prefix+tab.name
						else:
							tabname = tab.name
						# table length according to the project
						length = tab.length[pj][0][1]
						# end address of the table - last byte address
						end = tab.base_address + length-1
						# distance from the beginning of the current table and the previous one
						diff = tab.base_address - prev
						# if there is a free space - write line of free space
						if diff > 0:
							totalfree += diff+1
							b = tab.base_address - 1
							buf = ",%d, 0x%04X, 0x%04X, 0\n" % (diff,prev,b)
							fcsv.write(buf)
						# write a csv line
						buf = "%s.%s, %d, 0x%04X, 0x%04X, %d\n" % (s.name,tabname,length,tab.base_address,end,tab.at)
						fcsv.write(buf)
						prev = end + 1
				except KeyError:
					continue
			# see the free space from the end of the last table in segment and the segment end
			diff = s.end_address - prev
			if diff > 0:
				totalfree += diff+1
				buf = ",%d, 0x%04X, 0x%04X, 0\n" % (diff,prev,s.end_address)
				fcsv.write(buf)
		buf = "\nTotal Free Space, %d\n\n" % (totalfree)
		fcsv.write(buf)
		fcsv.close()
	except IOError:
		print "Cannot open '%s' file" % (filetoopen)
		return	

def format_runner_line(maxl,field,entry,runner_fw):
	"""
	generates line for all not reserved fields
	"""
	if field.name.lower().startswith('reserved'):
		return
	# add to longest field name, entry's name and a maximum fix part - for alignement
	maxl = maxl+len(entry.name)+25 # '#define + _F_OFFSET_MOD16 + space'
	txt = '#define '+entry.name.upper()+'_'+field.name.upper()
	txt1 = (txt+'_F_OFFSET ').ljust(maxl)
	txt2 = '%sd.%d\n' % (txt1,field.frombit)
	runner_fw.write(txt2)
	txt1 = (txt+'_F_WIDTH ').ljust(maxl)
	txt2 = '%sd.%d\n' % (txt1,field.bits)
	runner_fw.write(txt2)
	txt1 = (txt+'_OFFSET ').ljust(maxl)
	ti=0
	# calculates the field offset
	# if the entry is 1 word or longer
	if entry.length >= 4:
		# field byte or less - offset is half word
		if field.bits <= 8:
			ti = field.hword
		# field is longer than byte, but fits a half word - offset is nearest smaller half word
		elif field.bits <= 16:
			ti = (field.hword/2)*2
		# field is longer than 16 bits - offset is nearest smaller word
		else:
			ti = (field.hword/4)*4
	elif entry.length == 2: # if the entry is 2 bytes - offset is half word
		ti = field.hword
	txt2 = '%sd.%d\n' % (txt1,ti)
	runner_fw.write(txt2)
	# generates offset mod8 and mod16
	if field.bits < 8 and field.frombit > 7:
		txt1 = (txt+'_F_OFFSET_MOD8 ').ljust(maxl)
		txt2 = '%sd.%d\n' % (txt1,field.frombit%8)
		runner_fw.write(txt2)
	if field.bits < 16 and field.frombit > 15:
		txt1 = (txt+'_F_OFFSET_MOD16 ').ljust(maxl)
		txt2 = '%sd.%d\n' % (txt1,field.frombit%16)
		runner_fw.write(txt2)

def format_field_line(field,maxl,entname,stt):
	'''
	format a line for a field into a structure definition
	uintX_t field_name    :  field_bits sufix
	'''
	fieldsuffix = "\t__PACKING_ATTRIBUTE_FIELD_LEVEL__;"
	name = field.name.lower()
	enum = ""
	if field.isarray:
		nname = entname.upper()+'_'+field.name.upper()
		text = '\t%s\t%s[%s%s_NUMBER];' % (stt,name,genUtil.header,nname)
	else:
		l = "%d" % (field.bits)
		name = name.ljust(maxl)
		text = "\t%s\t%s\t:%s%s" % (stt,name,l,fieldsuffix)
	textfinal = text
	# if it is field and has a codedef field
	# write comment with its enumeration
	if isinstance(field,fwField):
		if field.codedef:
			enum = genUtil.header+field.codedef
			enum = enum.lower()
			enum = '/*defined by '+enum+' enumeration*/'
			textfinal += ' ' + enum
	return textfinal+'\n'

def calculateMaxl(maxl,entryname,f):
	if f.isarray:
		name = genUtil.header+entryname.upper()+'_'+f.name.upper()+'_NUMBER'
		textn = '%s\t%d\n' % (name,f.length)
		text = '%s[%s]' % (f.name,textn)
		if maxl < len(text):
			maxl = len(text)
	else:
		if maxl < len(f.name):
			maxl = len(f.name)
	return maxl

def generate_entry_struct(ent,structfile):
	'''
	generate entry structure as a typedef structure with all its fields
	generate all read/write macros for each field
	'''
	if ent.projects[0] != 'DEFAULT':
		# write '#ifdef ....
		txt = genUtil.set_project(ent.projects)
		structfile.write(txt)
	structheader = "\ntypedef struct\n{\n"
	structtail = "}\n__PACKING_ATTRIBUTE_STRUCT_END__"
	maxl = len('reserved')+2
	# find the most long name of a field, to make a nice alignment into the structure
	for f in ent.fields:
		if isinstance(f,fwUnion):
			for uf in f.fields:
				maxl = calculateMaxl(maxl,ent.name,uf)
		else:
			maxl = calculateMaxl(maxl,ent.name,f)
			if f.isarray:
				# if the field is an array - generate its size definition line
				name = genUtil.header+ent.name.upper()+'_'+f.name.upper()+'_NUMBER'
				textn = '%s\t%d\n' % (name,f.length)
				structfile.write('#define '+textn)
	# begin to write the structure
	structfile.write(structheader)
	# take the beginning of the first field (in bits)
	cur = ent.fields[0].frombit
	# entity - default is word (32 bits)
	# if the entry length is a byte or 2 bytes, the entity is 8 or 16
	d = 32
	if ent.length == 1:
		d = 8
	elif ent.length == 2:
		d = 16
	# run over all entry's fields
	for f in ent.fields:
		stt = 'uint%d_t' % (d)
		if isinstance(f,fwUnion):
			# format a line of the union itself
			textfinal=format_field_line(f,maxl,ent.name,stt)
			structfile.write(textfinal)
			# prepare comment - all the fields into the union are written under this comment
			structfile.write("/* fields union = "+f.name+", size = "+str(f.bits)+" bits\n")
			for unionf in f.fields:
				if unionf.isarray:
					if (unionf.bits == 8 or unionf.bits == 16 or unionf.bits == 32): #and (cur % unionf.bits == 0):
						stt = 'uint%d_t' % (unionf.bits)
				# format a field field line
				textfinal=format_field_line(unionf,maxl,ent.name,stt)
				structfile.write(textfinal)
			# close sub-fields comment
			structfile.write(" end fields union*/\n")
		else:
			if f.isarray:
				# determine maximum field length as software sees it
				if (f.bits == 8 or f.bits == 16 or f.bits == 32): #and (cur % f.bits == 0):
					stt = 'uint%d_t' % (f.bits)
			# format a field field line
			textfinal=format_field_line(f,maxl,ent.name,stt)
			structfile.write(textfinal)
		cur += f.get_fields()
	# close the structure
	text = '%s %s%s_DTS;\n\n' % (structtail,genUtil.header,ent.name) 
	structfile.write(text)
	maxl = 0
	# find the most long name of a field, to make a nice alignment of the macros
	for f in ent.fields:
		if isinstance(f,fwUnion):
			for uf in f.fields:
				if len(uf.name) > maxl:
					maxl = len(uf.name)
		else:
			if len(f.name) > maxl:
				maxl = len(f.name)
	# generate read/write macros for every field
	for f in ent.fields:
		genUtil.regular(f,maxl,ent,structfile,False)
		# if the field is an union of sub-fields - generate for them also, all macros
		if isinstance(f,fwUnion):
			for unionf in f.fields:
				genUtil.regular(unionf,maxl,ent,structfile,False)
	# close '#ifdef ....
	if ent.projects[0] != 'DEFAULT':
		structfile.write('#endif\n')

def generate_for_runner(table,runner_defs):
	# set table name adding prefix, if any
	if table.prefix != "":
		tname = table.prefix+table.name
	else:
		tname = table.name
	# write '#ifdef ..... in both files
	if table.projects[0] != 'DEFAULT':
		txtp = genUtil.set_project(table.projects)
		runner_defs.write(txtp)
	# write to runner definition file, table base address
	n = '#define ' + tname.upper() + '_ADDRESS'
	txt = '%s 0x%04x\n' % (n.ljust(100),table.base_address)
	runner_defs.write(txt)
	# close '#ifdef  for runner driver file
	if table.projects[0] != 'DEFAULT':
		txt = '#endif  /* %s */\n' % (table.projects[0].upper())
		runner_defs.write(txt)

def generate_table_struct(unions,table,filetowrite,runner_defs,seg_of_default):
	'''
	unions - a general list of all tables in an union
	seg_of_default - segment
	runner_defs - file for rdd driver definitions
	filetowrite - data structure file

	return the unions list updated
	'''
	if len(table.entries)==0:
		print "WARNING: No entry defined for table "+table.name
		return unions
	generate_for_runner(table,runner_defs)
	# if the table is a part of an union and it is not already counted
	if table.union:
		if not table.union in unions.keys():
			# add the union name
			unions[table.union] = [table]
		else:
			unions[table.union].append(table)
	else:
		generate_regular_table(table,filetowrite,seg_of_default)
	return unions

def generate_regular_table(table,filetowrite,seg_of_default):
	'''
	seg_of_default - segment
	filetowrite - data structure file
	'''
	dogenerate = True
	# if the table has only one entry, do not generate the table - the entry's structure is enough
	if table.size == 1 and table.size2 == 0 and table.size3 == 0:
		dogenerate = False
	maxl=0
	# calculate the longest entry name, for alignement
	for e in table.entries:
		if maxl < len(e.name):
			maxl = len(e.name)
	# add 5 chars
	maxl += 5
	# list of entries names
	enames = [x.name for x in table.entries]
	# set of unique names
	eset = set(enames)
	# list of unique names
	enames = list(eset)
	if dogenerate and not table.done:
		# generate a table structure
		setifdef = False
		if not table.donotduplicate and table.projects[0] != 'DEFAULT':
			txtp = genUtil.set_project(table.projects)
			filetowrite.write(txtp)
			setifdef = True
		# add prefix if it is defined and it is not a restriction of same basic table, differ by address
		if table.prefix != "" and not table.donotduplicate:
			tname = table.prefix+table.name
		else:
			tname = table.name
		# generate tables' sizes - if they are defined
		if table.size > 1:
			txt = '\n#define %s%s_SIZE     %d' % (genUtil.header,tname.upper(),table.size)
			filetowrite.write(txt)
		if table.size2 > 1:
			txt = '\n#define %s%s_SIZE2    %d' % (genUtil.header,tname.upper(),table.size2)
			filetowrite.write(txt)
		if table.size3 > 1:
			txt = '\n#define %s%s_SIZE3    %d' % (genUtil.header,tname.upper(),table.size3)
			filetowrite.write(txt)
		filetowrite.write('\ntypedef struct\n{\n')
		# if it is an union - add union's name as its entry
		if table.union:
			txt = '\t%s%s_DTS\tentry' % (genUtil.header,table.union.upper())
			if table.size > 1:
				txt += '[ %s%s_SIZE ]' % (genUtil.header,tname.upper())
			if table.size2 > 1:
				txt += '[ %s%s_SIZE2 ]' % (genUtil.header,tname.upper())
			if table.size3 > 1:
				txt += '[ %s%s_SIZE3 ]' % (genUtil.header,tname.upper())
			filetowrite.write(txt+';\n')
		else:
			# not an union - add all its entries to the structure
			for e in enames:
				txt = '\t%s%s_DTS\tentry' % (genUtil.header,e.upper())
				if table.size > 1:
					txt += '[ %s%s_SIZE ]' % (genUtil.header,tname.upper())
				if table.size2 > 1:
					txt += '[ %s%s_SIZE2 ]' % (genUtil.header,tname.upper())
				if table.size3 > 1:
					txt += '[ %s%s_SIZE3 ]' % (genUtil.header,tname.upper())
				filetowrite.write(txt+';\n')
		# close the structure, form table structure name
		txt = '%s%s_DTS;\n\n' % (genUtil.header,tname.upper())
		filetowrite.write('}\n__PACKING_ATTRIBUTE_STRUCT_END__ ' + txt)
		# if the segment has 'generate_pointer' option - generate pointer macro
		if seg_of_default.generate_pointer and seg_of_default.device:
			base = tname.upper()+"_ADDRESS"
			tabname = genUtil.header + tname.upper()
			if seg_of_default.start_address != 0:
				base += ' - '+seg_of_default.start.lower()
			txt = '#define %s_PTR()\t( %s_DTS * )(DEVICE_ADDRESS( %s ) + %s );\n\n' % (tabname,tabname,seg_of_default.device,base)
			filetowrite.write(txt)
		# close '#ifdef ... for data structure file
		if setifdef:
			filetowrite.write('#endif\n')
	# mark table
	table.done = True
	
def generateh(allSegments,seg_of_default,unions,structfile,runner_defs):
	'''
	generate software h files - structures and for rdd driver
		- generate entry structures
		- generate table structure
	'''
	# for all tables in segment
	for tabtuple in range(len(seg_of_default.tables)):
		t = seg_of_default.tables[tabtuple]
		# for all entries in table
		for e in t.entries:
			# if same entry in multiple tables - generate it only once
			if e.done:
				continue
			generate_entry_struct(e,structfile)
			e.done = True
		# generate table structure
		unions = generate_table_struct(unions,t,structfile,runner_defs,seg_of_default)
		# if table structure was generated and there are more than one table with the same name -
		# mark all the others as 'done', to skip a new generation of the same table
		if t.done:
			for s in allSegments:
				# if there is a table with size, then if need to be generated only once - mark table in all segments
				all_tables_with_same_name = [x for x in s.tables if x.name == t.name and x.donotduplicate]
				for allt in all_tables_with_same_name:
					allt.done = True
	return unions

def gen_fw_defs_auto(FWprojects,tables_entries,filename):
	'''
	generate h files for firmware 
	'''
	file_runner_fw = filename+'fw_defs_auto.h'
	file_copyright = 'runner_copyright.h'
	try:
		runner_fw = open(file_runner_fw,'w')
		file_copyright = open(file_copyright,'r')
	except IOError:
		print "Cannot open one of '%s','%s' files" % (file_runner_fw,file_copyright)
		return	
	for line in file_copyright:
		runner_fw.write(line)
	text = "\n\n/* This is an automated file. Do not edit its contents. */\n\n\n"
	runner_fw.write(text)
	file_copyright.close()
	# run over all defined entries
	for entry in tables_entries:
		# set '#ifdef .......
		if entry.projects[0] != 'DEFAULT':
			txt = genUtil.set_project(entry.projects)
			runner_fw.write(txt)
		writecomments = False
		maxl = 0
		# calculate the longest name of the fields in entry
		for f in entry.fields:
			if not f.name.lower().startswith('reserved'):
				writecomments = True
			if isinstance(f,fwField):
				if len(f.name) > maxl:
					maxl = len(f.name)
			else:
				for uf in f.fields:
					if len(uf.name) > maxl:
						maxl = len(uf.name)
		if writecomments:
			# if there is a field not 'reserved' generates a line with entry's length
			en = entry.name.replace('_',' ')
			runner_fw.write('/**** '+en.upper()+' ****/\n')
			txt = '\n#define %s%s_BYTE_SIZE\td.%d\n\n' % (genUtil.header,entry.name.upper(),entry.length)
			runner_fw.write(txt)
		# for each field	
		for f in entry.fields:
			if isinstance(f,fwField):
				format_runner_line(maxl,f,entry,runner_fw)
			else:
				for uf in f.fields:
					format_runner_line(maxl,uf,entry,runner_fw)
		if writecomments:
			runner_fw.write('\n')	
		# close '#ifdef ......
		if entry.projects[0] != 'DEFAULT':
			runner_fw.write('#endif\n')	
	# generates enumerations
	generate_enum(FWprojects,runner_fw,True)
	runner_fw.close()

def generate_enum(projects,file_data_h,fw_or_h):
	'''
	generates the enumeration constants 
	'''
	for v in projects:
		if len(v.codedefs) == 0:
			continue
		file_data_h.write('\n')
		if v.name != 'DEFAULT':
			txt = '#if defined '+ v.name
			file_data_h.write(txt+'\n')
		if not fw_or_h:
			file_data_h.write("typedef enum\n{\n")
		for c in v.codedefs:
			maxl = 0
			for n in c.values.keys():
				if len(n) > maxl:
					maxl = len(n) 
			maxl += len(c.name) + 4
			if not fw_or_h:
				name = c.name.upper()+'_FIRST = '
				last = c.sortedcode[0][1]
				txt = '\t%s%d,\n' % (name.ljust(maxl),last)
				file_data_h.write(txt)
			for cdef in c.sortedcode:
				cname = (c.name+'_'+cdef[0]).upper().ljust(maxl)
				if not fw_or_h:
					txt = '\t%s = %s,\n' % (cname,cdef[1])
				else:
					txt = '#define %sd.%s\n' % (cname,cdef[1])
				file_data_h.write(txt)
				last = cdef[1]
			if not fw_or_h:
				name = c.name.upper()+'_LAST = '
				txt = '\t%s%d\n' % (name.ljust(maxl),last)
				file_data_h.write(txt)
				txt = "} %s%s;\n" % (genUtil.header.lower(),c.name.lower())
				file_data_h.write(txt)
		if v.name != 'DEFAULT':
			file_data_h.write('#endif\n')

def generateUnions(unions,filetowrite,FWsegments):
	'''
	generate table unions
	a table union may have clone tables in different segments in different projects
	unions is a dict with union_name as key and a list of tables as value
	'''
	for union,tablelist in unions.iteritems():
		projects = []
		for table in tablelist:
			if table.projects[0] != 'DEFAULT':
				projects.extend(table.projects) 
		if len(projects):
			txtp = genUtil.set_project(projects)
			filetowrite.write(txtp)
		maxl=0
		# calculate the longest entry name, for alignement
		for e in table.entries:
			if maxl < len(e.name):
				maxl = len(e.name)
		# add 5 chars
		maxl += 5
		# list of entries names
		enames = [x.name for x in table.entries]
		# set of unique names
		eset = set(enames)
		# list of unique names
		enames = list(eset)
		# write the union structure
		filetowrite.write('\ntypedef union\n{\n')
		# all entries are part of the union
		for e in enames:
			name = (e.upper()+'_DTS').ljust(maxl)
			txt = '\t%s%s%s;\n' % (genUtil.header,name,e.lower())
			filetowrite.write(txt)
		txt = '%s%s_DTS;\n\n' % (genUtil.header,union.upper())
		filetowrite.write('}\n__PACKING_ATTRIBUTE_STRUCT_END__ ' + txt)
		if len(projects):
			filetowrite.write('#endif\n')
		for table in tablelist:
			segs = [x for x in FWsegments if x.name == table.segment]
			generate_regular_table(table,filetowrite,segs[0])

def generate(FWprojects,FWsegments,filename):
	'''
	generates csv files for each project, h file for software and rdd 
	'''
	for p in FWprojects:
		generateCSV(p,filename)
	file_data_struct = filename+'rdd_data_structures_auto.h'
	file_runner_defs = filename+'rdd_runner_defs_auto.h'
	file_copyright = 'runner_copyright.h'
	try:
		file_data_struct_h = open(file_data_struct,'w')
		file_runner_defs_h = open(file_runner_defs,'w')
		file_copyright = open(file_copyright,'r')
	except IOError:
		print "Cannot open one of '%s','%s','%s' files" % (file_data_struct,file_runner_defs,file_copyright)
		return	
	for line in file_copyright:
		file_data_struct_h.write(line)
		file_runner_defs_h.write(line)
	text = "\n\n/* This is an automated file. Do not edit its contents. */\n\n\n"
	file_data_struct_h.write(text)
	file_runner_defs_h.write(text)
	file_copyright.close()
	file_data_struct_h.write("#ifndef _RDD_DATA_STRUCTURES_AUTO_H\n#define _RDD_DATA_STRUCTURES_AUTO_H\n\n")
	file_runner_defs_h.write("#ifndef _RDD_RUNNER_DEFS_AUTO_H\n#define _RDD_RUNNER_DEFS_AUTO_H\n\n")
	unions = {}
	# pass over all segments
	for s in FWsegments:
		text = '/* '+s.name+' */\n'
		file_data_struct_h.write(text)
		file_runner_defs_h.write(text)
		unions = generateh(FWsegments,s,unions,file_data_struct_h,file_runner_defs_h)
	# generate table unions
	generateUnions(unions,file_data_struct_h,FWsegments)
	# generate enumerations types - for each project 
	generate_enum(FWprojects,file_data_struct_h,False)
	file_data_struct_h.write("#endif /* _RDD_DATA_STRUCTURES_AUTO_H */\n")
	file_data_struct_h.close()
	file_runner_defs_h.write("#endif /* _RDD_RUNNER_DEFS_AUTO_H */\n")
	file_runner_defs_h.close()



