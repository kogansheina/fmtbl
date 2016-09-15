from fwclasses import fwProject, fwSegment, fwTable, fwEntry, fwField, fwUnion, fwCodedef
header = 'RDD_'
def set_project(projectList):
	txt = '#if defined ' + projectList[0]
	for p in projectList[1:]:
		txt += ' || defined ' + p
	txt += '\n'
	return txt

def writeMacros(field,entry,rbody,wbody,maxlfields,filetowrite,gencode):
	'''
	format the entire line of macro definition
	rbody - read macro body
	wbody - write macro body
	maxlfields - number of chars of the longest field name
	generate macros only for not reserved fields
	for code generation - use macros for those fields also
	'''
	if not field.name.lower().startswith('reserved') or gencode:
		txt = '#define %s%s_' % (header,entry.name.upper())
		# txt is the beginning of the first part of a macro definition
		# the alignement must be done according to the longest name + the first part + some fix part
		maxl = maxlfields+18+len(txt) # _WRITE( v, p )
		txt += field.name.upper()
		if field.isarray:
			txtR = txt+"_READ( r, p, i )"
			txtW = txt+"_WRITE( v, p, i )"
		else:
			txtR = txt+"_READ( r, p )"
			txtW = txt+"_WRITE( v, p )"
		# format the first part of the macro and align it
		txtR = txtR.ljust(maxl)
		txtW = txtW.ljust(maxl)
		if not gencode:
			# write the macros
			filetowrite.write(txtR+rbody+'\n')
			filetowrite.write(txtW+wbody+'\n')
			if entry.genlocals and not field.isarray:
				txtR = txt+"_L_READ( wv )"
				txtW = txt+"_L_WRITE( v, wv )"
				txtR = txtR.ljust(maxl)
				txtW = txtW.ljust(maxl)
				txtf = '%sFIELD_GET( wv, %d, %d )\n' % (txtR,field.frombit,field.bits)
				filetowrite.write(txtf)
				txtf = '%sFIELD_SET( v, %d, %d, wv )\n' % (txtW,field.frombit,field.bits)
				filetowrite.write(txtf)
		else:
			# for c code - use only macros body
			n = field.name.ljust(25)
			# if the field in an array - generate a loop for read/write
			if field.isarray:
				txt = '\tSTT_PRINTF("\\t%s=\\n\\t");\n' % (n)
				filetowrite.write(txt)
				txtr = '\tfor(i=0,j=0; i<%d; i++)\n\t{\n' % (field.length)
				filetowrite.write(txtr)
				filetowrite.write("\t\t"+rbody+";\n")
				filetowrite.write('\t\tif (decreq)\n\t\t\tSTT_PRINTF(\"%d \", (int)r);\n') 
				filetowrite.write('\t\telse\n\t\t\tSTT_PRINTF(\"0x%08x \", (unsigned int)r);\n')
				filetowrite.write('\n\t\tif (rw == WRITEREG)\n\t\t{\n\t\t\tSTT_PRINTF("\\t==>");\n')
				filetowrite.write('\t\t\tif (scanf("%x",&v) == 1)\n')
				filetowrite.write('\t\t\t\t'+wbody+';\n\t\t}\n')
				filetowrite.write('\t\tj++;\n\t\tif (j >= 8)\n\t\t{\n\t\t\tj = 0;\n')
				filetowrite.write('\t\t\tSTT_PRINTF("\\n\\t");\n\t\t}\n')
				filetowrite.write('\t}\n\tif (!j)\n\t\tSTT_PRINTF("\\n");\n')
			else:
				filetowrite.write("\t"+rbody+";\n")
				txttmp1 = '"\\t' 
				txttmp2 = '= %d"'
				txtr = txttmp1+n+txttmp2+', (int)r);'
				filetowrite.write('\tif (decreq)\n\t\tSTT_PRINTF('+txtr+'\n')
				txttmp2 = '= 0x%08x\"'
				txtr = txttmp1+n+txttmp2+', (unsigned int)r);'
				filetowrite.write('\telse\n\t\tSTT_PRINTF('+txtr+'\n')
				filetowrite.write('\tif (rw == WRITEREG)\n\t{\n\t\tSTT_PRINTF("\\t==>");\n')
				filetowrite.write('\t\tif (scanf(\"%x\",&v) == 1)\n')
				filetowrite.write("\t\t\t"+wbody+";\n\t}\n")
				filetowrite.write('\telse\n\t\tSTT_PRINTF("\\n");\n')

