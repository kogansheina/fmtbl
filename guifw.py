from Tkinter import *
import tkFont
import tkMessageBox,tkFileDialog
from fwclasses import fwField, fwUnion
import os
# globals
fieldChanges = {} # dict with entry name as key, list of tuples (project,segment,table) as value
modifyFields=False
# constants
myFont  = -18 # in pixels = 12 points
FIRST = 0
LAST = 2
MIDDLE = 1
CHUNK = 5
titleFont = ("Arial", 16, "bold italic")
# globals !!!!
wpixel = 0
hpixel = 0
wchars = 0 # maximum number of chars in frame

class displayTable(Frame):
	'''
	generic class to display my tables
	received a list of header columns length, header columns names, callback to retrieve actual values
	project,segment,table,entry - identifies the table to be displayed
	name - is class type
	buttonw - add 'up/down' options
	all - add 'right' option
	'''
	def __init__(self,parent,project,segment,name,headercols=None,
				headernames=None,callbackValues=None,table=None,entry=None,
				buttonw=False,all=False):
		Frame.__init__(self, parent,bg="white")
		self.frames = parent.frames
		self.name = name				# instance name
		self.widgetsToDestoy = []		# list of widgets to be destroyed on change
		self.windowsList = []			# list of new windows generated from this one
		self.currentfrom = 0			# index 'from' to display lines in table
		self.tableList = []				# list on entries to be displayed - data base
		self.currentName = None			# name of the lowest level to be displayed : specific or None (for all)
		if name == "TABLE":
			self.currentName = table 
		elif name == "ENTRY":
			self.currentName = entry
		self.projects = parent.projects	# main data base
		self.project = project			# project name (specific or None)
		self.segment = segment			# segment name (specific or None)
		self.projectName = project		# project specific name 
		self.segmentName = segment		# segment specific name 
		self.tableName = table			# table specific name 
		self.entryName = entry			# entry specific name 
		self.parent = parent			# widget parent
		self.rowList = {}				# dict with project as key and list of its segments as value
		self.table=table				# table name or None
		self.entry=entry				# entry name or None
		self.config(headercols,headernames,callbackValues)
		self.setParameters()			# set all kinds of parameters
		self.title = self.setTitle()	# set title of the table
		self.buttons = False			# to make next/prev buttons
		self.all = all					# the class in on new window
		if not self.all:
			if len(self.tableList) > CHUNK: # index 'to' to display lines in table
				self.currentto = CHUNK		# there are more than 5 lines to be displayed
				self.buttons = True
			else:
				self.currentto = len(self.tableList) 
		else:
			self.currentto = len(self.tableList) 
		self.buttonw = buttonw			# to make new window
		self.maxn = self.setMaxName()	# maximum column 0 - longest name in table
		if self.buttons:				# to create next/prev buttons
			self.gifdown = PhotoImage(file = './arrowdown.gif')
			self.gifup = PhotoImage(file = './arrowup.gif')
		if self.buttonw:				# to create new window button
			self.gifright = PhotoImage(file = './arrowright.gif')
		self.oldw = None

	def config(self,headercols=None,headernames=None,callbackValues=None):
		self.headercols = headercols		# list of columns width
		self.headernames = headernames		# list of columns names
		self.callbackValues = callbackValues# callback to receive a list of columns' values

	def setParameters(self):
		'''
		parameters : set class parameter
			project     - intial parameter (project name or None)
			projectName - actual project name 
			segment     - inital parameter (segment name or None)
			segmentName - actual segment name
			table     - inital parameter (table name or None)
			tableName - actual table name
			entry     - inital parameter (entryt name or None)
			entryName - actual entry name

			self.tableList - list of objects to be displayed
		'''
		if self.name == "PROJECT":
			if self.project == None:
				for p in self.projects:
					if p.name == 'DEFAULT':
						continue
					segments = []
					if self.segment == None:
						for s in p.segments:
							segments.append(s)
					else:
						s = [x for x in p.segments if x.name == self.segment]
						if len(s) == 0:
							print "Wrong segmentt '"+self.segment+"'"
							return
						segments.append(s[0])
					self.rowList[p.name]=segments
			else:
				p = [x for x in self.projects if x.name == self.project]
				if len(p) == 0:
					print "Wrong project '"+self.project+"'"
					return
				segments = []
				if self.segment == None:
					for s in p[0].segments:
						segments.append(s)
				else: # specific segment 
					s = [x for x in p[0].segments if x.name == self.segment]
					segments.append(s[0])
				self.rowList[self.project]=segments
		else:
			if self.project == None:
				self.projectName = self.projects[1].name
				if self.segment == None:
					self.tableList = self.projects[1].segments[0].tables_unified
					self.segmentName = self.projects[1].segments[0].name
				else:
					tmp = [x for x in self.projects[1].segments if x.name == self.segmentName]
					if len(tmp) > 0:
						self.tableList = tmp[0].tables_unified
						self.segmentName = segment
					else:
						print "Wrong segment '"+self.segment+"'"
						return
			else: # specific project
				tmpp = [x for x in self.projects if x.name == self.project]
				if len(tmpp) == 0:
					print "Wrong project '"+self.project+"'"
					return
				if self.segment == None:
					self.tableList = tmpp[0].segments[0].tables_unified
					self.segmentName = tmpp[0].segments[0].name
				else: # specific segment
					tmps = [x for x in tmpp[0].segments if x.name == self.segment]
					if len(tmps) == 0:
						print "Wrong segment '"+self.segment+"'"
						return
					self.segmentName = self.segment
					tmpt = [x for x in tmps[0].tables_unified if "DEFAULT" in x.projects or self.projectName in x.projects]
					if len(tmpt) == 0:
						print "Wrong project '"+self.projectName+"'"
						return
					self.tableList = tmpt
			if self.name == "ENTRY" or self.name == "FIELD":
				if self.table == None:
					entryList = self.tableList[0].entries
					self.tableName = self.tableList[0].name
				else: # specific table
					tmp = [x for x in self.tableList if x.name == self.table]
					if len(tmp) == 0:
						print "Wrong table '"+self.table+"'"
						return
					tmpe = [x for x in tmp[0].entries if "DEFAULT" in x.projects or self.projectName in x.projects]
					entryList = tmpe
					self.tableName = self.table
				if self.name == "FIELD":
					if self.entry == None:
						fieldList = entryList[0].fields
						self.entryName = entryList[0].name
					else: # specific entry
						tmp = [x for x in entryList if x.name == self.entry]
						if len(tmp) == 0:
							print "Wrong Entry '"+self.entry+"'"
							return
						fieldList = tmp[0].fields
						self.entryName = self.entry
					self.tableList = fieldList
				else:
					self.tableList = entryList
		mysize = setFontSize(wchars,wpixel-10)
		self.textFontHeader = ("Arial", mysize, "bold italic")
		self.textFont = ("Arial", mysize)

	def setMaxName(self):
		maxn = 0						# maximum length(chars) of the tables names
		if self.name == "TABLE":
			if self.table == None:
				for i in range(len(self.tableList)):
					tab = self.tableList[i]
					if len(tab.name+tab.prefix) > maxn:
						maxn = len(tab.name+tab.prefix)
			else:
				maxn = len(self.table)
		elif self.name == "ENTRY":
			if self.entry == None:
				for i in range(len(self.tableList)):
					tab = self.tableList[i]
					if len(tab.name) > maxn:
						maxn = len(tab.name)
			else:
				maxn = len(self.entry)
		elif self.name == "FIELD":
			for i in range(len(self.tableList)):
				tab = self.tableList[i]
				if len(tab.name) > maxn:
					maxn = len(tab.name)
		else: # project
			for r in self.rowList.keys():
				if len(r) > maxn:
					maxn = len(r)
		return maxn

	def setTitle(self):
		if self.name == "TABLE":
			if self.table == None:
				title = 'FW Tables in Segment %s of Project %s' % (self.segmentName,self.projectName)
			else:
				title = 'FW Table %s in Segment %s of Project %s' % (self.tableName,self.segmentName,self.projectName)
		elif self.name == "ENTRY":
			if self.entry == None:
				title = 'FW Entries in Table %s in Segment %s of Project %s' % (self.tableName,self.segmentName,self.projectName)
			else:
				title = 'FW Entry %s in Table %s in Segment %s of Project %s' % (self.entryName,self.table,self.segmentName,self.projectName)
		elif self.name == "FIELD":
			title = 'FW Fields of Entry %s in Table %s in Segment %s of Project %s' % (self.entryName,self.tableName,self.segmentName,self.projectName)
		else:
			if self.project == None:
				if self.segment == None:
					title = 'FW Segments of all Projects'
				else:
					title = 'FW Segment %s of all Projects' % (self.segmentName)
			else:
				if self.segment == None:
					title = 'FW Segments of Project %s' % (self.projectName)
				else:
					title = 'FW Segment %s of Project %s' % (self.segmentName,self.projectName) 
		return title

	def doLines(self,i,j,which):
		'''
		display table rows
		get values for the specific table
		'''
		getvalues = self.callbackValues(self.tableList[i],-1)
		if self.name != "FIELD":
			values = getvalues[1]
			self.setOneLink(i+1+j,values[0],which,self.all)
			self.setOneLine(i+1+j,values,which)
		else:
			j = self.doFieldLines(i+1+j,which,self.tableList[i],getvalues)
		return j

	def doFieldLines(self,rownumber,which,field,getvalues):
		'''
		display fields table - take care of union fields
		'''
		k = getvalues[0]			# for fields in an union, = -1 end of the union fields
		values = getvalues[1]
		if not self.all:			# main window
			# for all coulmns
			for z in range(0,len(values)):
				if z == 1:	# name column
					w=LabelWidget(self.master,z,rownumber,values[z],self.textFont,"black",just='left',w=self.headercols[z],which=which)
				else:
					w=LabelWidget(self.master,z,rownumber,values[z],self.textFont,"black",just='center',w=self.headercols[z],which=which)
				self.widgetsToDestoy.append(w)
			# do it for all union fields
			if k > 0:
				# take the next field - it might be a field of an union
				getvalues = self.callbackValues(field,k)
				rownumber = self.doFieldLines(rownumber+1,which,field,getvalues)
		else: # 'right' window
			# detect specific entry block into data base
			tmpp = [x for x in self.projects if x.name == self.projectName]
			tmps = [x for x in tmpp[0].segments if x.name == self.segmentName]
			tmpt = [x for x in tmps[0].tables_unified if x.name == self.tableName]
			tmpe = [x for x in tmpt[0].entries if x.name == self.entryName]
			rownumber = self.setOneLineInAll(rownumber,which,field,getvalues,tmpe[0])
		return rownumber

	def setOneLineInAll(self,rownumber,which,field,getvalues,tmpe):
		'''
		display all fields of the entry
		'''
		notchangeble = [2,3,4,7] 	# word,hword,from,union
		k = getvalues[0]			# for fields in an union, = -1 end of the union fields
		values = getvalues[1]
		if len(values) == 0:		# no fields in the entry or end of an union
			return rownumber
		if values[7] != "None": 	# union name
			tmpu = [x for x in tmpe.fields if x.name == values[7]]
			tmpfl = [x for x in tmpu[0].fields if x.name == values[1]]
		else:
			tmpfl = [x for x in tmpe.fields if x.name == values[1]]
		tmpf= tmpfl[0]				# on field block
		# for all fields columns
		for z in range(0,len(values)):
			if modifyFields: 	# permits fields modification
				if z == 0:		# field number - used to select
					w=LabelWidget(self.master,z,rownumber,values[z],self.textFont,"green",just='center',w=self.headercols[z],which=which)
					def handler_move(event, ent=tmpe, row=tmpf):
						if event.keysym == 'Next' or event.keysym == 'Down':
							return self.moveupdown(ent,row,True)
						elif event.keysym == 'Prior' or event.keysym == 'Up':
							return self.moveupdown(ent,row,False)
						elif event.keysym == 'Insert':
							return self.insertline(ent,row)
						elif event.keysym == 'Delete':
							return self.deleteline(ent,row)
					def takeIt(event,w=w):
						w.config(fg='red')		# to know it is selected
						if self.oldw:
							self.oldw.config(fg='green')
						self.oldw = w
					w.bind("<Key>",func=handler_move)
					w.bind("<Button-1>",func=takeIt)
				elif z in notchangeble : # columns not defineable - they are calculated
					w=LabelWidget(self.master,z,rownumber,values[z],self.textFont,"black",just='center',w=self.headercols[z],which=which)
				else:	# columns which might be changed
					chgval = StringVar()
					chgval.set(values[z])
					if z == 1: # name
						w = Entry(self.master,bd=3,justify=LEFT,width=self.headercols[z],textvariable=chgval,fg="blue")
					else:
						w = Entry(self.master,bd=3,justify=CENTER,width=self.headercols[z],textvariable=chgval,fg="blue")
					w.grid(row=rownumber,column=z)
					def handler_modify(event, ent=tmpe, row=tmpf, ind=z, w=w):
						return self.chgField(ent,row,ind,w)
					w.bind("<Return>",func=handler_modify)
					# remember the StringVal to may get the new value
					tmpf.chgvalsw[z] = chgval
			else: # regular display
				if z==1:
					w=LabelWidget(self.master,z,rownumber,values[z],self.textFont,"black",just='left',w=self.headercols[z],which=which)
				else:
					w=LabelWidget(self.master,z,rownumber,values[z],self.textFont,"black",just='center',w=self.headercols[z],which=which)
			self.widgetsToDestoy.append(w)
		# do it for all union fields
		if k > 0:
			getvalues = self.callbackValues(field,k)
			rownumber = self.setOneLineInAll(rownumber+1,which,field,getvalues,tmpe)
		return rownumber

	def moveupdown(self,ent,fld,down):
		# down = True ==> go down, else go up
		# w is the list of row's widgets; its widgets begin at row*len(self.headercols)
		rownumber = fld.ind
		go = False
		if down:
			if rownumber < ent.totalfields - 1: # not last row
				nextrownumber = rownumber + 1
				go = True
		else:
			if rownumber > 0: # not the first row
				nextrownumber = rownumber - 1
				go = True
		if go:
			try:
				if fld.parent: # if not none, it is an union field
					if down:
						fldnext = fld.parent.fields[fld.ind-fld.parent.ind+1] # field to be first
					else:
						fldnext = fld.parent.fields[fld.ind-fld.parent.ind-1] # field to be first
				else:
					if down:
						fldnext = ent.fields[fld.ind+1] # field to be first
					else:
						fldnext = ent.fields[fld.ind-1] # field to be first
				# cannot move fields between union and regular
				# none has subunion or both have subunion
				if (fldnext.subunion == fld.subunion) or (fldnext.subunion != None and fld.subunion != None):
					#update indexes
					tmpi = fldnext.ind
					fldnext.ind = fld.ind
					fld.ind = tmpi
					#switch the fields
					if fld.parent: # if not none, it is an union field
						fld.parent.fields[fldnext.ind-fld.parent.ind] = fldnext
						fld.parent.fields[fld.ind-fld.parent.ind] = fld
					else:
						ent.fields[fldnext.ind]=fldnext
						ent.fields[fld.ind]=fld
					for wi in self.widgetsToDestoy:
						wi.destroy()
					self.widgetsToDestoy = []
					self.recalculate_fields(ent)
					row_offset=0
					# display the content of the columns for every row(table)
					for i in range(self.currentto-1):
						row_offset=self.doLines(i,row_offset,MIDDLE)
					self.doLines(self.currentto-1,row_offset,LAST)
					self.master.update_idletasks()
				else:
					txt1 = "Cannot switch between one field of union and one regular field\n"
					txt = 'subunion='
					if fldnext.subunion:
						txt += fldnext.subunion
					else:
						txt += 'None'
					txt += ' vs subunion='
					if fld.subunion:
						txt += fld.subunion
					else:
						txt += 'None'
					print txt1+txt
					tkMessageBox.showwarning("Warning", txt1+txt)
			except IndexError:
				print "%d index orig=%d : len=%d" % (down,fld.ind,len(ent.fields))
		else:
			tkMessageBox.showwarning("Warning", "Cannot do the move : row="+str(rownumber)+" total="+str(ent.totalfields))

	def insertline(self,ent,fld):
		'''
		insert a new field, AFTER the selected
		'''
		if fld.parent: # field of an union
			newfld = fwField("new",str(fld.parent.bits),"1",False,None,fld.subunion)
			# update indexes for the next fields
			i = fld.ind-fld.parent.ind
			for j in fld.parent.fields[i+1:]:
				j.ind += 1
			# add the new field to the union
			txt = fld.parent.add_field_dyn(newfld,i+1)
		else:
			newfld = fwField("new","32","1",False,None,None)
			# update indexes for the next fields
			i = fld.ind
			for j in ent.fields[i+1:]:
				j.ind += 1
			# add the field to the entry
			txt = ent.add_field_dyn(newfld,i+1)
			# increment the count for display
			self.currentto += 1
		if txt:
			# error adding the field
			tkMessageBox.showerror("Error", txt)
			return
		self.recalculate_fields(ent)
		for wi in self.widgetsToDestoy:
			wi.destroy()
		self.widgetsToDestoy = []
		row_offset=0
		# display the content of the columns for every row(table)
		for i in range(self.currentto-1):
			row_offset=self.doLines(i,row_offset,MIDDLE)
		self.doLines(self.currentto-1,row_offset,LAST)
		self.master.update_idletasks()
		# store a reminder of the change - used by 'save as...' function
		self.addToSet()

	def recalculate_fields(self,ent):
		'''
		set parameters as at the beginning, to permit re-calculation of the 'frombit','word' and 'hword' fields
		'''
		fld = ent.fields[0]
		fld.frombit = 0
		fld.word = 0
		fld.hword = 0
		fld.dword = -1
		ent.length = 0
		ent.calculate_length()

	def deleteline(self,ent,fld):
		'''
		delete a field
		'''
		if fld.parent: # field into an union
			# update indexes for the next fields
			i = fld.ind-fld.parent.ind
			for j in fld.parent.fields[i+1:]:
				j.ind -= 1
			fld.parent.fields.remove(fld)
			fld.parent.totalfields -= 1
		else:
			# update indexes for the next fields
			i = fld.ind
			for j in ent.fields[i+1:]:
				j.ind -= 1
			ent.fields.remove(fld)
			# decrement the counter for display
			self.currentto -= 1
		ent.totalfields -= 1
		for wi in self.widgetsToDestoy:
			wi.destroy()
		self.widgetsToDestoy = []
		self.recalculate_fields(ent)
		row_offset=0
		# display the content of the columns for every row(table)
		for i in range(self.currentto-1):
			row_offset=self.doLines(i,row_offset,MIDDLE)
		self.doLines(self.currentto-1,row_offset,LAST)
		self.master.update_idletasks()
		# store a reminder of the change - used by 'save as...' function
		self.addToSet()

	def addToSet(self):
		'''
		fieldChanges is a dictionary with entry name as key
		the value is a dictionary with project name as key and as value a tuple (segment,table)
		'''
		global fieldChanges
		if self.entryName in fieldChanges.keys():
			tempdict = fieldChanges[self.entryName]
			if not self.projectName in tempdict.keys():
				tempdict[self.projectName] = (self.segmentName,self.tableName)
		else:
			fieldChanges[self.entryName]={self.projectName:(self.segmentName,self.tableName)}
				
	def chgField(self,ent,fld,ind,w):
		'''
		read the new value of the column and store it into the data base
		'''
		#store a reminder of the change - used by 'save as...' function
		self.addToSet()
		v = fld.chgvalsw[ind].get()
		fld.changeVal(ind,v)
		self.recalculate_fields(ent)		
		row_offset=0
		# display the content of the columns for every row(table)
		for i in range(self.currentto-1):
			row_offset=self.doLines(i,row_offset,MIDDLE)
		self.doLines(self.currentto-1,row_offset,LAST)
		self.master.update_idletasks()

	def doDisplay(self):
		'''
		do actually the widgets to display data
		'''
		self.master = Canvas(self.parent,width=wpixel,bd=0,bg="white")
		self.lbl=TitleWidget(self.parent,text=self.title)
		# project has a special table
		if self.name == "PROJECT":
			# first column of the header
			LabelWidget(self.master,0,0,self.headernames[0],self.textFontHeader,"brown",w=self.headercols[0],which=FIRST)
			n = 0
			# calculate the length of the other columns
			for v in self.rowList.values():
				if len(v) > n:
					n = len(v)
			# second header - spans all segments columns + right arrows
			LabelWidget(self.master,1,0,self.headernames[1],self.textFontHeader,"brown",n=int(n*1.5),w=self.headercols[1]+self.headercols[2],which=FIRST)
			r = 1 # row number
			k = MIDDLE
			# display every segment for each project 
			for p,segs in self.rowList.iteritems():
				# set first column : project name, spans 2 rows
				LabelWidget(self.master,0,r,p, self.textFont,"black",w=self.headercols[0],which=k,r=2)
				# set all segments info for the current project; columns from 1, step 2 (1 for info, 1 for arrow)
				for i in range(len(segs)):
					# create widget with event -> display tables of the (project,segment) combination
					w=LabelWidget2(self.master,2*i+1,r,segs[i].name,self.textFont,self.headercols[2*i+1],k)
					# arguments on event : projects data base, segment name(column), project name(row)
					def handler(event, projects=self.projects, seg=segs[i].name, prj=p):
						return self.entryhandler(prj,seg,None,None)
					w.bind(sequence="<Button-1>",func=handler)
					l3=Button(self.master,image=self.gifright)
					l3.grid(row=r,column=2*i+2)
					def handlerw(event, projects=self.projects,seg=segs[i].name, prj=p):
						return self.nextwindow(seg,prj,None,None)
					l3.bind("<Button-1>", func=handlerw)
					self.master.create_image(r,2*i+2, image=self.gifright)
					txt = 'Start=0x%x End=0x%x' % (segs[i].start_address,segs[i].end_address)
					# row 2 for same project
					LabelWidget(self.master,2*i+1,r+1,txt, self.textFont,"black",just="left",w=self.headercols[2*i+2],which=k)
				r += 2
				if r == 2*(len(self.rowList)-1):
					k = LAST
		else:
			# all tables, besides PROJECT
			self.setHeader()
			if self.currentName == None:
				row_offset=0
				# display the content of the columns for every row(table)
				for i in range(self.currentto-1):
					row_offset=self.doLines(i,row_offset,MIDDLE)
				self.doLines(self.currentto-1,row_offset,LAST)
			else: # specific line
				self.doLines(0,0,LAST)
		if not self.all:
			# if in main window - store it - for next/previous
			self.frames[self.name] = (self.master,self.lbl)
		self.lbl.pack()
		self.master.pack(fill=BOTH,expand=True)

	def setHeader(self):
		c = len(self.headernames)
		# put headers columns
		for r in range(c):
			LabelWidget(self.master,r,0,self.headernames[r],self.textFontHeader,"brown",w=self.headercols[r],which=FIRST)
		# create next button
		if self.buttons:
			# put in your own gif file here, may need to add full path
			self.down=Button(self.master,image=self.gifdown)
			self.down.grid(row=0,column=c)
			self.down.bind("<Button-1>", self.nexttable)
			self.master.create_image(0,c, image=self.gifdown)
			self.up = None
	
	def prevtable(self,event):
		'''
		display the previous CHUNK of rows in the table
		if they exist
		'''
		# if already displayed, at least, one chunk
		if self.currentto > CHUNK: # go up
			self.currentto = self.currentfrom
			# check we reached the beginning of the table
			if self.currentfrom < CHUNK:
				self.currentfrom = 0
			else:
				self.currentfrom = self.currentfrom - CHUNK
			# destroy all the widgets of the current display
			for w in self.widgetsToDestoy:
				w.destroy()
			self.widgetsToDestoy = []
			# write the previous chunk
			row_offset=0
			for i in range(self.currentfrom,self.currentto-1):
				row_offset=self.doLines(i,row_offset,MIDDLE)
			self.doLines(self.currentto-1,row_offset,LAST)
			if self.currentfrom == 0 and self.up:
				# destroy prev button
				self.up.destroy()
				self.up = None
			# create the next button
			if self.buttons and not self.down:
				c = len(self.headernames)
				self.down=Button(self.master,image=self.gifdown)
				self.down.grid(row=0,column=c)
				self.down.bind("<Button-1>", self.nexttable)
				self.master.create_image(0,c, image=self.gifdown)
				self.master.pack(fill=BOTH,expand=True)

	def nexttable(self,event):
		'''
		display the next CHUNK of rows in the table
		if they exist
		'''
		# check if there is any down
		if len(self.tableList) > self.currentto: # go down
			# destroy all the widgets of the current display
			for w in self.widgetsToDestoy:
				w.destroy()
			self.widgetsToDestoy = []
			self.currentfrom = self.currentto
			# check if we reached the end of the table
			if len(self.tableList) > CHUNK + self.currentto:
				self.currentto = self.currentto + CHUNK
			else:
				self.currentto = len(self.tableList)
			# display the next chunk of tables
			row_offset=0
			for i in range(self.currentfrom,self.currentto-1):
				row_offset=self.doLines(i,row_offset,MIDDLE)
			self.doLines(self.currentto-1,row_offset,LAST)
			if self.currentto == len(self.tableList) and self.down:
				# destroy prev button
				self.down.destroy()
				self.down = None
			# create the prev button
			if self.buttons and not self.up:
				c = len(self.headernames)
				self.up=Button(self.master,image=self.gifup)
				self.up.grid(row=0,column=c+1)
				self.up.bind("<Button-1>", self.prevtable)
				self.master.create_image(0,c+1, image=self.gifup)
				self.master.pack(fill=BOTH,expand=True)

	def setOneLink(self,i,name,which,regular):
		'''
		name - value of the first column
		'''
		if not regular:
			w=LabelWidget(self.master,0,i+1,name,self.textFont,"blue",just='left',w=self.headercols[0],which=which)
			if self.name == "TABLE":
				def handler(event, prj=self.projectName,seg=self.segmentName,tab=name,row=None):
					return self.entryhandler(prj,seg,tab,row)
				w.bind(sequence="<Button-1>",func=handler )
			else: # entry
				def handler(event, prj=self.projectName,seg=self.segmentName,tab=self.tableName,row=name):
					return self.entryhandler(prj,seg,tab,row)
				w.bind(sequence="<Button-1>",func=handler )
		else: # name is not a link futher
			w=LabelWidget(self.master,0,i+1,name,self.textFont,"black",just='left',w=self.headercols[0],which=which)
		if not self.all : 
			self.widgetsToDestoy.append(w)

	def setOneLine(self,i,ent,which):
		'''
		ent - list of values
		'''
		for j in range(1,len(ent)): # the 0 entry was displayed by setOneLink
			if ent[j]:
				w=LabelWidget(self.master,j,i+1,ent[j],self.textFont,"black",w=self.headercols[j],which=which)
			else:
				w=LabelWidget(self.master,j,i+1,'None',self.textFont,"black",w=self.headercols[j],which=which)
			if not self.all:
				self.widgetsToDestoy.append(w)
		if self.buttonw: # the table has a 'right' button
			self.right=Button(self.master,image=self.gifright)
			self.right.grid(row=i+1,column=len(ent))
			def handlerw(event, seg=self.segmentName, prj=self.projectName, tab=self.tableName, row=ent[0]):
				return self.nextwindow(seg,prj,tab,row)
			self.right.bind("<Button-1>", func=handlerw)
			self.master.create_image(i+1, 2, image=self.gifright)

	def nextwindow(self,seg,prj,tab,row):
		'''
		creates a new window when the 'right' button is clicked
		from PROJECT to display all the tables
		from ENTRY to display all fields
		'''
		top=Toplevel(master=self.parent,width=wpixel,height=hpixel/4)
		top.frames = self.frames
		top.projects = self.projects
		if not tab and not row: # I am in projects
			top.title = prj+'->'+seg
		else:
			if tab:
				top.title(tab+'->'+row)
			else:
				top.title('->'+row)
		def nextwindow_handler(name=top.title):
			return self.quitwindow(name)
		top.protocol("WM_DELETE_WINDOW", nextwindow_handler)
		self.windowsList.append(top)
		if self.name == "ENTRY":
			displayFields(top,prj,seg,tab,row,all=True)
		elif self.name == "PROJECT":
			displayTables(top,prj,seg,None,all=True)

	def quitwindow(self,name):
		'''
		close window handler (all the new ones) - not the main
		closeing the main - will close all its children
		'''
	 	for topw in self.windowsList:
	 		if name == topw.title:
	 			self.windowsList.remove(topw)
	 			topw.destroy()
	 			break

	def entryhandler(self,p,s,t,e):
		'''
		handler for click on 'blue' name
		clear all the children widgets
		display the new ones according to parameters
		'''
		if self.name == "PROJECT":
			self.frames["TABLE"][0].destroy()
			self.frames["TABLE"][1].destroy()
			displayTables(self.frames["MAIN"][0],p,s,None)
			t = None
	 	if self.name == "TABLE" or self.name == "PROJECT":
	 		self.frames["ENTRY"][0].destroy()
	 		self.frames["ENTRY"][1].destroy()
	 		displayEntries(self.frames["MAIN"][0],p,s,t,None)
	 		e = None
	 	self.frames["FIELD"][0].destroy()
	 	self.frames["FIELD"][1].destroy()
	 	try:
	 		# if the entry has fields, create first field in entry table
	 		displayFields(self.frames["MAIN"][0],p,s,t,e)
	 	except IndexError:
	 		pass

