#!/usr/bin/env python
import copy
class fwProject():
	def __init__(self,name):
		self.name = name
		self.segments = []
		self.codedefs = []

	def add_segment(self,seg):
		if seg.name in [x.name for x in self.segments]:
			print "ERROR: Segment '%s' already defined for Project '%s'" % (seg.name,self.name)
		else:
			self.segments.append(seg)

	def add_codedef(self,codedef):
		for c in self.codedefs:
			if c.name == codedef.name:
				print "ERROR: Codedef '%s' already defined for Project '%s'" % (c.name,self.name)
				return
		self.codedefs.append(codedef)

	def validate(self):
		r1 = True
		for seg in self.segments:
			if not seg.check_table_overlapping(self.name):
				r1 = False
		return r1

	def print_project(self,sh):
		print "\nProject "+self.name
		for s in self.segments:
			s.print_segment(sh)
		for c in self.codedefs:
			c.print_defs()

class fwSegmentForProject():
	'''
	segment object for FWprojects list - its tables are all tables in project : specific and DEFAULT
	and sorted by start_address
	'''
	def __init__(self,name,start,end,generate_pointer,device):
		self.name = name
		self.start_address = start
		self.end_address = end
		self.generate_pointer = generate_pointer
		self.device = device
		self.tables_unified = []

	def build_sorted_tables(self):
		start = [x.base_address for x in self.tables_unified]
		# sort table base 
		sorted_start = sorted(start)
		tmp = []
		for ti in range(len(sorted_start)):
			for t in self.tables_unified:
				if t.base_address == sorted_start[ti] and not t in tmp:
					tmp.append(t)
					break
		self.tables_unified = tmp

	def check_table_overlapping(self,p):
		ret = True
		if len(self.tables_unified)==0:
			print "Segment '%s' has no tables under Project '%s'" % (self.name,p)
			return
		# first table
		prev0 = 0 # table index
		prev1 = self.tables_unified[prev0].base_address # table base address
		# check first with the beginning of the segment
		if prev1 < self.start_address:
			print "ERROR: Table '%s' overlaps with Segment '%s' start, under Project '%s'" % (self.tables_unified[prev0].name,self.name,p)
		# go over all the other tables in segment
		for ti in range(1,len(self.tables_unified)):
			t = self.tables_unified[ti]
			doit = False
			# if project is common to previous table and current - do check
			if p in self.tables_unified[prev0].length.keys() and p in t.length.keys():
				doit = True
				pjprev = p
				pj = p
			# if any - previous table and current is defined for DEFAULT project - do check
			if not doit and ('DEFAULT' in self.tables_unified[prev0].length.keys() or 'DEFAULT' in t.length.keys()):
				doit = True
				# determine the actual project to look for each table
				if 'DEFAULT' in self.tables_unified[prev0].length.keys():
					pjprev = 'DEFAULT'
				else:
					pjprev = p
				if 'DEFAULT' in t.length.keys():
					pj = 'DEFAULT'
				else:
					pj = p
			if not doit:
				continue
			try:
				# take table length according to project
				nextlength = self.tables_unified[prev0].length[pjprev][0][1]
			except KeyError:
				print 'Key error: p='+p+' pjprev='+pjprev
				print self.tables_unified[prev0].length[pjprev]
			# check base address of the current against base address of the previous plus its length into the current project
			if t.base_address < prev1 + nextlength:
				print "ERROR: Table '%s' overlaps with Table '%s' into the Segment '%s' under Project '%s'" % (t.name,self.tables_unified[prev0].name,self.name,p)
				print "DEBUG: base=0x%x prev=0x%x length=0x%x" % (t.base_address,prev1,nextlength)
				ret = False
			else:
				# current is ok with its precedent table - check it with segment end address
				try:
					# current table length per project
					nextlength = t.length[pj][0][1]
				except KeyError:
					print 'Key error: p='+p+' pj='+pj
					print t.length[pj]
				if t.base_address + nextlength - 1 > self.end_address:
					print "ERROR: Table '%s' ends beyond Segment '%s' boundaries under Project '%s'" % (t.name,self.name,p)
					print "DEBUG: base=0x%x length=0x%x end=0x%x" % (t.base_address,nextlength,self.end_address)
					ret = False	
			# go to next cuple			
			prev1 = t.base_address
			prev0 = ti
		return ret

	def add_table(self,tab):
		self.tables_unified.append(tab)

	def print_segment(self,sh):
		print "Segment %s : start=0x%x end=0x%x" % (self.name,self.start_address,self.end_address)
		for t in self.tables_unified:
			t.print_table(sh)
		print '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&'

