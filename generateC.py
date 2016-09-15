#!/usr/bin/env python
import os
from fwclasses import fwProject, fwSegment, fwTable, fwEntry, fwField, fwUnion, fwCodedef
import genUtil

def generateCode(FWprojects,FWsegments,filename):
	'''
	generate c,h code files, to be used into real image to print the content of an entry,
	according to its structure dfinition
	'''
	file_dumpAddrsName = filename+'/runnerreg_DumpAddrs.c'
	file_dumphName = filename+'/runnerreg_Dump.h'
	file_dumpcName = filename+'/runnerreg_Dump.c'
	file_regaddrsName = filename+'/regaddrs.h'
	try:
		file_dumpAddrs = open(file_dumpAddrsName,'w')
		file_dumph = open(file_dumphName,'w')
		file_dumpc = open(file_dumpcName,'w')
		file_regaddrs = open(file_regaddrsName,'w')
	except IOError:
		print "Cannot open one of '%s','%s','%s','%s' files" % (file_dumpAddrsName,file_dumphName,file_dumpcName,file_regaddrsName)
		return	
	file_dumph.write("#ifndef __RUNNERREG_DUMP_H_INCLUDED")
	file_dumph.write("\n#define __RUNNERREG_DUMP_H_INCLUDED\n\n")
	file_dumph.write('#include "runner_reg_dump.h"\n\n')
	file_dumpc.write('#include <stdio.h>\n')
	file_dumpc.write('#include <stdlib.h>\n')
	file_dumpc.write('#include "access_macros.h"\n')
	file_dumpc.write('#include "runnerreg_Dump.h"\n')
	file_dumpc.write('#include "memreg.h"\n\n')
	file_regaddrs.write("#ifndef _REGS_ADDRS_H\n#define _REGS_ADDRS_H\n\n")
	# prepare data base for a new generation
	for s in FWsegments:
		for t in s.tables:
			t.done=False
	# over all segments
	for s in FWsegments:
		# over all tables
		for t in s.tables:
			if not t.done:
				# over all entries
				for e in t.entries:
					if not e.done:
						generate_entry_code(e,t,s.name,file_dumph,file_dumpc,file_regaddrs)
						e.done = True
				t.done = True
	file_dumpAddrs.write('#include "runnerreg_Dump.h"\n')
	file_dumpAddrs.write('#include "rdp_maps.h"\n\n')
	file_dumpAddrs.write('unsigned int SEGMENTS_ADDRESSES[NUMBER_OF_SEGMENTS] =\n{\n')
	# generate addresses for all projects
	for p in FWprojects:
		if p.name == 'DEFAULT': # skip defualt project, its tables are included
			continue
		# write '#ifdef .........
		file_dumpAddrs.write('#ifdef '+p.name+'\n')
		# over all segments
		for s in p.segments:
			# write segment start address
			if s.generate_pointer:
				txt = ' 0x%x + %s,' % (s.start_address,s.device)
			else:
				txt = ' 0x%x,' % (s.start_address)
			file_dumpAddrs.write(txt)
		# close project
		file_dumpAddrs.write('\n#endif\n')
	file_dumpAddrs.write('};\n')
	# pass over all segments with their original tables
	for seg in FWsegments:
		# for every table
		for v in seg.tables:
			# write '#ifdef ....
			if v.projects[0] != 'DEFAULT':
				txt = genUtil.set_project(v.projects)
				file_dumpAddrs.write(txt)
			# set table name, add prefix, if any
			if v.prefix != "":
				vname = v.prefix+v.name
			else:
				vname = v.name
			txt = 'static DUMP_RUNNERREG_STRUCT %s =\n{\n' % (vname)
			file_dumpAddrs.write(txt)
			templistoflengths = v.get_table_bytes()
			already = False
			# for all table's entries
			for ent in v.entries:
				try:
					# common projects between entry and table
					common = [x for x in ent.projects if x in templistoflengths.keys()]
					pj = ent.projects[0]
					# set table project
					if len(common) == 0: # nothing in common
						if 'DEFAULT' in templistoflengths.keys():
							pj = 'DEFAULT'
					# entry is defined for specific project
					if ent.projects[0] != 'DEFAULT':
						# set '#ifdef ....
						txt = genUtil.set_project(ent.projects)
						file_dumpAddrs.write(txt)
						# write entry length, according to project
						txt = '\t%d,\n\t{\n' % (templistoflengths[pj][0][0])
						file_dumpAddrs.write(txt)
					elif not already: # DEFAULT - check if it was not already generated
						# write entry's length
						txt = '\t%d,\n\t{\n' % (templistoflengths[pj][0][0])
						file_dumpAddrs.write(txt)
						already = True
					# write callbacks
					txt = '\t\t{ dump_%s%s, ' % (genUtil.header,ent.name.upper())
					file_dumpAddrs.write(txt)
					# write table base address
					txt = '0x%x },\n' % (v.base_address)
					file_dumpAddrs.write(txt)
					# close #endif
					if ent.projects[0] != 'DEFAULT':
						file_dumpAddrs.write('#endif\n')
				except KeyError:
					print "KeyError"
					print ent.projects
					print templistoflengths
					continue
			# close structure
			file_dumpAddrs.write("\t\t{ 0, 0 },\n\t}\n};\n")
			# close #ifdef
			if v.projects[0] != 'DEFAULT':
				file_dumpAddrs.write('#endif\n')
	# fill the main structure
	file_dumpAddrs.write("\nTABLE_STRUCT RUNNER_TABLES[NUMBER_OF_TABLES] =\n{\n")
	# go over all segments' tables
	for seg in FWsegments:
		for v in seg.tables:
			if v.projects[0] != 'DEFAULT':
				txt = genUtil.set_project(v.projects)
				file_dumpAddrs.write(txt)
			if v.prefix != "":
				vname = v.prefix+v.name
			else:
				vname = v.name
			# set index entry in structure - contains 'tbldmp' field - table might be viewed
			txt = '\t{ \"%s\", %d, %s_INDEX, & %s },\n' % (vname,v.tbldmp,seg.name.upper(),vname)
			file_dumpAddrs.write(txt)
			if v.projects[0] != 'DEFAULT':
				file_dumpAddrs.write('#endif\n')
	for y in range(len(FWsegments)):
		# define segments indexes in registers addresses file
		txt = '#define %s_INDEX\t %d\n' % (FWsegments[y].name.upper(),y)
		file_regaddrs.write(txt)
	# for each project - skip DEFAULT
	for p in FWprojects:
		if p.name != 'DEFAULT':
			file_regaddrs.write('#if defined '+p.name.upper()+'\n')
			n = 0
			# write number of segments for each project
			txt = '#define NUMBER_OF_SEGMENTS\t %d\n' % (len(p.segments))
			file_regaddrs.write(txt)
			# write number of tables for each segment in project
			for s in p.segments:
				n += len(s.tables_unified)
			txt = '#define NUMBER_OF_TABLES\t %d\n' % (n)
			file_regaddrs.write(txt)
			file_regaddrs.write('#endif\n')
	file_dumpAddrs.write('};\n')
	file_dumph.write("\n#endif /* __RUNNERREG_DUMP_H_INCLUDED */\n")
	file_dumpAddrs.close()
	file_dumph.close()
	file_dumpc.close()
	file_regaddrs.write("\n#endif /* _REGS_ADDRS_H */\n")
	file_regaddrs.close()