class displaySelected(displayTable):
	'''
	class inherits displayTable - to display only the found tables 
	'''
	def __init__(self,parent,project,segment,table,selectedList,lookfor,all=False):
		displayTable.__init__(self,parent,project,segment,"TABLE",table=table,all=all)
		headercols = [self.maxn+6,14,16,self.maxn+6]
		headers = ['Name','Base','Length (bytes)','Union']
		self.config(headercols=headercols,headernames=headers,callbackValues=self.getValues)
		title = "Result of the search '"+lookfor+"' tables"
		self.master = Canvas(parent,width=wpixel,bd=0,bg="white")
		self.lbl=TitleWidget(parent,text=title)
		self.setHeader()
		row_offset = 1
		for i in selectedList:
			getvalues = self.callbackValues(i,-1)
			k = getvalues[0]			# for fields in an union, = -1 end of the union fields
			values = getvalues[1]
			# in this kind of window the selected tables might be open futher
			w=LabelWidget(self.master,0,row_offset+1,values[0],self.textFont,"blue",just='left',w=self.headercols[0],which=MIDDLE)
			def handler(event, parent=parent,prj=self.projectName,seg=self.segmentName,tab=values[0],row=None):
				return self.entryhandler_1(parent,prj,seg,tab,row)
			w.bind(sequence="<Button-1>",func=handler )
			self.setOneLine(row_offset,values,MIDDLE)
			row_offset += 1
		self.lbl.pack()
		self.master.pack(fill=BOTH,expand=True)
		displayEntries(parent,self.projectName,self.segmentName,self.tableName,None)
		displayFields(parent,self.projectName,self.segmentName,self.tableName,None)

	def getValues(self,tab,k):
		'''
		bring the table's parameters to be displayed - check for the table in required project or DEFAULT
		'''
		temp = []
		if tab.prefix != "":
			tname = tab.prefix+tab.name
		else:
			tname = tab.name
		temp.append(tname)
		temp.append(tab.base)
		l = []
		if self.projectName in tab.length.keys():
			l = tab.length[self.projectName]
		elif 'DEFAULT' in tab.length:
			l = tab.length['DEFAULT']
		txt = '%d  (0x%x)' % (l[0][1],l[0][1])
		temp.append(txt)
		if tab.union:
			temp.append(tab.union)
		else:
			temp.append('None')
		return (k,temp)

	def entryhandler_1(self,parent,p,s,t,e):
		'''
		handler to open a table link
		'''
		parent.frames["ENTRY"][0].destroy()
		parent.frames["ENTRY"][1].destroy()
		displayEntries(parent.frames["MAIN"][0],p,s,t,None)
		e = None
		parent.frames["FIELD"][0].destroy()
		parent.frames["FIELD"][1].destroy()
		try:
			# if the entry has fields, create first field in entry table
			displayFields(parent.frames["MAIN"][0],p,s,t,e)
		except IndexError:
			pass