class fwSegment():
	def __init__(self,name,start,end,genptr,dev):
		self.name = name
		self.start = start
		self.end = end
		if genptr == None or genptr == 'FALSE':
			self.generate_pointer = False
		else:
			self.generate_pointer = True
		self.device = dev
		self.tables = []
		try:
			if not start.startswith('0x') and not start.startswith('0X'):
				print "WARNING: Segment '%s' has a decimal end address %s" % (self.name,start)
				self.start_address = int(start,10)
			else:
				self.start_address = int(start,16)
			if not end.startswith('0x') and not end.startswith('0X'):
				print "WARNING: Segment '%s' has a decimal end address %s" % (self.name,end)
				self.end_address = int(end,10)
			else:
				self.end_address = int(end,16)
		except ValueError:
			print "ERROR: Segment: "+self.name+" ValueError for "+start+" or "+end
			self.start_address = 0
			self.end_address = 0

	def add_table(self,tab):
		'''
		add the table if it has an unique name, or it has different projects field or different prefix
		'''
		for t in self.tables:
			if tab.name == t.name and len([x for x in t.projects if x in tab.projects]) > 0 and tab.prefix == t.prefix:
				return 
		self.tables.append(tab)

	def build_sorted_tables(self):
		'''
		sort tables by their base address
		'''
		start = [x.base_address for x in self.tables]
		# sort table base 
		sorted_start = sorted(start)
		tmp = []
		# build a list of the sorted tables 
		for ti in range(len(sorted_start)):
			for t in self.tables:
				if t.base_address == sorted_start[ti] and not t in tmp:
					tmp.append(t)
					break
		self.tables = tmp

	def check_fields_codedef(self,projectname,listofcodedefs):
		'''
		for each field with 'codedef' definition of all entries of all tables,
		check that field length, in bits, may contain the greatest value of the enumeration
		'''
		ret = True
		for t in self.tables:
			if t.projects[0]!='DEFAULT' and not projectname in t.projects:
				return ret
			for e in t.entries:
				if e.projects[0]!='DEFAULT' and not projectname in e.projects:
					continue
				for f in e.fields:
					if isinstance(f,fwField) and f.codedef:
						crt = [x for x in listofcodedefs if x.name == f.codedef]
						if len(crt) > 1:
							print "WARNING: More than 1 definition for codedef '%s' under Project '%s'" % (f.codedef,projectname)
						elif len(crt) < 1:
							print "ERROR: Segment %s Field '%s' of Entry '%s' has codedef attribute '%s', but this is not defined for Project '%s'" % (self.name,f.name, 
								e.name, f.codedef,projectname)
							ret = False
						else:
							maxval = (1 << f.bits) - 1
							if maxval < crt[0].maxval:
								print "ERROR: Segment %s Field '%s' of Entry '%s' has %d bits, but the greatest value of enum '%s' is %d, under Project '%s'" % (self.name,f.name,
									 e.name,f.bits,f.codedef,crt[0].maxval,projectname) 							   
								ret = False
		return ret

	def print_segment(self,sh):
		print "Segment %s : start=0x%x end=0x%x %d %s" % (self.name,self.start_address,self.end_address,self.generate_pointer,self.device)
		for t in self.tables:
			t.print_table(sh)
		print '++++++++++++++++++++++++++++++++++++++++++++++'

