# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import copy
import json
import time
import os

from matplotlib import pyplot as plt

def rm_baseline_cov(baseline_coverage, test_coverage):
	'''
		Returns the difference between test_coverage and
		baseline_coverage in such a way that what is
		returned is the unique coverage for the test in
		question.
		
		This function assumes that the coverage jsons given
		as parameters are those created by using grcov with
		the flags |-t coveralls --token XXX --commit-sha XXX|.

		:param: baseline_coverage: Baseline coverage from start up and shut down
		:param: test_coverage: Code coverage from a given test.
	'''

	# Get all files into a quicker search format
	unique_test_coverage = copy.deepcopy(test_coverage)
	baseline_files = {el['name']: el for el in baseline_coverage['source_files']}
	test_files = {el['name']: el for el in test_coverage['source_files']}

	# Perform the difference and find everything
	# unique to the test.
	unique_files = 0
	unique_files_list = []
	unique_file_coverage = {}
	for test_file in test_files:
		if test_file not in baseline_files:
			unique_file_coverage[test_file] = test_files[test_file]
			unique_files += 1
			unique_files_list.append(test_file)
			continue

		# Get line numbers and the differences
		file_coverage = {i+1 for i, cov in enumerate(test_files[test_file]['coverage']) \
							     if cov is not None and cov > 0}

		baseline = {i+1 for i, cov in enumerate(baseline_files[test_file]['coverage']) \
							if cov is not None and cov > 0}

		unique_coverage = file_coverage - baseline

		if len(unique_coverage) > 0:
			unique_file_coverage[test_file] = test_files[test_file]

			# Return the data to original format to return
			# coverage within the test_coverge data object.
			fmt_unique_coverage = []
			for i, cov in enumerate(unique_file_coverage[test_file]['coverage']):
				if cov is None:
					fmt_unique_coverage.append(None)
					continue

				if cov > 0:
					# If there is a count
					if (i+1) in unique_coverage:
						# Only add the count if it's unique
						fmt_unique_coverage.append(unique_file_coverage[test_file]['coverage'][i])
						continue
				# Zero out everything that is not unique
				fmt_unique_coverage.append(0)
			unique_file_coverage[test_file]['coverage'] = fmt_unique_coverage

	# Reformat to original test_coverage list structure
	unique_test_coverage['source_files'] = list(unique_file_coverage.values())
	unique_test_coverage['unique_file_count'] = unique_files
	unique_test_coverage['unique_files'] = unique_files_list

	return unique_test_coverage