class displayTables(displayTable):
	'''
	class to display TABLES
	'''
	def __init__(self,parent,project,segment,table,all=False):
		displayTable.__init__(self,parent,project,segment,"TABLE",table=table,all=all)
		headercols = [self.maxn+6,14,16,self.maxn+6]
		headers = ['Name','Base','Length (bytes)','Union']
		self.config(headercols=headercols,headernames=headers,callbackValues=self.getValues)
		if not all:
			self.doDisplay()
		else: # display all tables - no link , in a new window
			lbl=TitleWidget(parent,text=self.title)
			lbl.pack(side=TOP,fill=BOTH)
			self.canvas = Canvas(parent, width=wpixel,borderwidth=0, background="#ffffff")
			self.master = Frame(self.canvas, width=wpixel,background="#ffffff")
			self.vsb = Scrollbar(parent, orient="vertical", command=self.canvas.yview)
			self.canvas.configure(yscrollcommand=self.vsb.set)
			self.vsb.pack(side="right", fill="y")
			self.canvas.pack(side="left", fill="both", expand=True)
			self.canvas.create_window((0,0), window=self.master, anchor="nw", tags="self.master")
			self.canvas.configure(scrollregion=(0,0,wpixel,len(self.tableList)*60))
			self.setHeader()
			## display the content of the columns for every row(table)
			for i in range(self.currentto-1):
				self.doLines(i,0,MIDDLE)
			self.doLines(self.currentto-1,0,LAST)
			self.pack(fill=BOTH,expand=True)
			self.canvas.focus_set()
			self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
			self.master.bind_all("<Control-f>",self._ctrlf)
			self.canvas.update_idletasks()

	def getValues(self,tab,k):
		temp = []
		if tab.prefix != "":
			tname = tab.prefix+tab.name
		else:
			tname = tab.name
		temp.append(tname)
		temp.append(tab.base)
		l = []
		if self.projectName in tab.length.keys():
			l = tab.length[self.projectName]
		elif 'DEFAULT' in tab.length:
			l = tab.length['DEFAULT']
		txt = '%d  (0x%x)' % (l[0][1],l[0][1])
		temp.append(txt)
		if tab.union:
			temp.append(tab.union)
		else:
			temp.append('None')
		return (k,temp)

	def _on_mousewheel(self, event):
		# -120 is down ; +120 is up
		self.canvas.yview_scroll(-1*(event.delta/120), "units")

	def _ctrlf(self,event):
		'''
		handler for ctrl-f = find function
		'''
		self.lookfor = StringVar()
		self.we = Entry(self.master,width=self.headercols[0],bg="yellow",textvariable=self.lookfor)
		self.we.bind("<Return>",self.look_for_tables)
		self.we.grid(row=1,column=3)
		self.we.focus_set()

	def look_for_tables(self,event):
		'''
		actually does the serach
		'''
		self.lookfor = self.we.get()
		tofind = self.lookfor.upper()
		star = 0
		found = []
		if tofind.startswith('*'):
			tofind = tofind[1:]
			star = 1
		if tofind.endswith('*'):
			tofind = tofind[:len(tofind)-1]
			if star == 1:
				star = 3
			else:
				star = 2
		for i in self.tableList:
			j = i
			iname = i.name.upper()
			if star == 1:
				if tofind == iname[len(iname)-len(tofind):]:
					found.append(j)
			elif star == 2:
				if tofind == iname[:len(tofind)]:
					found.append(j)
			elif star == 3:
				if tofind in iname:
					found.append(j)
			else:
				if tofind == iname:
					found.append(j)
		if len(found) == 0:
			print "No table with "+self.lookfor+" was found"
		else:
			# display only the found tables
			self.we.destroy()
			top=Toplevel(master=self.master,width=wpixel,height=hpixel/4)
			top.frames = {}
			top.frames["MAIN"]=(top,None)
			top.projects = self.projects
			top.title(self.lookfor)
			def secwindow_handler(name=top.title):
				return self.quitwindow(name)
			top.protocol("WM_DELETE_WINDOW", secwindow_handler)
			self.windowsList.append(top)
			displaySelected(top,self.projectName,self.segmentName,found[0].name,found,self.lookfor)