class fwTable():
	def __init__(self,name,size,size2,size3,union):
		self.name = name
		if not size:
			self.size = 0
		else:
			self.size = int(size)
		if not size2:
			self.size2 = 0
		else:
			self.size2 = int(size2)
		if not size3:
			self.size3 = 0
		else:
			self.size3 = int(size3)
		self.union = union
		self.entries = []
		self.length = {}
		self.done = False
		self.donotduplicate = False
		# if the basic table has 'size' defined - it will overwrite any 'length' definition
		# and it means that all clone tables differ in base address ONLY - so the table will be
		# generated ONLY once (not how many table properties are defined)
		if self.size > 0:
			self.donotduplicate = True

	def add_properties(self,base,length,length2,length3,anchor,shared,align_type,align,prefix,module,tbldmp):
		self.anchor = False
		self.shared = False
		self.align_type = "regular"
		self.align = 1
		self.prefix = ""
		self.module = 'none'
		self.tbldmp = True
		self.at = 1
		if anchor:
			self.anchor = anchor
		if shared:
			self.shared = shared
		# if
		if length :
			if self.size == 0:
				self.size = int(length)
			else:
				if self.size != int(length):
					print "WARNING: Table '%s' property defines length(%s) different than table size(%d)" % (self.name,length,self.size)
		elif self.size == 0:
			self.size = 1 # force table size - if it is not defined at all
		if length2:
			if self.size2 == 0:
				self.size2 = int(length2)
			elif self.size2 != int(length2):
				print "WARNING: Table '%s' property defines length2(%s) different than table size2(%d)" % (self.name,length2,self.size2)
		if length3:
			if self.size3 == 0:
				self.size3 = int(length3)
			elif self.size3 != int(length3):
				print "WARNING: Table '%s' property defines length3(%s) different than table size3(%d)" % (self.name,length3,self.size3)
		if align_type:
			if align_type != 'table' and align_type != 'cyclic' and align_type != 'regular': 
				print "WARNING: Table '%s' property align type incorrectly(%s); it may be 'regular','cyclic','table'" % (self.name,align_type)
			else:
				self.align_type = align_type
		if self.align_type == 'table':
			self.at = 2
		elif self.align_type == 'cyclic':
			self.at = 3
		if align:
			self.align = int(align)
			if self.align%2 != 0 and self.align != 1:
				print "WARNING: Table '%s' has an invalid alignment. I must be 1 or even. It will be considered 1" % (self.name)
		if prefix:
			self.prefix = prefix+"_"
		if module:
			self.module = module
		if tbldmp:
			if tbldmp == "FALSE":
				self.tbldmp = False
		self.base = base
		try:
			self.base_address = int(base,16)
		except ValueError:
			print "ERROR: Table: "+self.name+" ValueError for "+base
			self.base_address = 0

	def add_entry(self,entry):
		for e in self.entries:
			# add an entry if it is unique in table or has different projects
			if e.name == entry.name and e.projects == entry.projects:
				return
		self.entries.append(entry)

	def add_project_segment(self,project,segment):
		self.projects = project
		self.segment = segment

	def get_table_bytes(self):
		'''
		calculates table length - migth be different in different projects
		'''
		if len(self.length) == 0:
			# dict with project as key
			# dict value will be a list of tuples (total entries length, table length)
			pr = {}
			for e in self.entries:
				for p in e.projects:
					if not p in pr.keys():
						pr[p] = []
			if not self.union:
				for p in pr.keys():
					temp = 0
					# for all entries of the given project
					for e in self.entries:
						if p in e.projects:
							temp += e.get_entry_bytes()
					if self.size:
						length = temp * self.size
					if self.size2:
						length *= self.size2
					if self.size3:
						length *= self.size3
					pr[p].append((temp,length))
			else: # table union
				maxentry = 0 
				for p in pr.keys():
					temp = 0
					# for all entries of the given project
					# take the maximum entry length
					for e in self.entries:
						if p in e.projects:
							temp = e.get_entry_bytes()
							if maxentry < temp:
								maxentry = temp
					if self.size:
						length = maxentry * self.size
					if self.size2:
						length *= self.size2
					if self.size3:
						length *= self.size3
					pr[p].append((maxentry, length))
			self.length = copy.deepcopy(pr)
		return self.length

	def print_table(self,s):
		if self.prefix != "":
			name = self.prefix+self.name
		else:
			name = self.name
		print "\tTable %s : base=%s size=%d size2=%d size3=%d union=%s" % (name,self.base,self.size,self.size2,self.size3,self.union)
		txt = "\t      Projects "
		for p in self.projects:
			txt += p+' '
		print "%s" % (txt)
		if not s:
			print "\t           anchor=%s shared=%s aling_type=%s align=%d module=%s tbldmp=%d" % (self.anchor,self.shared,self.align_type,self.align,self.module,self.tbldmp)
			for e in self.entries:
				e.print_entry()