def main():
	gathering = False
	RESULTS_DIR = """C:\\Users\\greg\\Documents\\mozwork\\baseline_differences\\results2\\"""
	DATA_DIR = """C:\\Users\\greg\\Documents\\mozwork\\baseline_differences\\overtime_analysis\\"""

	dirs = os.listdir(DATA_DIR)
	print(dirs)

	difference_sets = {'xul-js': [], 'xul-html': [], 'html-js': [], 'html-xul': [], 'js-xul': [], 'js-html': []}

	if gathering:
		count = 0
		for test_chunk_dir in dirs:
			if count > 100:
				break
			count += 1

			curr_dir = os.path.join(DATA_DIR, test_chunk_dir)

			baselines = []
			onlyfiles = [f for f in os.listdir(curr_dir) if os.path.isfile(os.path.join(curr_dir, f))]
			for file in onlyfiles:
				fpath = os.path.join(curr_dir, file)
				with open(fpath) as f:
				    tmp_coverage = json.load(f)

				if 'baselinecoverage' in tmp_coverage['test']:
					baselines.append(tmp_coverage)

			for baseline_coverage in baselines:
				tname = baseline_coverage['test']
				ttype = tname.split('.')[-1]

				print("On baseline: " + ttype)
				for test_coverage in baselines:
					tname2 = test_coverage['test']
					ttype2 = tname2.split('.')[-1]
					if ttype == ttype2:
						continue

					print("Test coverage: " + ttype2)

					unique_coverage = rm_baseline_cov(baseline_coverage['report'], test_coverage['report'])

					for diff in difference_sets:
						split_diff = diff.split('-')
						if split_diff[0] == ttype2 and split_diff[1] == ttype:
							difference_sets[diff].append(unique_coverage)

			print("Difference Lengths:")
			for i in difference_sets:
				print(i + ":" + str(len(difference_sets[i])))
	else:
		for diff_type in difference_sets:
			save_path = os.path.join(RESULTS_DIR, diff_type + '.json')
			with open(os.path.join(RESULTS_DIR, diff_type + '.json'), 'r') as f:
				difference_sets[diff_type] = json.load(f)

	total_files = {}
	unique_files = {}
	total_lines_unique = {}
	unique_files_list = {}

	# Split into c, js, and etc. groups
	c_group = ('cpp', 'h', 'c', 'cc', 'hh', 'tcc')
	js_group = ('js', 'jsm')
	c_split = {}
	js_split = {}
	etc_split = {}
	c_split['total_files'] = {}
	c_split['total_lines_unique'] = {}
	js_split['total_files'] = {}
	js_split['total_lines_unique'] = {}
	etc_split['total_files'] = {}
	etc_split['total_lines_unique'] = {}
	all_files = {}

	for diff_type in difference_sets:
		total_files[diff_type] = []
		unique_files[diff_type] = []
		unique_files_list[diff_type] = []
		total_lines_unique[diff_type] = []
		all_files[diff_type] = []
		save_path = os.path.join(RESULTS_DIR, diff_type + '.json')

		if not os.path.exists(save_path):		
			with open(os.path.join(RESULTS_DIR, diff_type + '.json'), 'w') as f:
				json.dump(difference_sets[diff_type], f)

		c_split['total_files'][diff_type] = [0] * len(difference_sets[diff_type])
		c_split['total_lines_unique'][diff_type] = [0] * len(difference_sets[diff_type])
		js_split['total_files'][diff_type] = [0] * len(difference_sets[diff_type])
		js_split['total_lines_unique'][diff_type] = [0] * len(difference_sets[diff_type])
		etc_split['total_files'][diff_type] = [0] * len(difference_sets[diff_type])
		etc_split['total_lines_unique'][diff_type] = [0] * len(difference_sets[diff_type])

		for i, diff in enumerate(difference_sets[diff_type]):
			total_files[diff_type].append(len(diff['source_files']))
			unique_files[diff_type].append(diff['unique_file_count'])
			unique_files_list[diff_type].extend(diff['unique_files'])

			for t in diff['source_files']:
				tname = t['name']
				all_files[diff_type].append(tname)
				ftype = tname.split('.')[-1]
				if ftype in c_group:
					c_split['total_files'][diff_type][i] += 1
					c_split['total_lines_unique'][diff_type][i] += len([line for line in t['coverage'] if line is not None and line > 0])
				elif ftype in js_group:
					js_split['total_files'][diff_type][i] += 1
					js_split['total_lines_unique'][diff_type][i] += len([line for line in t['coverage'] if line is not None and line > 0])
				else:
					print("No group for: " + ftype)
					etc_split['total_files'][diff_type][i] += 1
					etc_split['total_lines_unique'][diff_type][i] += len([line for line in t['coverage'] if line is not None and line > 0])

			total_lines_changed = 0

			for f in diff['source_files']:
				coverage = f['coverage']
				total_lines_changed += len([line for line in coverage if line is not None and line > 0])
			total_lines_unique[diff_type].append(total_lines_changed)

	for diff_type in unique_files_list:
		unique_files_list[diff_type] = list(set(unique_files_list[diff_type]))

	for diff_type in all_files:
		all_files[diff_type] = list(set(all_files[diff_type]))

	with open(os.path.join(RESULTS_DIR, 'all_files_per_type.json'), 'w') as f:
		json.dump(all_files, f, indent=4)

	all_files_list = []
	for diff_type in all_files:
		all_files_list.extend(all_files[diff_type])

	all_files_list_no_dupes = list(set(all_files_list))
	all_files_path_split = {}
	for file in all_files_list_no_dupes:
		file_split = file.split('/')
		if 'testing' == file_split[0]:
			continue

		if len(file_split) > 2:
			dict_dir = file_split[0] + '/' + file_split[1]
			filename = '/'.join(file_split[2:])
		else:
			dict_dir = file_split[0]
			filename = file_split[-1]
		if dict_dir == 'media/ffvpx':
			continue

		if dict_dir not in all_files_path_split:
			all_files_path_split[dict_dir] = []
		all_files_path_split[dict_dir].append(filename)

	with open(os.path.join(RESULTS_DIR, 'all_files_list.json'), 'w') as f:
		json.dump(all_files_list_no_dupes, f, indent=4)

	with open(os.path.join(RESULTS_DIR, 'all_files_split_by_dir.json'), 'w') as f:
		json.dump(all_files_path_split, f, indent=4)

	import numpy as np
	inds = np.arange(len(total_files['xul-js']))
	colors = {
		'xul-js': 'r', 'xul-html': 'm', 'html-js': 'b', 'html-xul': 'dodgerblue', 'js-xul': 'gray', 'js-html': 'k'
	}

	ftype_dict = {
		'c-split': {'name': 'C/C++ coverage', 'data': c_split},
		'js-split': {'name': 'JS coverage', 'data': js_split},
		'etc-split': {'name': 'Etc. coverage', 'data': etc_split},
	}

	for split_type in ftype_dict:
		diff = ftype_dict[split_type]['data']
		total_files = diff['total_files']
		total_lines_unique = diff['total_lines_unique']
		title = ftype_dict[split_type]['name']

		plt.figure()
		ax = plt.subplot(2,1,1)
		for diff_type in total_files:
			plt.plot(inds, total_files[diff_type], label=diff_type, color=colors[diff_type])
		plt.gca().set_title('Total number of files with differences')

		plt.subplot(2,1,2)
		for diff_type in total_lines_unique:
			plt.plot(inds, total_lines_unique[diff_type], label=diff_type, color=colors[diff_type])
		plt.gca().set_title('Total number of unique lines')

		plt.suptitle(title)
		plt.legend(loc='upper right')

		#plt.figure()
		#for diff_type in unique_files:
		#	plt.plot(inds, unique_files[diff_type], label=diff_type, color=colors[diff_type])
		#plt.legend()

	plt.show()

	return


if __name__=="__main__":
	main()