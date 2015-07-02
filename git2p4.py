#!/usr/bin/python

import sys, os

from debug import *
from common import *
from git_p4_commands import *

def main(argc, argv):
	try:
		env = get_env()
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

	result = run_cmd("p4 opened %s/..." % p4_repo_relpath)
	if result:
		pr_warn("There are files opened in p4. Please submit or revert them first\n" +
			result)
		ret = raw_input("Do you want to revert these files?(y/n)")
		if ret == "y":
			run_cmd("p4 revert -c default %s/..." % p4_repo_relpath)
		else:
			return

	replace_p4_with_git(git_repo_path, p4_repo_path, p4_repo_relpath)
	os.chdir(p4_repo_path)

	git_last_cl = find_last_change_list_in_git()
	p4_last_cl = find_last_change_list_in_p4(p4_repo_relpath)

	if cmp(git_last_cl, p4_last_cl) != 0:
		pr_error("P4 was updated since last sync to git. Please update git repo accroding to p4.\n" + 
				"last git change list: %s\n" % git_last_cl + 
				"last  p4 change list: %s\n" % p4_last_cl)
		return

	result = run_cmd("git log --pretty=oneline CL%s..HEAD" % git_last_cl)
	commit_to_cl = [ line.split()[0] for line in result.splitlines()[::-1]]

	#check current commit	

	for commit in commit_to_cl:
		run_cmd("git checkout %s" % commit)

		result = run_cmd("git log --name-status -1 %s" % commit)
		print result
		mod_files = re.findall(r"^[M]{1}\t(.*)$", result, re.MULTILINE)
		add_files = re.findall(r"^[A]{1}\t(.*)$", result, re.MULTILINE)
		del_files = re.findall(r"^[D]{1}\t(.*)$", result, re.MULTILINE)

		files = ""
		if mod_files:
			cmd = "p4 edit"
			for f in mod_files:
				cmd += " " + p4_repo_relpath + "/" + f
				files += "\t" + p4_repo_relpath + "/" + f + "\n"
			run_cmd(cmd)
			print mod_files

		if add_files:
			cmd = "p4 add"
			for f in add_files:
				cmd += " " + p4_repo_relpath + "/" + f
				files += "\t" + p4_repo_relpath + "/" + f + "\n"
			print add_files
			run_cmd(cmd)

		if del_files:
			cmd = "p4 delete"
			for f in del_files:
				cmd += " " + p4_repo_relpath + "/" + f
				files += "\t" + p4_repo_relpath + "/" + f + "\n"
			print del_files
			run_cmd(cmd)

		commit_info = run_cmd("git log -1 %s" % commit)
		author = re.findall("^Author:\s*(.*)$", commit_info, re.MULTILINE)[0]
		cl_info = "Change:\tnew\n\n" + "Status:\tnew\n\n" + "Description:\n"

		for line in commit_info.splitlines()[4:]:
			cl_info += "\t" + line.strip() + "\n"
		cl_info += "\tBy %s" % author

		cl_info += "\nFiles:\n" + files
		pr_info(cl_info)
		result = run_cmd("p4 change -i", stdin=cl_info)
		try:
			cl = re.findall(r"^Change ([0-9]*) ", result, re.MULTILINE)[0]
		except Exception:
			pr_error("Can not add change")


		result = raw_input("Submit and Continue?(y/n)")
		if result != "y":
			return

		run_cmd("p4 submit -c %s" % cl)

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)