def carehex(c):
	'''
	receives a number and returns a the correspondent string
	as a hexa representation of the number
	'''
	if c < 0: # the MSB bit is '1'
		# split the number into 7 LSB nibbles
		# they may be translated as usual
		temp = "%07x" % (c & 0x0fffffff)
		# its LSB nibble is transformed to a positive number
		# and translated as usual
		temp0 = "%x" % ((c & 0xf0000000) >> 28)
		# returns the concatenated string
		return "0x%s%s" % (temp0,temp)
	else:
		# return the usual translated string
		return '0x%08x' % (c)

def regular(field,maxl,entry,filetowrite,gencode):
	'''
	format the macros body according to the field length and position
	maxl - number of chars of the longest field name
	gencode - is True for c code generation
	'''
	I=""
	i="" 
	if field.isarray:
		I="I_"
		i="i, "
	# entire entry is 8 bits long
	if entry.reglen == 8:
		if field.bits == 8:
			# field of 8 bits => use exact byte access
			txtRB = 'MREAD_'+I
			txtWB = 'MWRITE_'+I
			tmp = "8((uint8_t *)p, %s" % (i)
		else:
			# field less than byte ==> use inner word macros
			txtRB = 'FIELD_MREAD_'+I
			txtWB = 'FIELD_MWRITE_'+I
			tmp = "8((uint8_t *)p, %d, %d, %s" % (field.frombit,field.bits,i)
		tmpr = "%sr )" % (tmp)
		tmpw = "%sv )" % (tmp)
	# entire entry is 16 bits long
	elif entry.reglen == 16:
		txtRB = 'FIELD_MREAD_'+I
		txtWB = 'FIELD_MWRITE_'+I
		if field.hword ==0: # field aligned to the beginning of the word
			tmp = "16((uint8_t *)p, %d, %d, %s" % (field.frombit,field.bits,i)
		else:
			tmp = "16((uint8_t *)p + %d, %d, %d, %s" % (field.hword,field.frombit,field.bits,i)
		# field is byte aligned to byte
		if field.bits == 8 and field.frombit%8 == 0: 
			txtRB = 'MREAD_'+I				# change the macros to exact ones
			txtWB = 'MWRITE_'+I
			if field.hword ==0: # field aligned to the beginning of the word
				tmp = "8((uint8_t *)p, %s" % (i)
			else:
				tmp = "8((uint8_t *)p + %d, %s" % (field.hword,i)
		# field less than byte, but inside a byte
		elif field.bits < 8 and (field.frombit/8 == (field.frombit+field.bits-1)/8):
			if field.hword ==0:
				tmp = "8((uint8_t *)p, %d, %d, %s" % (field.frombit%8,field.bits,i)
			else:
				tmp = "8((uint8_t *)p + %d, %d, %d, %s" % (field.hword,field.frombit%8,field.bits,i)
		# field is as entry's length
		elif field.bits == 16:
			txtRB = 'MREAD_'+I
			txtWB = 'MWRITE_'+I
			if field.hword ==0:
				tmp = "16((uint8_t *)p, %s" % (i)
			else:
				tmp = "16((uint8_t *)p + %d, %s" % (field.hword,i)
		tmpr = "%sr )" % (tmp)
		tmpw = "%sv )" % (tmp)
	# entry is exactly an word or the field is entirely into this word
	elif entry.reglen == 32 or field.dword < 0:
		txtRB = 'FIELD_MREAD_'+I
		txtWB = 'FIELD_MWRITE_'+I
		if field.hword ==0:
			tmp = "32((uint8_t *)p, %d, %d, %s" % (field.frombit,field.bits,i)
		else:
			tmp = "32((uint8_t *)p + %d, %d, %d, %s" % (field.word*4,field.frombit,field.bits,i)
		# field is byte aligned to byte
		if field.bits == 8 and field.frombit%8 == 0:
			txtRB = 'MREAD_'+I
			txtWB = 'MWRITE_'+I
			if field.hword ==0:
				tmp = "8((uint8_t *)p, %s" % (i)
			else:
				tmp = "8((uint8_t *)p + %d, %s" % (field.hword,i)
		# field is half word aligned to half word
		elif field.bits == 16 and field.frombit%16 == 0:
			txtRB = 'MREAD_'+I
			txtWB = 'MWRITE_'+I
			if field.hword ==0:
				tmp = "16((uint8_t *)p, %s" % (i)
			else:
				offset = (field.hword/2)*2
				tmp = "16((uint8_t *)p + %d, %s" % (offset,i)
		# field less than byte, but inside a byte
		elif field.bits < 8 and (field.frombit/8 == (field.frombit+field.bits-1)/8):
			if field.hword ==0:
				tmp = "8((uint8_t *)p, %d, %d, %s" % (field.frombit%8,field.bits,i)
			else:
				tmp = "8((uint8_t *)p + %d, %d, %d, %s" % (field.hword,field.frombit%8,field.bits,i)
		# field less than half word , but inside a half word
		elif field.bits < 16 and (field.frombit/16 == (field.frombit+field.bits-1)/16):
			if field.hword ==0:
				tmp = "16((uint8_t *)p, %d, %d, %s" % (field.frombit%16,field.bits,i)
			else:
				offset = (field.hword/2)*2
				tmp = "16((uint8_t *)p + %d, %d, %d, %s" % (offset,field.frombit%16,field.bits,i)
		# field long as the entry of an word
		elif field.bits == 32:
			txtRB = 'MREAD_'+I
			txtWB = 'MWRITE_'+I
			if field.word == 0:
				tmp = "32((uint8_t *)p, %s" % (i)
			else:
				offset = field.word*4
				tmp = "32((uint8_t *)p + %d, %s" % (offset,i)
		tmpr = "%sr )" % (tmp)
		tmpw = "%sv )" % (tmp)
	# all the othe cases - entry longer than an word
	else:
		# use composed macros:
		# read : read 2 words; apply mask and perform an or between results
		# write : apply mask, shift and write to 2 words
		offset = field.dword*4
		offset1 = offset+4
		size2 = 32 - field.frombit
		size1 = field.bits - size2
		mask = 1
		for i in range(1,size2):
			mask = ((mask << 1) | 1)
		notmask = ~mask
		strmask = carehex(mask)
		strnotmask = carehex(notmask)
		if offset == 0:
			txtRB = "{ uint32_t temp; FIELD_MREAD_32((uint8_t *)p, 0, %d, temp ); r = temp << %d; " % (size1,size2)
			txtWB = "{ FIELD_MWRITE_32((uint8_t *)p, 0, %d, ((v & %s) >> %d)); " % (size1,strnotmask,size2)
			tmpr = "FIELD_MREAD_32(((uint8_t *)p + %d), %d, %d, temp ); r = r | temp; }" % (offset1,field.frombit,size2)
			tmpw = "FIELD_MWRITE_32(((uint8_t *)p + %d), %d, %d, (v & %s)); }" % (offset1,field.frombit,size2,strmask)
		else:
			txtRB = "{ uint32_t temp; FIELD_MREAD_32(((uint8_t *)p + %d), 0, %d, temp ); r = temp << %d; " % (offset,size1,size2)
			txtWB = "{ FIELD_MWRITE_32(((uint8_t *)p + %d), 0, %d, ((v & %s) >> %d)); " % (offset,size1,strnotmask,size2)
			tmpr = "FIELD_MREAD_32(((uint8_t *)p + %d), %d, %d, temp ); r = r | temp; }" % (offset1,field.frombit,size2)
			tmpw = "FIELD_MWRITE_32(((uint8_t *)p + %d), %d, %d, (v & %s)); }" % (offset1,field.frombit,size2,strmask)
	# for fields with codedef - write a comment with its enumeration
	if isinstance(field,fwField) and field.codedef:
		tmpt = (header+field.codedef).lower()
		tmp = ' /*defined by %s enumeration*/' % (tmpt)
		tmpr += tmp
		tmpw += tmp
	# actualy format the macro
	writeMacros(field,entry,txtRB+tmpr,txtWB+tmpw,maxl,filetowrite,gencode)

