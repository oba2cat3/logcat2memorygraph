'''
Copyright 2014 Oren Barad

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

'''

'''
Oren Barad

This Script requires python 2.7 at minimum, and was written on a 64bit Windows 7.
it needs a lib called xlswriter - avilable from http://xlsxwriter.readthedocs.org/#
'''

import codecs
from datetime import datetime
import xlsxwriter
import os
import sys
import datetime
import re
import time
import traceback




'''
You can setup a specific event series in this script. 
'''
'''
-------------configuration setup start----------
'''
# use milisecound timestamps epoch, or the time from the logline.
timestamp=False
# here you can setup a specific event series - setup the series name, log to look for, location on the MS axis, and the color of the diamod
#         series name , simple filter , defualt value, color
custom_events = [("webview", "nativeDestroy view" , "50" , '#FF0000'), 
				("start" ,"byte allocation", "60" , '#0000FF')]

# setup the input and output files for the script.
				
in_file=r'interesting_log.txt'
out_file = r'raw_vm.xlsx'
'''
-------------configuration setup end----------
'''
				
timestamp_regex = ".*?(\d\d-\d\d \d\d:\d\d:\d\d)\.(\d\d\d).*"
time_regex = ".*?\d\d-\d\d (\d\d:\d\d:\d\d)\.(\d\d\d).*"
regex_for_dalvik_heap_clamp = ".*Clamp target GC heap from (\d+.\d\d\d)MB to (\d+.\d\d\d)MB.*"
regex_for_dalvik_heap_grow = ".*Grow heap \(frag case\) to (\d+.\d\d\d)MB for (\d+)\-byte allocation.*"

regex_for_dalvik_vm_gc_for_alloc = ".*GC_FOR_ALLOC freed [<]{0,1}(\d+)K, \d+?% free (\d+)K\/(\d+)K, paused (\d+)ms, total (\d+)ms.*"
regex_for_dalvik_vm_gc_explicit = ".*GC_EXPLICIT freed [<]{0,1}(\d+)K, \d+?% free (\d+)K\/(\d+)K, paused (\d+)ms\+(\d+)ms, total (\d+)ms.*"
regex_for_dalvik_vm_gc_concurrent = ".*GC_CONCURRENT freed [<]{0,1}(\d+)K, \d+?% free (\d+)K\/(\d+)K, paused (\d+)ms\+(\d+)ms, total (\d+)ms.*"
regex_for_dalvik_vm_gc_before_oom = ".*GC_BEFORE_OOM freed [<]{0,1}(\d+)K, \d+?% free (\d+)K\/(\d+)K, paused (\d+)ms, total (\d+)ms.*"
regex_for_dalvik_vm_gc_wait_for_concurent = ".*WAIT_FOR_CONCURRENT_GC blocked (\d+)ms.*"
regex_for_pid = ".*\((\d+)\)\:.*"
col_blue = '#4F81DB'
col_red='#C0504D'
col_green='#9BBB59'
col_purple='#8064A2'
filter_regex = "[^a-zA-Z0-9\^\-;:\<\>\\\/,\"\'\`=._\]\[\(\)\*\&\^\%\$\#\@\!\~\?\t ]" 

def get_timestamp(str):
	m = re.match(timestamp_regex, str)
	tstamp = m.group(1) # 05-29 14:59:09.771 
#	print (tstamp)
	my_time = datetime.datetime.strptime(tstamp, "%m-%d %H:%M:%S")
	my_time = my_time.replace(year=2014)
	tmp_tstamp = time.mktime(my_time.timetuple())*1000 + int (m.group(2))
	tmp_tstamp=tmp_tstamp%100000000
	return "%.0f" % tmp_tstamp

def get_time(str):
	m = re.match(time_regex, str)
	tstamp = m.group(1) # 05-29 14:59:09.771 
	return tstamp
	
	
def get_gc_explicit(mystr):
	m = re.match(regex_for_dalvik_vm_gc_explicit, mystr)
	res = ["exp" , m.group(1),m.group(2),m.group(3),m.group(4),m.group(5),str(int(m.group(4)) + int(m.group(5))),m.group(6)] # free,used heap,max heap,first pause time,secound pause time, total time
	return res	
	
