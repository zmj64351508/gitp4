#!/usr/bin/python

import sys, os
import re

import argparse

from debug import *
from common import *
from git_p4_commands import *

def cleanup_branch(origin_branch):
	run_cmd("git checkout %s" % origin_branch)
	try:
		run_cmd("git branch -D branch_merge_p4")
	except:
		pass

def fix_commit_message(msg):
	i = 0
	while i < len(msg):
		if msg[i] == '"':
			msg = msg[0:i] + "\\" + msg[i:]
			i += 1
		i += 1
	return msg

def init_p4git(init_p4_path):
	dir_name = os.path.basename(init_p4_path)
	os.mkdir(dir_name)
	os.chdir(dir_name)
	if not is_git_path_valid("."):
		run_cmd("git init")
	if os.path.isfile(".git/p4_repo"):
		os.remove(".git/p4_repo")
	with open(".git/p4_repo", "w") as f:
		f.write(init_p4_path)

def main(argc, argv):
	parser = argparse.ArgumentParser(description="p4 to git converter")

	parser.add_argument("--init", action="store", dest="init_p4_path", type=str)

	args = parser.parse_args(argv[1:])
	if args.init_p4_path:
		init_p4git(args.init_p4_path)

	try:
		env = get_env()
	except IOError as e:
		print e
		print "Please try to %s --init <p4 path>" % os.path.basename(argv[0])
		return
	except Exception as e:
		print e
		return

	git_repo_path = env["git_repo_path"]
	p4_repo_path = env["p4_repo_path"]
	p4_repo_relpath = env["p4_repo_relpath"]

	pr_info("git repo: %s" % git_repo_path)
	pr_info("p4 repo: %s" % p4_repo_path)
	pr_info("p4 root: %s" % p4_repo_relpath)

	if not is_git_path_valid(git_repo_path):
		pr_error("Invalid git repo path")
		return

	replace_p4_with_git(git_repo_path, p4_repo_path, p4_repo_relpath)
	os.chdir(p4_repo_path)

	if args.init_p4_path:
		change_list = "0"
	else:
		origin_branch = get_origin_branch()
		if not origin_branch:
			pr_error("Can not find the original branch, do you in a branch?")

		# checkout last change list
		change_list = find_last_change_list_in_git()

		run_cmd("git clean -fd")
		cleanup_branch(origin_branch)
		run_cmd("git checkout -b branch_merge_p4 CL%s" % change_list)

	run_cmd("git clean -fd")
	pr_info("git repo last change list is " + change_list)

	# syncing p4 to the latest
	run_cmd("p4 sync -f %s/...#head" % p4_repo_relpath)

	# check whether git repo is already the lastest according to p4
	if not args.init_p4_path:
		ret = run_cmd("git status")
		if ret.find("working directory clean") >= 0:
			cleanup_branch(origin_branch)
			# nothing to do
			pr_info("git repo is already the latest on p4")
			return

	# determine which change list should be committed
	ret = run_cmd("p4 changes " + p4_repo_relpath + "/...")
	cl_to_commit = []
	for cl in ret.split("\n"):
		try:
			cl_to_commit.append(cl.split()[1])
			if cmp(cl.split()[1], change_list) == 0:
				break
		except:
			pass
	cl_to_commit = cl_to_commit[::-1]
	pr_info("following change list need to be committed:\n%s" % cl_to_commit)

	if args.init_p4_path:
		# insert commits start with index 1, so insert a fake commit in index 0
		cl_to_commit.insert(0, "no_use")
	else:
		# sync p4 to the git lasted change list, and check the work tree
		run_cmd("p4 sync -f %s/...@%s" % (p4_repo_relpath, cl_to_commit[0]))
		ret = run_cmd("git status")
		if ret.find("working directory clean") < 0:
			pr_error("Working tree not clean\n%s" % ret)
			return

	# commit from the next change list
	for cl in cl_to_commit[1:]:
		run_cmd("p4 sync %s/...@%s" % (p4_repo_relpath, cl))
		cl_info = run_cmd("p4 describe -s %s" % cl)
		cl_info = re.findall("(.*)Affected files ...\n", cl_info, re.DOTALL|re.MULTILINE)[0]
		cl_info += "Merge from Perforce\n"
		cl_info = fix_commit_message(cl_info)
		run_cmd("git add -A")
		pr_info("committing CL%s" % cl)
		#print run_cmd("git status")
		try:
			pr_info(run_cmd("git commit -m \"%s\"" % cl_info))
		except:
			pr_error("commit error occurred")

	#p4_change_list = re.findall(r"^Change [" + str(change_list) + "]+ .*$", ret, re.MULTILINE)
	#if len(p4_change_list) == 0:
	#	pr_error("Cannot find CL%d in p4" % change_list)
	#	return
	#pr_info("p4 change list: %s" % p4_change_list[0])

	#pr_info(run_cmd("p4 describe -s %s" % change_list))

	run_cmd("git tag CL%s" % cl_to_commit[-1])
	run_cmd("chmod -R +w *")
	run_cmd("git checkout master")
	run_cmd("git rebase branch_merge_p4")
	cleanup_branch(origin_branch)

	pr_info("replaceing git with latest p4 repo")
	replace_git_with_p4(git_repo_path, p4_repo_path, p4_repo_relpath)

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)