class displayEntries(displayTable):
	'''
	class to display ENTRY table
	'''
	def __init__(self,parent,project,segment,table,entry):
		displayTable.__init__(self,parent,project,segment,"ENTRY",table=table,entry=entry,buttonw=True)
		headercols = [self.maxn+6,16]
		headers = ['Name','Length (bytes)']
		self.config(headercols=headercols,headernames=headers,callbackValues=self.getValues)
		self.doDisplay()

	def getValues(self,tab,k):
		return (k,[tab.name,str(tab.length)])

class displayFields(displayTable):
	'''
	class to display FIELD table
	'''
	def __init__(self,parent,project,segment,table,entry,all=False):
		displayTable.__init__(self,parent,project,segment,"FIELD",table=table,entry=entry,all=all)
		headercols = [4,self.maxn+6,10,10,10,10,10,self.maxn,self.maxn,self.maxn]
		headers = ['Ind','Name','Word','Byte','From','Size(bits)','ArraySize','Union','SubUnion','Enum']
		self.config(headercols=headercols,headernames=headers,callbackValues=self.getValues)
		self.doDisplay()
	
	def getValues(self,ent,k):
		if isinstance(ent,fwField) and k == -1:
			if not ent.codedef:
				return (-1,[str(ent.ind),ent.name,str(ent.word),str(ent.hword),str(ent.frombit),str(ent.bits),str(ent.length),'None','None','None'])
			return (-1,[str(ent.ind),ent.name,str(ent.word),str(ent.hword),str(ent.frombit),str(ent.bits),str(ent.length),'None','None',ent.codedef])
		else: # for union fields
			if k < len(ent.fields): 
				if k == -1:
					k = 0
				enti = ent.fields[k]
				if not enti.codedef:
					return (k+1,[str(enti.ind),enti.name,str(enti.word),str(enti.hword),str(enti.frombit),str(enti.bits),str(enti.length),ent.name,enti.subunion,'None'])
				return (k+1,[str(enti.ind),enti.name,str(enti.word),str(enti.hword),str(enti.frombit),str(enti.bits),str(enti.length),ent.name,enti.subunion,enti.codedef])
			else:
				return (-1,[])