def get_gc_concurrent(mystr):
	m = re.match(regex_for_dalvik_vm_gc_concurrent, mystr)
	res = ["con" , m.group(1),m.group(2),m.group(3),m.group(4),m.group(5),str(int(m.group(4)) + int(m.group(5))),m.group(6)] # free,used heap,max heap,first pause time,secound pause time, total time
	return res

def get_gc_alloc(mystr):
	m = re.match(regex_for_dalvik_vm_gc_for_alloc, mystr)
	res = ["alloc" , m.group(1),m.group(2),m.group(3),m.group(4),"",m.group(4),m.group(5)] # free,used heap,max heap,pause time, total time
	return res

def get_gc_before_oom(mystr):
	m = re.match(regex_for_dalvik_vm_gc_before_oom, mystr)
	res = ["oom" , m.group(1),m.group(2),m.group(3),m.group(4),"",m.group(4),m.group(5)] # free,used heap,max heap,pause time, total time
	return res

def get_gc_concurrent_wait(mystr):
	# regex_for_dalvik_vm_gc_wait_for_concurent
	m = re.match(regex_for_dalvik_vm_gc_wait_for_concurent, mystr)
	res = ["con_wait" ,"","","","","","", m.group(1)] # pause time
	return res
	
def get_pid(mystr):
	m = re.match(regex_for_pid, mystr)
	res=None
	if (m!=None):
		res = m.group(1)
	return res
	
def grow_heap(mystr):
	m = re.match(regex_for_dalvik_heap_grow, mystr)
	dat=str(int(1024*float(m.group(1))))
	res = ["heap_grow" ,"",dat,"","","","",""] # pause time
	return res

def clamp_heap(mystr):
	
	m = re.match(regex_for_dalvik_heap_clamp, mystr)
	dat=str(int(1024*float(m.group(1))))
	res = ["heap_clamp" ,"","",dat,"","","",""] # pause time
	return res	
	
def get_custom_event(str):
	res=()
	return res


def write_to_workbook(pid ,data, full_log_holder, workbook, cust_events=[] , sect_format={}):
	if (len(data)<50):
		return
	
	worksheet = workbook.add_worksheet(pid)
	headers1 = ["time" , "pid" , "event" , "freed" , "current heap" , "max heap" , "p", "p1", "ui pause time" , "total pause"] 
	for h in cust_events:
		headers1.append(h[0])
	headers1.append("log line")
	x=0
	for header in headers1:
		worksheet.write(0,x,header ,sect_format["head"] )
		x+=1
	
	y=0
	for row in data:
		x=0
		y+=1
		for d in row:
			if (d!=None):
				if (re.match("^\d+$" , d)):
					worksheet.write_number(y,x,int(d))
				else:
					worksheet.write(y,x,d)
			x+=1
			
	'''
	At this point - define the chart for the data. the timestamps are at column A, the max heap, and current heap are at column E and F.
	UI pause is at I and total pause is at J. the headers are on row 1, and the data is in row 2 to y
	'''
	
	chart = workbook.add_chart({'type': 'line'})

	# Add a series to the chart.
	# primary y axis series:
	chart.add_series({'name': ("=\'%s\'!$E$1" % pid) , 'categories': ("=\'%s\'!$A$2:$A$%s" % (pid,y)), 'values': ("=\'%s\'!$E$2:$E$%s" % (pid,y)),'line':   {'color': col_blue }})
	chart.add_series({'name': ("=\'%s\'!$F$1" % pid) ,'categories':  ("=\'%s\'!$A$2:$A$%s" % (pid,y)), 'values': ("=\'%s\'!$F$2:$F$%s" % (pid,y)), 'line':   {'color': col_red}})
	# secoundry y axis series:
	chart.add_series({'name': ("=\'%s\'!$I$1"% pid) ,'categories': ("=\'%s\'!$A$2:$A$%s" % (pid,y)), 'values': ("=\'%s\'!$I$2:$I$%s" % (pid,y)),'y2_axis': True, 'marker': {'type': 'square'},'line':   {'none': True,'color': col_green}})
	chart.add_series({'name': ("=\'%s\'!$J$1"% pid) ,'categories': ("=\'%s\'!$A$2:$A$%s" % (pid,y)), 'values': ("=\'%s\'!$J$2:$J$%s" % (pid,y)),'y2_axis': True, 'marker': {'type': 'short_dash','color': col_purple},'line':   {'none': True}})
	
	letter = 'K'
	for c_event in custom_events:
		name = ("=\'%s\'!$%s$1"% (pid,letter))
		values = ("=\'%s\'!$%s$2:$%s$%s" % (pid,letter,letter,y))
		chart.add_series({'name': name ,'categories': ("=\'%s\'!$A$2:$A$%s" % (pid,y)), 'values': values,'y2_axis': True, 'marker': {'type': 'diamond','fill':   {'color': c_event[3]} , 'size' : '10'},'line':   {'none': True}})
		letter = chr(ord(letter)+1)
	# Insert the chart into the worksheet.
	chart.set_x_axis({'name': 'dalvikvm event timestamps'})
	chart.set_y_axis({'name': 'heap size in KB' , 'position' : 'top'})
	chart.set_y2_axis({'name': 'Time in MS' , 'position' : 'top'})
	chart_loc = ('B3')
	chart.set_size({'width': 1440, 'height': 576})
	chart.show_blanks_as('span')
	chart.set_title({'name': 'Heap size and GC delays' , 'position' : 'top'})
	worksheet.insert_chart(chart_loc, chart)
	
	x=0
	for d in full_log_holder:
		y+=1
		d = re.sub(filter_regex, "", d)
	#	print (d)
		worksheet.write(y,x,d)


	
