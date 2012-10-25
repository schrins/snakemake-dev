# -*- coding: utf-8 -*-

import os, traceback, sys, csv
from snakemake.workflow import Workflow
from snakemake.exceptions import print_exception
from snakemake.logging import logger, init_logger

__author__ = "Johannes Köster"
__version__ = "1.2.3"

def snakemake(snakefile, list = False, jobs = 1, directory = None, targets = None, dryrun = False, touch = False, forcethis = False, forceall = False, forcerules = None, stats = None, give_reason = False, nocolor = False, printshellcmds = False, quiet = False, cluster = None, standalone = False, dag = False, ignore_ambiguity = False, scriptpath = None):
	"""
	Run snakemake on a given snakefile.
	Note: at the moment, this function is not thread-safe!
		
	Arguments
	snakefile         -- the snakefile.
	list              -- list rules.
	jobs              -- maximum number of parallel jobs (default: 1).
	directory         -- working directory (default: current directory).
	rule              -- execute this rule (default: first rule in snakefile).
	dryrun            -- print the rules that would be executed, but do not execute them.
	forcethis         -- force the selected rule to be executed
	forceall          -- force all rules to be executed
	time_measurements -- measure the running times of all rules
	"""
	if forcerules:
		forcerules = set(forcerules) # ensure O(1) access since this will be done for every rule

	init_logger(nocolor=nocolor, stdout=dryrun)

	if not os.path.exists(snakefile):
		logger.error("Error: Snakefile \"{}\" not present.".format(snakefile))
		return False

	def print_rules(log):
		log("Defined rules:")
		for rule in workflow.get_rules(): log(rule.name)
	
	olddir = os.getcwd()

	workflow = Workflow(scriptpath = scriptpath)

	if directory:
		# change to the specified directory. This overrides eventually specified workdir in Snakefile
		workflow.workdir(directory)

	if standalone:
		try:
			# set the process group
			os.setpgrp()
		except:
			# ignore: if it does not work we can still work without it
			pass

	try:
		workflow.include(snakefile, overwrite_first_rule = True)

		workflow.check_rules()

		if list:
			print_rules(logger.info)
			return 0
	
		workflow.cores = jobs
		
		success = True
		if not targets: 
			success = workflow.run_first_rule(dryrun = dryrun, printshellcmds = printshellcmds, quiet = quiet, touch = touch, forcethis = forcethis, forceall = forceall, forcerules = forcerules, give_reason = give_reason, cluster = cluster, dag = dag, ignore_ambiguity = ignore_ambiguity)
		else:
			success = workflow.run_rules(targets, dryrun = dryrun, printshellcmds = printshellcmds, quiet = quiet, touch = touch, forcethis = forcethis, forceall = forceall, forcerules = forcerules, give_reason = give_reason, cluster = cluster, dag = dag, ignore_ambiguity = ignore_ambiguity)
		if success and stats:
			stats = csv.writer(open(stats, "w"), delimiter = "\t")
			stats.writerow("rule minimum maximum sum mean".split())
			s = 0
			for measurement in workflow.get_runtimes():
				stats.writerow(measurement)
				s += measurement[3]
			stats.writerow([])
			stats.writerow(("Overall runtime", s))
		os.chdir(olddir)
		return success
	except (Exception, BaseException) as ex:
		print_exception(ex, workflow.rowmaps)
		os.chdir(olddir)
		return False
