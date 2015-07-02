import sys, os
import re

from debug import *
from common import *

def replace_p4_with_git(git_repo_path, p4_repo_path, p4_repo_relpath):
	run_cmd("p4 sync -f " + p4_repo_relpath + "/..." + "#head")
	run_cmd("rm -rf " + p4_repo_path)
	run_cmd("cp -rf " + git_repo_path + " " + p4_repo_path)

def replace_git_with_p4(git_repo_path, p4_repo_path, p4_repo_relpath):
	run_cmd("rm -rf %s" % git_repo_path+".bak")
	run_cmd("mv -f %s %s" % (git_repo_path, git_repo_path+".bak"))
	run_cmd("cp -rf %s %s" % (p4_repo_path, git_repo_path))

def get_origin_branch():
	ret = run_cmd("git branch")
	origin_branch = ""
	for line in ret.splitlines():
		if line.startswith("*"):
			origin_branch = line[1:].strip()
			break
	return origin_branch

def find_last_change_list_in_git():
	result = run_cmd("git tag")
	cl = re.findall(r"^CL.*", result, re.MULTILINE)
	if not cl:
		return None
	return cl[-1][2:]

def find_last_change_list_in_p4(p4_repo_relpath):
	result = run_cmd("p4 changes " + p4_repo_relpath + "/...")
	return result.splitlines()[0].split()[1]