class displayProjects(displayTable):
	'''
	class to display PROJECTS table
	'''
	def __init__(self,parent,project,segment):
		displayTable.__init__(self,parent,project,segment,"PROJECT",buttonw=True)
		maxseg = 0 		# maximum number of segments = number of columns
		maxsegn = 0 	# maximum length of segment name
		maxsegt = 0		# maximum length of text information
		for r in self.rowList.values():
			if len(r) > maxseg:
				maxseg = len(r)
			for s in r:
				if len(s.name) > maxsegn:
					maxsegn = len(s.name)
				txt = 'Start=0x%x End=0x%x' % (s.start_address,s.end_address)
				if len(txt) > maxsegt:
					maxsegt = len(txt)
		headercols = [self.maxn+4]
		headers = ['Project','Segments']
		for i in range(maxseg):
			headercols.append(maxsegn+4)    # segment name
			headercols.append(maxsegt+4)	# segment text
		self.config(headercols=headercols,headernames=headers)
		self.doDisplay()

def LabelWidget(master, col, row, text, textfont, foreground, just = 'center',n=1, w=12,which=MIDDLE,r=1):
	'''
	create a read only entry - looks as a label
	in a grid
	'''
	if just == 'left':
		titletext=text.ljust(w)
	else:
		titletext=text.center(w)
	e = Text(master,bg="white")
	e.insert(END,titletext)
	if which==FIRST: # first row
		e.config(relief=GROOVE,font=textfont,fg=foreground,width=w,height=r,state=DISABLED)
	elif which==LAST: # last row
		e.config(relief=RIDGE,font=textfont,fg=foreground,width=w,height=r,state=DISABLED)
	else:
		e.config(relief=SOLID,font=textfont,fg=foreground,width=w,height=r,state=DISABLED)
	e.grid(column=col, row=row, columnspan=n,rowspan=r)
	return e