class fwEntry():
	def __init__(self,name,projects,generate_locals,usage):
		self.name = name
		self.genlocals = False
		if generate_locals and generate_locals == "TRUE":
			self.genlocals = True
		self.fields = []
		self.length = 0 # number of bytes of the entry
		self.reglen = 0 # number of bits of the entry
		self.projects = projects
		self.hasarray = False
		self.done = False
		self.totalfields = 0
		self.usage = True
		if usage and usage == 'NO':
			self.usage = False

	def add_field(self,field):
		for f in self.fields:
			if f.name == field.name:
				print "ERROR: Field '%s' already defined for Entry '%s'" % (field.name,self.name)
				return False
		# increment only for regular field, not for union
		if isinstance(field,fwField):
			field.ind = len(self.fields)
			if field.isarray:
				self.hasarray = True
			self.totalfields += 1
		self.fields.append(field)
		return True

	def add_field_dyn(self,field,ind):
		'''
		add a new field thru GUI - it is added AFTER the selected field
		'''
		for f in self.fields:
			if f.name == field.name:
				txt = "ERROR: Field '%s' already defined for Entry '%s'" % (field.name,self.name)
				return txt
		field.ind = ind
		self.fields.insert(ind,field)
		if field.isarray:
			self.hasarray = True
		self.totalfields += 1
		return None

	def print_entry(self):
		print "\t\tEntry %s : genlocals=%d" % (self.name,self.genlocals)
		txt = "\t\t  Projects "
		for p in self.projects:
			txt += p+' '
		print "%s" % (txt)
		for f in self.fields:
			if isinstance(f,fwField):
				f.print_field()
			else:
				f.print_union()

	def get_entry_bytes(self):
		'''
		calculate entry's length in bytes
		'''
		if self.length == 0:
			length = 0
			for f in self.fields:
				# if the field is an union, take the global length
				if isinstance(f,fwUnion):
					length += f.bits
				else:
					# otherwise take field length
					length += f.get_fields()
			# total length of the entry in bits
			self.reglen = length
			# total length of the entry in bytes
			self.length =  length/8
			if length%8 != 0:
				self.length += 1
		return self.length

	def set_first_field(self,fld,maxl):
		'''
		because the fields must be represented in little endian and the processor is big endian
		the first defined field is the most left in the word
		therefore, it starts at maximum 'word' length minus its length in bits
		'word' may be byte, half word or word
		'''
		if fld.isarray:
			return 0
		return maxl-fld.bits

	def onefield(self,crtfld,prevfld,maxl,length):
		'''
		maxl - entity length (8,16 or 32)
		length - the accumulated length of fields, in bits
		crtfld - current field object 
		prevfld - previous field object  
		
		returns the current field length            
		'''
		if not prevfld.isarray:
			# if current length is less than the beginning of the previous
			if crtfld.bits < prevfld.frombit:
				# current begins before by its length from the previous
				crtfld.frombit = prevfld.frombit - crtfld.bits
				# same word
				crtfld.word = prevfld.word
			# if current length is greater than the beginning of the previous
			elif crtfld.bits > prevfld.frombit: 
				# it passed to the next word and begins from the maximum and before by its length from the previous
				crtfld.frombit = maxl + prevfld.frombit - crtfld.bits
				crtfld.word = prevfld.word + 1
				# if it does not begin at 0, means it lays into 2 words
				if prevfld.frombit > 0:
					crtfld.dword = crtfld.word - 1
			else:
				# current length is as previous beginning - means it is aligned to the word beginning
				crtfld.frombit = 0
				crtfld.word = prevfld.word
			crtfld.hword = length/8 # first byte number
		else:
			# previous field is an array - its length is multiplied by array's length
			# a presumption is done : FIELDS ARRAY ARE ALIGNED
			t = prevfld.bits * prevfld.length
			crtfld.word = prevfld.word + t/32
			if t%32 != 0:
				crtfld.word += 1
			crtfld.hword = prevfld.hword + t/8
			if t%8 != 0:
				crtfld.hword += 1
			crtfld.frombit = maxl-(crtfld.word%4+1)*8
		return crtfld.get_fields()

	def calculate_length(self):
		'''
		calculates fields parameters - it must be done after all entry's fields are defined
		it pass over all entry's fields, and calculates for each of them : frombit, word, hword and dword fields
		takeing in consideration if it is a regular field or an union of some fields
		'''
		length = self.get_entry_bytes() # entry's length in bytes
		if length == 0:
			return
		# maxl is maximum bits in entity
		maxl = 32
		if length == 1:
			maxl = 8
		elif length == 2:
			maxl = 16
		# first field of the entry
		field0 = self.fields[0]
		if isinstance(field0,fwField):
			# set the 'frombit' of the first field
			field0.frombit = self.set_first_field(field0,maxl)
		else:
			unionfields = field0
			unionfields.frombit = self.set_first_field(unionfields,maxl)
			# first bield of the union
			field0 = unionfields.fields[0]
			field0.frombit = self.set_first_field(field0,maxl)
			subunion = field0.subunion
			length = field0.bits
			# previous field is the first field of the entry
			prevfield = field0
			# go over all the other fields of the union
			for restfld in unionfields.fields[1:]:
				if restfld.subunion != subunion:
					subunion = restfld.subunion
					prevfield = field0
					length = restfld.bits
					restfld.frombit = self.set_first_field(restfld,maxl)
					restfld.word = field0.word
					restfld.hword = field0.hword
					restfld.dword = field0.dword
				else:
					length += self.onefield(restfld,prevfield,maxl,length)
				prevfield = restfld
		length = self.fields[0].bits
		# previous field is the first field of the entry
		prevfield = self.fields[0]
		# go over all the other fields of the entry
		for fld in self.fields[1:]:
			if isinstance(fld,fwField):
				length += self.onefield(fld,prevfield,maxl,length)
			else:
				# plength is the length the union begins; must be used for every subunion
				plength = length
				# set parameters for the entire union
				# length includes the union, it will be used for fields ofter the union
				length += self.onefield(fld,prevfield,maxl,length)
				# first field of the union
				firstfield = fld.fields[0]
				subunion = firstfield.subunion
				# set parameters for the first field of the union
				# as for the union itself
				dlength = plength + self.onefield(firstfield,prevfield,maxl,plength)
				# go over all the other fields of the union
				# previous field is the first field of the union
				dprevfield = prevfield
				for restfld in fld.fields[1:]: 
					if restfld.subunion != subunion:
						subunion = restfld.subunion
						# roll back as for the first field of the union
						dlength = plength + self.onefield(restfld,prevfield,maxl,plength)
					else:
						dlength += self.onefield(restfld,dprevfield,maxl,dlength)
					dprevfield = restfld
			prevfield = fld

