import os, sys
import subprocess
import re
from debug import *

def run_cmd(cmd, stdin=None):
	#print cmd
	#return subprocess.check_output(cmd, stderr=subprocess.PIPE, shell=True)

	process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, unused_err = process.communicate(stdin)
	retcode = process.poll()
	if retcode:
		#cmd = kwargs.get("args")
		raise subprocess.CalledProcessError(retcode, cmd, output=output)
	return output

def is_git_path_valid(path):
	return os.path.isdir(os.path.join(path, ".git"))

def get_p4_workspace(client_name):
	ret = run_cmd("p4 client -o %s" % client_name)
	return re.findall(r"^Root:\s*(.*)$", ret, re.MULTILINE)[0]

def get_env():
	git_repo_path = os.path.abspath(".")

	p4_client = os.getenv('P4CLIENT')
	p4_workspace = get_p4_workspace(p4_client)

	f = open(os.path.join(git_repo_path, ".git/p4_repo"), "r")
	line = f.readline()
	p4_repo_name = line.strip()
	f.close()

	p4_repo_path = os.path.join(p4_workspace, p4_repo_name.strip("/"))
	p4_repo_relpath = "//" + p4_repo_name.strip("/")

	return {"git_repo_path":git_repo_path,
		"p4_repo_path":p4_repo_path,
		"p4_repo_relpath":p4_repo_relpath}