def TitleWidget(master,text):
	'''
	create a read only text - looks as a label, in a grid
	'''
	l=Label(master,text="\n"+text+"\n",font=titleFont,fg='brown',bg="white")
	return l

def LabelWidget2(master, col, row, first, textfont,w,which):
	'''
	create a text - looks as a link concatenated in a grid
	'''
	t = Text(master,bg="white")
	t.insert(END,first)
	t.tag_add('gotoline',"1.0","1."+str(len(first)+1))
	t.tag_configure('gotoline',foreground='blue')
	if which == LAST:
		t.config(relief=RIDGE, font=textfont,fg='black',
			padx=1, pady=1,width=w,height=1,
			state=DISABLED)
	else:
		t.config(relief=SOLID, font=textfont,fg='black',
			padx=1, pady=1,width=w,height=1,
			state=DISABLED)
	t.grid(column=col, row=row)
	return t

def setFontSize(total,widthPixels):
	'''
	take main frame parameters - in pixels
	calculates the size of the char to fit the width
	return a tuple (width, height)
	'''
	text = "x" * total 
	mysize = myFont
	font = tkFont.Font(family="Arial", size=mysize)
	wd = font.measure(text)
	while wd >= wpixel-20:
		mysize -= myFont/6
		font = tkFont.Font(family="Arial", size=mysize)
		wd = font.measure(text)
	return mysize

