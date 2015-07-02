PR_LEVELS = [
	"ALWAYS",
	"ERROR",
	"WARN",
	"INFO",
	"DEBUG"
]

CUR_PR_LEVEL = PR_LEVELS.index("INFO")

def pr_error(string):
	pr_level("ERROR", string)

def pr_warn(string):
	pr_level("WARN", string)

def pr_info(string):
	pr_level("INFO", string)

def pr_debug(string):
	pr_level("DEBUG", string)

def pr_level(level, string):
	try:
		if PR_LEVELS.index(level) <= CUR_PR_LEVEL:
			print "[" + level + "] " + string
	except ValueError:
		pr_error("Unknown print level %s" % level)