def generate_entry_code(entry,table,segname,file_dumph,file_dumpc,file_regaddrs):
	'''
	generate c and h files, to be used into real image to print the content of an entry,
	according to its structure dfinition
	callbacks, to print entry's value
	'''
	if len(entry.fields) == 0:
		return
	txt = ''
	if entry.projects[0] != 'DEFAULT':
		txt = genUtil.set_project(entry.projects)
	elif table.projects[0] != 'DEFAULT':
		txt = genUtil.set_project(table.projects)
	if len(txt) > 0:
		file_dumph.write(txt)
		file_dumpc.write(txt)
	# callback definition
	txt = 'void dump_'+genUtil.header+entry.name.upper()+'(unsigned char *p, int rw, int decreq)'
	file_dumph.write(txt+';\n')
	file_dumpc.write(txt+'\n')
	txt =''
	# define subroutine variables
	if entry.hasarray:
		txt = '{\n\tunsigned int r,v;\n\tint i,j;\n\n\tSTT_PRINTF('
	else:
		txt = '{\n\tunsigned int r,v;\n\n\tSTT_PRINTF('
	# write title, as text for the print procedure : STT_PRINTF
	txt0 = entry.name+'\\n"'
	file_dumpc.write(txt+'"  Register '+txt0)
	file_dumpc.write(');\n\n')
	maxl = 0
	# the longest field name
	for f in entry.fields:
		if isinstance(f,fwUnion):
			for uf in f.fields:
				if len(uf.name) > maxl:
					maxl = len(uf.name)
		else:
			if len(f.name) > maxl:
				maxl = len(f.name)
	# for each field in entry - format macros body
	for f in entry.fields:
		genUtil.regular(f,maxl,entry,file_dumpc,True)
	# close subroutine
	file_dumpc.write('}\n')
	if entry.projects[0] != 'DEFAULT':
		file_dumph.write('#endif\n')
		file_dumpc.write('#endif\n')
	elif table.projects[0] != 'DEFAULT':
		file_dumph.write('#endif\n')
		file_dumpc.write('#endif\n')

