#!/usr/bin/env python3
"""Displays Grub entries and let the user choose which one should be default"""

import re
import sys
import os

from subprocess import call

def get_entries(file_path):
	"""Return a list of available entries"""
	entries = [];
	with open(file_path, 'r') as file:
		for line in file:
			m = re.search(r'^menuentry (?:\'|")(.*?)(?:\'|")', line)
			if m is not None: 
				entries.append(m.group(1))
	return entries
	
def get_current_entry(file_path):
	"""Return the current default entry"""
	with open(file_path, 'r') as file:
		for line in file:
			m = re.search(r'^saved_entry *=(.*)$', line)
			if m is not None: 
				return m.group(1)
	
def set_entry(file_path, entry):
	"""Set the new default entry"""
	with open(file_path, 'r') as file:
		lines = file.readlines()
	for i,line in enumerate(lines):
		if re.match(r'^saved_entry *=(.*)$', line):
			lines[i] = "saved_entry={}\n".format(entry)
	try:
		with open(file_path, 'w', newline='\n') as file:
			file.write(''.join(lines))
	except OSError:
		print("Cannot write the new configuration to {}".format(file_path))
		sys.exit(1)
	
def choose_entry(grub_path):
	"""Interactive menu to choose the new default entry"""
	entries = get_entries(os.path.join(grub_path, 'grub.cfg'))
	current_entry = get_current_entry(os.path.join(grub_path, 'grubenv'))
	print("-- List of entries --")
	for i,entry in enumerate(entries):
		print("{}. {}".format(i+1, entry))
	print("\nCurrent entry: {}".format(current_entry))
	
	while 1:
		choice = input("Type the number of the entry you want as default: ")
		try:
			choice = int(choice)
		except ValueError:
			print("You must type the number of the entry.")
			continue
		else:
			if choice < 1 or choice > len(entries):
				print("There is no entry {}.".format(choice))
				continue
			break
	return entries[choice-1]
	
def get_grub_path():
	"""Get the grub path from a config file or call choose_grub_path()"""
	if os.name == 'nt':
		config_path = os.path.expandvars('%appdata%\Grubchooser\grubchooser.conf')
	elif os.name == 'posix':
		config_path = os.path.expanduser('~/.grubchooser.conf')
	else:
		config_path = './.grubchooser.conf'
	
	try:
		file = open(config_path, 'r')
	except FileNotFoundError:
		return choose_grub_path(config_path)
	return file.readline().rstrip()
	
	
def choose_grub_path(config_path='.grubchooser.conf'):
	"""Ask the user for the grub path and save it to a config file"""
	default_grub_path = '/boot/grub/'
	grub_path = None
	while not grub_path:
		print("Type the path of the grub folder (which contains grub.cfg and grubenv)\n"
			"or press ENTER to use the default path:")
		grub_path = input("[{}]: ".format(default_grub_path)).strip("\"'")
		if not grub_path:
			grub_path = default_grub_path
		
		if not os.path.exists(os.path.join(grub_path, 'grub.cfg')):
			while 1:
				choice = input("There is no grub.cfg in \"{}\",\n".format(grub_path)
					+ "choose this path anyway (NOT recommended) ? [y\\n] ")
				if choice.lower() == 'y':
					break
				elif choice.lower() == 'n':
					# Restart the parent loop
					grub_path = None
					break
				else:
					continue
	try:
		os.makedirs(os.path.dirname(config_path), exist_ok=True)
	except FileExistsError:
		pass
	# OSError will be catched anyway when writing the config file
	try:
		with open(config_path, 'w') as file:
			file.write(grub_path)
	except OSError:
		print("ERROR: Cannot save the path of the grub folder.\n"
			"You still can choose the default entry for this time.")
	finally:
		return grub_path
		
def choose_reboot():
	"""Ask the user if he wants to reboot and use adhoc reboot command"""
	while True:
		choice = input("Would you like to reboot now ? [y\\N] ")
		if choice.lower() == 'n' or choice == '':
			return
		elif choice.lower() == 'y':
			break
		else:
			continue
	#debug
	#call = print
	# Reboot
	if os.name == 'nt':
		call('shutdown /r /t 00')
	else:
		call('reboot')

if __name__ == "__main__":
	grub_path = get_grub_path()
	grubenv_path = os.path.join(grub_path, 'grubenv')
	
	new_default = choose_entry(grub_path)
	set_entry(grubenv_path, new_default)
	print("Default entry successfully set to '{}'".format(new_default))
	choose_reboot()
	#input("Press ENTER to continue...")
