import re
import datetime
import time

timestamp_regex = ".*?(\d\d-\d\d \d\d:\d\d:\d\d)\.(\d\d\d).*"

def get_timestamp(str):
	m = re.match(timestamp_regex, str)
	tstamp = m.group(1) # 05-29 14:59:09.771 
	print (tstamp)
	my_time = datetime.datetime.strptime(tstamp, "%m-%d %H:%M:%S")
	my_time = my_time.replace(year=2014)
	tmp_tstamp = time.mktime(my_time.timetuple())*1000 + int (m.group(2))
	print ("%.0f" % tmp_tstamp)
	return "%.0f" % tmp_tstamp
	
def main():
	
	times = ["02-04 12:40:26.160" , "02-04 12:40:26.760" , "02-04 12:40:27.160" , "02-04 12:40:27.660" , "02-04 12:40:28.160" , "02-04 12:40:28.960"]
	
	for t in times:
		get_timestamp(t)
	
	
if __name__ == "__main__":
	main()