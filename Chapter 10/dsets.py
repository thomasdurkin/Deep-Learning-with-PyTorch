import functools
import glob
import os
import csv

from collections import namedtuple

CandidateInfoTuple = namedtuple('CandidateInfoTuple',
								'isNodule_bool, diameter_mm, series_uid, center_xyz')

# Cache function call to store results in memory
@functools.lru_cahce(1)
def getCandidateInfoList(requireOnDisk_bool = True):
	mhd_list = glob.glob('')
	presentOnDisk_set = {os.path.split(p)[-1][:-4] for p in mhd_list}

	diameter_dict = {}
	with open(f"./annotations.csv", "r") as f:
		for row in list(csv.reader(f))[1:]:
			series_uid = row[0]
			annotationCenter_xyz = tuple([float(x) for x in row [1:4]])
			annotationDiameter_mm = float(row[4])

			diameter_dict.setdefault(series_uid, []).append((annotationCenter_xyz, annotationDiameter_mm))

	candidateInfo_list = []
	with open(f"./candidates.csv", "r") as f:
		for row in list(csv.reader(f))[1:]:
			series_uid = row[0]

			# If a series_uid is not present, we have not downloaded that subset of data yet
			if series_uid not in presentOnDisk_set and requireOnDisk_bool:
				continue	
			
			candidateCenter_xyz = tuple([float(x) for x in row[1:4]])
			isNodule_bool = bool(int(row[4]))

			candidateDiameter_mm = 0.0
			for annotation_tup in diameter_dict.get(series_uid, []):
				annotationCenter_xyz, annotationDiameter_mm = annotation_tup
				
				for i in range(3):
					delta_mm = abs(candidateCenter_xyz[i] - annotationCenter_xyz[i])
					# Bounding box check. Divide diameter by 2 and then divide radius by 2 to require
					# that the two nodule center points not be too far apart relative to the size of the nodule
					if delta_mm > annotationDiameter_mm / 4:
						break
					else:
						candidateDiameter_mm = annotationDiameter_mm
						break

			candidateInfo_list.append(CandidateInfoTuple(isNodule_bool,
														 candidateDiameter_mm,
														 series_uid,
														 candidateCenter_xyz))
	# Sort by largest nodule
	candidateInfo_list.sort(reverse=True)
	return candidateInfo_list