class mainDisplay(Frame):
	'''
	main GUI window
	'''
	def __init__(self,top,projects,p,s,t,e):
		global wpixel,hpixel,CHUNK,wchars
		Frame.__init__(self, top,bg="white")
		self.frames = {} # key = "MAIN","PROJECT","TABLE","ENTRY","FIELD" ; value = (tuple of main widget, label widget)
		self.frames["MAIN"] = (self,None)
		self.projects = projects
		self.p = p
		self.s = s
		self.t = t
		self.e = e
		# each entry in list is a table; every tuple is (frame, class)
		wpixel = top.winfo_screenwidth()*0.85 # maximum width in pixels
		hpixel = top.winfo_screenheight()*0.8 # maximum high in pixels
		font = tkFont.Font(family="Arial", size=myFont)
		wcol = font.measure('x') 		      # number of pixels of char 
		wchars = int((wpixel-20)/wcol)		  # number of chars
		self.bind("<Configure>", self.resize)
		self.populate()

	def populate(self):
		# display projects, returns project frame
		displayProjects(self,self.p,self.s)
		# display tables, returns table frame
		displayTables(self,self.p,self.s,self.t)
		# display entries, return entry frame 
		displayEntries(self,self.p,self.s,self.t,self.e)
		# display fields return field frame 
		displayFields(self,self.p,self.s,self.t,self.e)

	def resize(self,event):
		global wpixel,hpixel,wchars
		wpixel = event.width*0.85
		hpixel = event.height*0.8
		font = tkFont.Font(family="Arial", size=myFont)
		wcol = font.measure('x') 		      # number of pixels of char 
		wchars = int((wpixel-20)/wcol)		  # number of chars