class fwUnion():
	def __init__(self,name,length,parent):
		self.ind = len(parent.fields)
		self.name = name
		self.bits = int(length)
		self.fields = []
		self.isarray = False
		self.frombit = 0
		self.word = 0
		self.hword = 0
		self.dword = -1
		self.parent = parent
		self.totalfields = 0

	def add_field(self,field):
		for f in self.fields:
			if f.name == field.name:
				print "ERROR: Field '%s' already defined for Union '%s'" % (field.name,self.name)
				return False
		field.ind = self.ind+self.totalfields
		field.parent = self
		self.fields.append(field)
		self.parent.totalfields += 1
		self.totalfields += 1
		return True

	def add_field_dyn(self,field,ind):
		'''
		add a field to union thru GUI, it is added AFTER the selected field
		'''
		for f in self.fields:
			if f.name == field.name:
				txt = "ERROR: Field '%s' already defined for Entry '%s'" % (field.name,self.name)
				return txt
		field.ind = self.ind+ind
		self.fields.insert(ind,field)
		self.parent.totalfields += 1
		self.totalfields += 1
		return None

	def print_field(self):
		print "\t\t\tUnion %s frombit=%d length=%d" % (self.name,self.frombit,self.bits)
		for f in self.fields:
			print "\t",
			f.print_field()

	def get_fields(self):
		return self.bits

	def check_subunion(self):
		subunion = None
		subunion_length = 0
		for s in self.fields:
			if not subunion:
				subunion = s.subunion
			elif subunion != s.subunion:
				if subunion_length > self.length:
					print "ERROR: Sub-union '%s' has total length(%d) greater than Union(%s) length(%d)" % (subunion,subunion_length,self.name,self.length)
					subunion_length = 0
			else:
				subunion_length += s.bits

