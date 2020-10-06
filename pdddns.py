#!/usr/bin/python3

#######################CFG###########################
#domain = 's0.ud3.ru'

curl = "/usr/bin/curl -s -H 'PddToken: 1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234'"
pddaddr = 'https://pddimp.yandex.ru'
pddlist = '/api2/admin/dns/list?domain='
pddadd = '/api2/admin/dns/add'
pddedit = '/api2/admin/dns/edit'
pdddel = '/api2/admin/dns/del'
defttl = 900
#####################################################

import subprocess, json, sys, argparse
from pprint import pprint

def main(argv):
	parser = argparse.ArgumentParser(description='Working with DNS zones hosted on Yandex Connect.')
	parser.add_argument('command', type=str, choices=['add', 'list', 'edit', 'del'], help='(str) Tell me what to do.')
	#parser.add_argument('-a', '--admin_mail', type=check_email, help='(email) Admin email address.')
	parser.add_argument('-c', '--content', type=str, help='(str) Record\'s content.')
	parser.add_argument('-d', '--domain', type=str, required=True, help='(str) Zone FQDN. Required for any command.')
	parser.add_argument('-f', action='store_true', help='Filters output rows of the "list" command (AND logic).')
	parser.add_argument('--cfilter', type=str, help='Filters output columns of the "list" command (row names with comma delimiter)')
	parser.add_argument('--fqdn', type=str, help='(str) Record\'s FQDN. Uses with "list" command and with "-f" option.')
	parser.add_argument('--port', type=int, help='(int 1-65535) Port for SRV records.')
	parser.add_argument('-p', '--priority', type=int, help='(int) Record\'s priority.')
	parser.add_argument('-r', '--record_id', type=int, help='(int) ID of the DNS record. Required for the "edit" and "del" commands.')
	parser.add_argument('-s', '--subdomain', type=str, help='(str) Sumdomain name.')
	parser.add_argument('-ttl', type=int, default=defttl, help='(int) Record\'s time to live in seconds. Default is 900.')
	parser.add_argument('-t', '--type', type=str, choices=['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT'], help='(str) Type of the DNS record. Required for the "add" command.')
	parser.add_argument('-target', type=str, help='(str) Canonical hostname for SRV records.')
	parser.add_argument('-w', '--weight', type=int, help='(int) SRV record\'s weight.')
	args = parser.parse_args()
	
#	print(vars(args))######################
	
	if args.command == 'add':
		add_record(vars(args))
	elif args.command == 'list':
		zone_list(vars(args))
	elif args.command == 'edit':
		edit_record(vars(args))
	elif args.command == 'del':
		del_record(vars(args))
	else:
		print('Error! Wrong command.')
		exit(1)
	#pprint(args)

def donothing():
	return 0

def check_email(email):
	import re
	regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,10}$'
	if(re.search(regex,email)):
		return email
	else:
		raise argparse.ArgumentTypeError("Invalid email address")
		return False
	

def decode_jsn(jsntxt):
	jsn = ''
	epos = 0
	try:
		jsn, epos = json.JSONDecoder().raw_decode(jsntxt)
	except Exception as e:
		print('Error! Wrong json dump recieved.')
		print('DUMP:')
		print(jsntxt)
		print('')
		print (e)
		exit(1)
	
	if jsn['success'] == 'error':
		print('Error! Server\'s response was not ok.')
		print('Response: ' + jsn['error'])
		exit(1)
	
	return jsn

def get_post_str(args):
	
	post = 'domain='+args['domain']+'&ttl='+str(args['ttl'])
	
	if type(args['content']) == str:
		if len(args['content']) < 1:
			print("Error! Argument 'content' is empty.")
			exit(1)
		post += '&content='+args['content']
	else:
		if args['command'] == 'add':
			print("Error! Argument 'content' has a wrong type.")
			exit(1)
	
	if type(args['subdomain']) == str:
		if len(args['subdomain']) < 1:
			args['subdomain'] = '@'
		post += '&subdomain='+args['subdomain']
	else:
		if args['command'] == 'add':
			args['subdomain'] = '@'
			post += '&subdomain='+args['subdomain']
	
	if type(args['type']) == str:
		post += '&type='+args['type']
	else:
		if args['command'] == 'add':
			print("Error! Argument 'type' has a wrong type.")
			exit(1)
	
	if args['type'] == 'SRV' or args['type'] == 'MX':
		if type(args['priority']) == int and args['priority'] > 0:
			post += '&priority='+str(args['priority'])
		else:
			print("Error! Argument 'priority' is wrong.")
			exit(1)
	
	if args['type'] == 'SRV':
		if type(args['weight']) == int and args['weght'] > 0:
			post += '&weight='+str(args['weight'])
		else:
			print("Error! Argument 'weight' is wrong.")
			exit(1)
		
		if type(args['port']) == int and args['port'] > 0 and args['port'] < 65536:
			post += '&port='+str(args['port'])
		else:
			print("Error! Argument 'port' is wrong.")
			exit(1)
		
		if type(args['target']) == str and len(args['target']) > 0:
			post += '&target='+args['target']
		else:
			print("Error! Argument 'target' is wrong.")
			exit(1)
		
	return post

