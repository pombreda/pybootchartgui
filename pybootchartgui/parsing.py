from __future__ import with_statement

import os
import re
import tarfile
from collections import defaultdict

from samples import *
from process_tree import ProcessTree

def _parse_headers(file):
    return dict( (map(lambda s: s.strip(),line.split('=', 1)) for line in file if '=' in line) )

def _parse_timed_blocks(file):
	blocks = file.read().split('\n\n')
	return [ (int(block.split('\n')[0]), block[1:]) for block in blocks if block.strip()]
	
def _parse_proc_ps_log(file):
	"""
	 * See proc(5) for details.
	 * 
	 * {pid, comm, state, ppid, pgrp, session, tty_nr, tpgid, flags, minflt, cminflt, majflt, cmajflt, utime, stime,
	 *  cutime, cstime, priority, nice, 0, itrealvalue, starttime, vsize, rss, rlim, startcode, endcode, startstack, 
	 *  kstkesp, kstkeip}
	"""
	processMap = {}
	timedBlocks = _parse_timed_blocks(file)	
	ltime = 0
	for time, block in timedBlocks:

		lines = block.split('\n')
		for line in lines[1:]:
			tokens = line.split(' ')			
			pid, cmd, state, ppid = int(tokens[0]), tokens[1], tokens[2], int(tokens[3])
				
			if not cmd.startswith('('):
				continue
			stime = int(tokens[21])

			if processMap.has_key(pid):
				process = processMap[pid]
				process.cmd = cmd.replace('(', '').replace(')', '') # why rename after latest name??
			else:
				process = Process(pid, cmd, ppid, min(time, stime))
				processMap[pid] = process
			
			userCpu = int(tokens[13])
			sysCpu = int(tokens[14])
			
			if process.last_user_cpu_time is not None and process.last_sys_cpu_time is not None and ltime is not None:
				userCpuLoad, sysCpuLoad = process.calc_load(userCpu, sysCpu, time - ltime)
				cpuSample = CPUSample('null', userCpu, sysCpu, 0.0)
				process.samples.append(ProcessSample(time, state, cpuSample))
			
			process.last_user_cpu_time = userCpu
			process.last_sys_cpu_time = sysCpu
		ltime = time
	
	numSamples = len(timedBlocks)-1
	startTime = timedBlocks[0][0]
	samplePeriod = (ltime - startTime)/numSamples	

	for process in processMap.values():
		process.set_parent(processMap)

	for process in processMap.values():
		process.calc_stats(samplePeriod)
		
	return ProcessStats(processMap.values(), samplePeriod, startTime, ltime)
	
def _parse_proc_stat_log(file):
	samples = []
	ltimes = None
	for time, block in _parse_timed_blocks(file):
		lines = block.split('\n')
		# CPU times {user, nice, system, idle, io_wait, irq, softirq}		
		tokens = lines[1].split();
		times = [ int(token) for token in tokens[1:] ]
		if ltimes:
			user = float((times[0] + times[1]) - (ltimes[0] + ltimes[1]))
			system = float((times[2] + times[5] + times[6]) - (ltimes[2] + ltimes[5] + ltimes[6]))
			idle = float(times[3] - ltimes[3])
			iowait = float(times[4] - ltimes[4])
			
			aSum = max(user + system + idle + iowait, 1)
			samples.append( CPUSample(time, user/aSum, system/aSum, iowait/aSum) )
		
		ltimes = times		
		# skip the rest of statistics lines
	return samples
		
def _parse_proc_disk_stat_log(file, numCpu):
	DISK_REGEX = 'hd.|sd.'
	
	diskStatSamples = defaultdict(DiskStatSample)
	diskStats = []
	ltime = None
	for time, block in _parse_timed_blocks(file):
		lines = block.split('\n')
		for line in lines:
			# {major minor name rio rmerge rsect ruse wio wmerge wsect wuse running use aveq}
			tokens = line.split();

			# take only lines with content and only look at the whole disks, eg. sda, not sda1, sda2 etc.
			if len(tokens) != 14 or not re.match(DISK_REGEX, tokens[2]) or not len(tokens[2]) == 3:
				continue
			
			disk = tokens[2]
			
			rsect, wsect, use = int(tokens[5]), int(tokens[9]), int(tokens[12])
			
			sample = diskStatSamples[disk]
						
			if ltime:				
				sample.changes = [rsect-sample.values[0], wsect-sample.values[1], use-sample.values[2]] 

			sample.values = [rsect, wsect, use]

		if ltime:
			interval = time - ltime
			
			sums = [0, 0, 0]
			for sample in diskStatSamples.values():
				for i in range(3):		
					sums[i] = sums[i] + sample.changes[i]
			
			
			readTput = sums[0] / 2.0 * 100.0 / interval
			writeTput = sums[1] / 2.0 * 100.0 / interval
			# number of ticks (1000/s), reduced to one CPU, time is in jiffies (100/s)
			util = float( sums[2] ) / 10 / interval / numCpu
			
			diskStats.append(DiskSample(time, readTput, writeTput, util))
			
		ltime = time
	return diskStats
	
	
def get_num_cpus(headers):
    """Get the number of CPUs from the system.cpu header property."""
    if headers is None:
        return 1
    cpu_model = headers.get("system.cpu")
    if cpu_model is None:
        return 1
    mat = re.match(".*\\((\\d+)\\)", cpu_model)
    if mat is None:
        return 1
    return int(mat.group(1))

class ParserState:
    def __init__(self):
        self.headers = None
	self.disk_stats = None
	self.ps_stats = None
	self.cpu_stats = None

_relevant_files = set(["header", "proc_diskstats.log", "proc_ps.log", "proc_stat.log"])

def _do_parse(state, name, file):
    if name == "header":
        state.headers = _parse_headers(file)
    elif name == "proc_diskstats.log":
        state.disk_stats = _parse_proc_disk_stat_log(file, get_num_cpus(state.headers))
    elif name == "proc_ps.log":
        state.ps_stats = _parse_proc_ps_log(file)
    elif name == "proc_stat.log":
        state.cpu_stats = _parse_proc_stat_log(file)
    return state

def parse_file(state, filename):
    basename = os.path.basename(filename)
    if not(basename in _relevant_files):
        return state
    with open(filename, "rb") as file:
        return _do_parse(state, basename, file)

def parse_paths(state, paths):
    for path in paths:
        root,extension = os.path.splitext(path)
        if not(os.path.exists(path)):
            print "warning: path '%s' does not exist, ignoring." % path
            continue
        if os.path.isdir(path):
            files = [ f for f in [os.path.join(path, f) for f in os.listdir(path)] if os.path.isfile(f) ]
            files.sort()
            state = parse_paths(state, files)
        elif extension in [".tar", ".tgz", ".tar.gz"]:
            tf = None
            try:
                tf = tarfile.open(path, 'r:*')
                for name in tf.getnames():
                    state = do_parse(state, name, tf.extractfile(name))
            except tarfile.ReadError, error:
                print "error: could not read tarfile '%s': %s." % (path, error)
            finally:
                if tf != None:
                    tf.close()
        else:
            state = parse_file(state, path)
    return state

def parse(paths, prune):   
    state = parse_paths(ParserState(), paths)
    monitored_app = state.headers.get("profile.process")
    proc_tree = ProcessTree(state.ps_stats, monitored_app, prune)
    return (state.headers, state.cpu_stats, state.disk_stats, proc_tree)