class fwField():
	def __init__(self,name,number_bits,number,isarray,codedef,subunion):
		self.ind = -1
		self.name = name
		self.bits = int(number_bits)
		self.length = int(number)
		self.isarray = isarray
		self.codedef = codedef
		self.subunion = subunion
		self.frombit = 0
		self.parent = None
		self.word = 0  	# word number
		self.hword = 0 	# byte number
		self.dword = -1	# if the field cross words - it is an word before self.word
		# index : 5 = bits, 6 = length ; 0-index,1-name,2-word,3-dword,4-frombit,7-union,8-subunion,9-codedef
		self.chgvalsw = {}

	def changeVal(self,ind,newval):
		if ind == 1:
			self.name = newval
		elif ind == 5:
			self.bits = int(newval)
		elif ind == 6:
			self.length = int(newval)
			if self.length > 1:
				self.isarray = True
		elif ind == 8:
			self.subunion = newval
		elif ind == 9:
			self.codedef = newval

	def print_field(self):
		print "\t\t\t%d Field %s bits=%d length=%d sub-union=%s codedef=%s" % (self.ind,self.name,self.bits,self.length,self.subunion,self.codedef)
		print "\t\t\t   frombit=%d word=%d hword=%d dword=%d" % (self.frombit,self.word,self.hword,self.dword)

	def get_fields(self):
		if not self.isarray:
			return self.bits
		else:
			return self.bits*self.length

class fwCodedef():
	def __init__(self,name):
		self.name = name
		self.values = {}
		self.maxval = 0
		self.sortedcode = []

	def add_value(self,name,value):
		self.values[name] = int(value)
		if self.maxval < self.values[name]:
			self.maxval = self.values[name]

	def print_defs(self):
		print "\tCodeDefs %s max value=%d" % (self.name,self.maxval)
		for k,v in self.values.iteritems():
			print "\t\t%s = %s" % (k,v)