def zone_list(args):
	
	PIPE = subprocess.PIPE
	p = subprocess.Popen(curl+" '"+pddaddr+pddlist+args['domain']+"'", shell=True, stdout=PIPE, close_fds=True, cwd='.')
	jsntxt = p.stdout.read().strip().decode()
	
	jsn = decode_jsn(jsntxt)
	
#	epos = 0
#	try:
#		jsn, epos = json.JSONDecoder().raw_decode(jsntxt)
#	except Exception as e:
#		print('Error! Wrong json dump recieved.')
#		print('DUMP:')
#		print(jsntxt)
#		print('')
#		print (e)
#		exit(1)
#
#	if jsn['success'] == 'error':
#		print('Error! Server\'s response was not ok.')
#		print('Response: ' + jsn['error'])
#		exit(1)
	
	rf = {}
	cf = []
	records = jsn['records']
	if args['f']:
		for item in args.items():
			if item[0] == 'cfilter' or item[0] == 'command' or item[0] == 'domain' or item[0] == 'f' or item[0] == 'ttl':
				continue
			if item[1] == None:
				continue
			rf.update({item[0]: item[1]})
		if args['cfilter'] != None:
			cf = args['cfilter'].split(',')
#		print (rf)#####################
#		print (cf)#####################
		
		if len(rf) > 0:
			records = []
		for item in rf.items():
			for j in jsn['records']:
				if item[0] == 'content':
					if j.get(item[0]) != None:
						if j.get(item[0]).find(item[1]) > -1:
							records.append(j)
				else:
					if j.get(item[0]) == item[1]:
						records.append(j)
			jsn['records'] = records
			records = []
		records = jsn['records']
	
#	print(records)#################
	i = 0
	for record in records:
		i+=1
		for key, value in record.items():
			if (not (key in cf)) and (len(cf) > 0) and args['f']:
				continue
			msg = key + ': ' + value.__str__()
			if (len(cf) == 1) and args['f']:
				msg = value.__str__()
			print(msg)
		if i < len(records):
			print('')
	
	

def add_record(args):
	
	post = get_post_str(args)
	
	PIPE = subprocess.PIPE
	p = subprocess.Popen(curl+" -d '"+post+"' '"+pddaddr+pddadd+"'", shell=True, stdout=PIPE, close_fds=True, cwd='.')
	jsntxt = p.stdout.read().strip().decode()
	
	jsn = decode_jsn(jsntxt)
	print (jsn)
	

def edit_record(args):
	
	if type(args['record_id']) != int:
		print("Error! Argument 'record_id' has a wrong type.")
		exit(1)
	post = 'record_id=' + str(args['record_id']) + '&'
	post += get_post_str(args)
#	print(post)###################
	PIPE = subprocess.PIPE
	p = subprocess.Popen(curl+" -d '"+post+"' '"+pddaddr+pddedit+"'", shell=True, stdout=PIPE, close_fds=True, cwd='.')
	jsntxt = p.stdout.read().strip().decode()
	
	jsn = decode_jsn(jsntxt)
	print (jsn)
	

def del_record(args):
	
	if type(args['record_id']) != int:
		print("Error! Argument 'record_id' has a wrong type.")
		exit(1)
	post = 'record_id=' + str(args['record_id']) + '&domain=' + args['domain']
#	print(post)###################
	PIPE = subprocess.PIPE
	p = subprocess.Popen(curl+" -d '"+post+"' '"+pddaddr+pdddel+"'", shell=True, stdout=PIPE, close_fds=True, cwd='.')
	jsntxt = p.stdout.read().strip().decode()
	
	jsn = decode_jsn(jsntxt)
	print (jsn)
	


if __name__ == "__main__":
	main(sys.argv)