class GUIapp():
	def __init__(self,modify,projects,segments,tables_entries,p,s,t,e,validClbk,genHClbk,genCCblk,argv1):
		global modifyFields
		root = Tk()
		self.projects = projects
		self.segments = segments
		self.tabsentries = tables_entries
		self.orig = argv1
		modifyFields = modify
		myframe = Frame(root)
		# buttons handlers
		def handler_validate(event):
			err = validClbk(self.segments,self.projects)
			if err:
				tkMessageBox.showinfo("Validation results", "Data Base has no error !!!")
			else:
				tkMessageBox.showinfo("Validation results", "Data Base has errors.\nSee them in the command line window !!!")
			return 
		def handler_gen_h(event):
			pathnamet = genHClbk(self.segments,self.projects,self.tabsentries,["-f"],self.orig)
			showInfo(pathnamet,True)
			return
		def handler_gen_c(event):
			pathnamet = genCCblk(self.segments,self.projects,self.tabsentries,["-f"],self.orig)
			showInfo(pathnamet,True)
			return
		def handler_gen_h_inplace(event):
			pathnamet = genHClbk(self.segments,self.projects,self.tabsentries,[],self.orig)
			showInfo(pathnamet,True)
			return
		def handler_gen_c_inplace(event):
			pathnamet = genCCblk(self.segments,self.projects,self.tabsentries,[],self.orig)
			showInfo(pathnamet,True)
			return
		if modify:
			def handler_saveas(event):
				txt=os.path.dirname(self.orig)+'/'
				pathname=tkFileDialog.asksaveasfilename(defaultextension='.xml',initialdir=txt,filetypes=[("All files", "*.*")],parent=root)
				if pathname:
					self.saveasfile(pathname)
				bsaveas.config(bg="yellow")
				return
			bsaveas = Button(myframe,text="Save as ...",bg="yellow")
			bsaveas.bind("<Button-1>",func=handler_saveas)
			bsaveas.grid(row=0,column=6)
		bv = Button(myframe,text="Validate",bg="yellow")
		bv.bind("<Button-1>",func=handler_validate)
		bg = Button(myframe,text="Generate h",bg="yellow")
		bg.bind("<Button-1>",func=handler_gen_h)
		bc = Button(myframe,text="Generate c",bg="yellow")
		bc.bind("<Button-1>",func=handler_gen_c)
		bginplace = Button(myframe,text="Generate h in place",bg="yellow")
		bginplace.bind("<Button-1>",func=handler_gen_h_inplace)
		bcinplace = Button(myframe,text="Generate c in place",bg="yellow")
		bcinplace.bind("<Button-1>",func=handler_gen_c_inplace)
		bv.grid(row=0,column=1)
		bg.grid(row=0,column=2)
		bginplace.grid(row=0,column=3)
		bc.grid(row=0,column=4)
		bcinplace.grid(row=0,column=5)
		myframe.pack()

		mainDisplay(root,projects,p,s,t,e).pack(fill=BOTH,expand=True)
		# main loop
		root.mainloop()

	def saveasfile(self,filename):
		'''
		save database into another file
		'''
		def setState(s,l):
			if l == '</entry>':
				return 1
			elif l == '</data_segment>' and s >= 0:
				return -1
			return s

		def entry_in_changes(l):
			'''
			parse a read entry line from the original file
			look for name and project list - if exist, otherwise, project is set to DEFAULT
			'''
			i = l.find('name')
			l1 = line[i+len('name'):]
			i = l1.find('=')
			l1 = l1[i+1:]
			j = l1.find(' ')
			if j==-1:
				j = l1.find('>')
			name = l1[:j].strip()
			if name.startswith('"'):
				name = name[1:len(name)-1] 
			i = l.find('project')
			if i >=0:
				l1 = l[i+len('project'):]
				i = l1.find('=')
				l1 = l1[i+1:]
				j = l1.find(' ')
				if j == -1:
					j = l1.find('>')
				project = l1[:j]
			else:
				project = 'DEFAULT'
			if project.startswith('"'):
				project = project[1:len(project)-1]
			# check if the current ENTRY defintion has been changed
			if name in fieldChanges.keys():
				if project == 'DEFAULT':
					return (name,[project])
				else:
					# the ENTRY has projects - check if the entry for the specific project has been changed
					projdict = fieldChanges[name]
					projlist = projdict.keys()    	# list of projects of the given entry which have changes
					projectlist = project.split('+')	# list of projects of the entry from original file
					tmp = [x for x in projlist if x in projectlist]
					if len(tmp) > 0: # some common project
						return (name,tmp)
			return None

		def formatField(f,union):
			'''
			format a field line for the XML file
			<field name="error_type" size="9" is_array="true" array_num_entries="32" sub_union="1" codedef="CPU_REASON"></field>
			'''
			lo = '\t\t\t'
			if union:
				lo += '\t'
			lo += '<field name='+f.name
			lo += ' size="'+str(f.bits)+'"'
			if f.length > 1:
				lo += ' is_array="true" array_num_entries="'+str(f.length)+'"'
			if f.subunion:
				lo += ' subunion="'+f.subunion+'"'
			if f.codedef:
				lo += ' codedef="'+f.codedef+'"'
			lo += '></field>'
			return lo

		try:
			fi = open(self.orig,"r")
			fo = open(filename,"w")
			print fieldChanges
			state=0
			name = None
			nameprojects = None
			ignore = False
			# read the original file
			for liner in fi:
				line = liner.strip()
				# ignore is set for an entry which has changes
				# all the fields of the entry are read and ignored
				# until entry finished
				if ignore:
					# read and ignore all entry's fields
					if line == '</entry>':
						ignore = False 
						state = 1
						fo.write(liner)
					continue
				if state == -1:
					# we already did the 'entries' section - all the other lines from the original file
					# may be coppied as is
					fo.write(liner)
					continue
				else:
					# look for 'entries' section
					if state == 0:
						if line == '<data_segment name="entries">':
							state = 1
					elif state == 1:
						# we are into 'entries' section, looking for entries
						if line.startswith('<entry'):
							nametp = entry_in_changes(line)
							# check for changes
							if nametp:
								name = nametp[0]
								nameprojects = nametp[1]
								state = 2
								# the entry has changes
							else:
								state = setState(state,line)
						else:
							state = setState(state,line)
					elif state == 2:
						# look for fields of the entry
						if line.startswith('<field name'):
							projdict = fieldChanges[name]
							p = nameprojects[0]
							# according to the project with changes
							# take segment and table
							if p == 'DEFAULT':
								seg_tab = projdict[projdict.keys()[0]]
							else:
								seg_tab = projdict[p]
							# go to entry's block
							tmpp = [x for x in self.projects if x.name == p]
							tmps = [x for x in tmpp[0].segments if x.name == seg_tab[0]]
							tmpt = [x for x in tmps[0].tables_unified if x.name == seg_tab[1]]
							tmpe = [x for x in tmpt[0].entries if x.name == name]
							ignore = True # read and drop all fields of this entry
							# run along specific data base and writes fields
							for f in tmpe[0].fields:
								if not f.parent: # regular field
									lo = formatField(f,False)
									fo.write(lo+'\n')
								else: # union
									txt = '\t\t\t<union_field union_name="%s" union_size="%d">' % (f.name,f.bits)
									fo.write(txt+'\n')
									# run for all union's fields
									for fu in f.fields:
										lo = formatField(fu,True)
										fo.write(lo+'\n')
									fo.write('\t\t\t</union_field>\n')
							continue
						else:
							state = setState(state,line)
				fo.write(liner)
			fi.close()
			fo.close()
			tkMessageBox.showinfo("Info", "File : "+ filename +" is saved")
		except IOError:
			print "Cannot open "+filename+" or "+self.orig

def showInfo(pathname_tuple,gui):
	pathname = pathname_tuple[0]
	errlist = pathname_tuple[1]
	if len(errlist) > 0:
		for err in errlist:
			print err
	if gui:
		if len(errlist) > 0:
			tkMessageBox.showinfo("Info", "Files are generated in '"+pathname+"'\n\nData Base has errors.\nSee them in the command line window !!!")
		else:
			tkMessageBox.showinfo("Info", "Files are generated in '"+pathname+"'")
	else:
		print "Files are generated in '"+pathname+"'"