def main():

	
	log_holder={}
	all_log_holder = {}
	for x in codecs.open(in_file, "r" , "utf-8"):
		x=x.strip()
		pid = get_pid(x)
		if (pid==None):
			continue
		should_print=False
		heap_data=[]
		extra_data = len(custom_events)*[""]
		event_index=0
		for c_event in custom_events:
			if (c_event[1] in x):
				should_print=True
				heap_data= 8*[""]
				heap_data[0]=c_event[0]
				extra_data[event_index] = c_event[2]
			event_index+=1
		# initial filter for dalvik heap vm messages:
		if ("dalvikvm-heap" in x):
			if ("Clamp target" in x):
				should_print=True
				heap_data=clamp_heap(x)
			elif("Grow heap" in x):
				should_print=True
				heap_data=grow_heap(x)
		# initial filter for dalvik heap vm messages:
		elif ("dalvikvm" in x):
			if ("GC_EXPLICIT" in x):
				should_print=True
				heap_data=get_gc_explicit(x)
			elif("GC_FOR_ALLOC" in x):
				heap_data=get_gc_alloc(x)
				should_print=True
			elif("GC_CONCURRENT" in x):
				heap_data=get_gc_concurrent(x)
				should_print=True
			elif("WAIT_FOR_CONCURRENT_GC" in x):
				heap_data=get_gc_concurrent_wait(x)
				should_print=True
		if(should_print):
			tstamp =""
			if (timestamp):
				tstamp = get_timestamp(x)
			else:
				tstamp = get_time(x)
			dat = []
			dat.append(tstamp)
			dat.append(get_pid(x))
			dat.extend(heap_data)
			dat.extend(extra_data)
			dat.append(x)
			
			if (pid not in log_holder):
				
				log_holder[pid]=[dat]
			else:
				log_holder[pid].append(dat)
		else:
			pass
		if (pid not in all_log_holder):
			all_log_holder[pid]=[x]
		else:
			all_log_holder[pid].append(x)
	try:	
		workbook = xlsxwriter.Workbook(out_file)
		head_format = workbook.add_format({'bold': True , 'bg_color' : '#9BBB59'}) #  'font_color': 'red' ,'bg_color' : 'green'
		section_format = {"head" : head_format}
		for pid in log_holder:
			print (pid)
			write_to_workbook(pid, log_holder[pid],all_log_holder[pid], workbook, custom_events ,section_format)
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		print(exc_type)
		print(exc_value)
		print(traceback.format_exc())
	finally:
		workbook.close()
	
if __name__ == "__main__":
	main()
