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

	# Returns the differences between the first
	# and the second set given. Or those elements that are
	# in the first but not the second one.
	def diff(first, second):
		second = set(second)
		return [item for item in first if item not in second]

	def get_all_but_name(element):
		return {i: element[i] for i in element if i != 'name'}

	print("Removing baseline code coverage")

	# Get all files into a quicker search format
	unique_test_coverage = copy.deepcopy(test_coverage)
	baseline_files = {el['name']: get_all_but_name(el) for el in baseline_coverage['source_files']}
	test_files = {el['name']: get_all_but_name(el) for el in test_coverage['source_files']}

	# Perform the difference and find everything
	# unique to the test.
	unique_files = 0
	unique_file_coverage = {}
	for test_file in test_files:
		if test_file not in baseline_files:
			unique_file_coverage[test_file] = test_files[test_file]
			unique_files += 1
			continue

		# Get line numbers and the differences
		file_coverage = [i+1 for i in range(len(test_files[test_file]['coverage'])) \
							     if test_files[test_file]['coverage'][i] is not None and \
							        test_files[test_file]['coverage'][i] > 0]

		baseline = [i+1 for i in range(len(baseline_files[test_file]['coverage'])) \
							if baseline_files[test_file]['coverage'][i] is not None and \
							   baseline_files[test_file]['coverage'][i] > 0]

		unique_coverage = diff(file_coverage, baseline)

		if len(unique_coverage) > 0:
			unique_file_coverage[test_file] = test_files[test_file]

			# Return the data to original format to return
			# coverage within the test_coverge data object.
			fmt_unique_coverage = []
			for i in range(len(unique_file_coverage[test_file]['coverage'])):
				if unique_file_coverage[test_file]['coverage'][i] is None:
					fmt_unique_coverage.append(None)
					continue

				if unique_file_coverage[test_file]['coverage'][i] > 0:
					# If there is a count
					if (i+1) in unique_coverage:
						# Only add the count if it's unique
						fmt_unique_coverage.append(unique_file_coverage[test_file]['coverage'][i])
						continue
				# Zero out everything that is not unique
				fmt_unique_coverage.append(0)
			unique_file_coverage[test_file]['coverage'] = fmt_unique_coverage

	# Reformat to original test_coverage structure
	formatted_coverage = []
	for test_file in unique_file_coverage:
		entry = unique_file_coverage[test_file]
		entry['name'] = test_file
		formatted_coverage.append(entry)
	unique_test_coverage['source_files'] = formatted_coverage
	unique_test_coverage['unique_file_count'] = unique_files

	return unique_test_coverage


def main():
	analyze = True
	RESULT_DIR = """C:\\Users\\greg\\Documents\\mozwork\\baseline_differences\\"""
	baseline_coverage_path = """C:\\Users\\greg\\Documents\\mozwork\\baseline_differences\\test_baselinecoverage.xul.json"""
	test_coverage_path = """C:\\Users\\greg\\Documents\\mozwork\\baseline_differences\\test_baselinecoverage.html.json"""

	if not analyze:
		# Open the jsons
		with open(baseline_coverage_path) as f:
		    baseline_coverage = json.load(f)
		with open(test_coverage_path) as f:
		    test_coverage = json.load(f)

		# Get the test coverage - returns what is unique to the second argument
		unique_coverage = rm_baseline_cov(baseline_coverage['report'], test_coverage['report'])

		test_coverage['total_file_count'] = len(unique_coverage['source_files'])
		test_coverage['report'] = unique_coverage
		with open(os.path.join(RESULT_DIR, 'difference_' + str(int(time.time())) + '.json'), 'w') as f:
			json.dump(test_coverage, f)
		return

	diff_list = {
		'differences_unique_to_xul_baseline_against_js.json': {'display_name': 'xul-js'},
		'differences_unique_to_xul_baseline_against_html.json': {'display_name': 'xul-html'},
		'differences_unique_to_html_baseline_against_js.json': {'display_name': 'html-js'},
		'differences_unique_to_html_baseline_against_xul.json': {'display_name': 'html-xul'},
		'differences_unique_to_js_baseline_against_xul.json': {'display_name': 'js-xul'},
		'differences_unique_to_js_baseline_against_html.json': {'display_name': 'js-html'}
	}


	x_names = []
	total_files = []
	unique_files = []
	for difference_name in diff_list:
		with open(os.path.join(RESULT_DIR, difference_name)) as f:
			diff_list[difference_name]['diff'] = json.load(f)

		x_names.append(diff_list[difference_name]['display_name'])
		total_files.append(diff_list[difference_name]['diff']['total_file_count'])
		unique_files.append(diff_list[difference_name]['diff']['report']['unique_file_count'])

	import numpy as np
	inds = np.arange(6)
	width = 0.35
	plt.bar(inds, unique_files, width, color='r', label='Unique Files')
	plt.bar(inds, total_files, width, color='g', alpha=0.3, label='Files with at least 1 difference')
	plt.xticks(range(len(total_files)), x_names)
	plt.legend()
	plt.show()


if __name__=="__main__":
	main()