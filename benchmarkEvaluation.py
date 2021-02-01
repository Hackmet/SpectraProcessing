"""
SPECTRA PROCESSING
Copyright (C) 2020 Josef Brandt, University of Gothenborg.
<josef.brandt@gu.se>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program, see COPYING.
If not, see <https://www.gnu.org/licenses/>.
"""


import matplotlib.pyplot as plt
import time
from sklearn.preprocessing import StandardScaler

import importData as io
from specCorrelation import correlate_spectra
from descriptors import DescriptorLibrary
from classification import test_randForestClassifier, balanceDataset
from functions import compareResultLists
from distort import *

t0 = time.time()
pathSampleSpec: str = r'Sample Spectra/sampleSpectra.npy'
pathSampleAssignments: str = r'Sample Spectra/origResults.txt'

# forceRegenerate: bool = False
# if forceRegenerate or not (os.path.exists(pathSampleSpec) and os.path.exists(pathSampleAssignments)):
#     print('regenerating sample spectra from files...')
#     origResults, testSpectra = io.get_test_spectra()
#     np.savetxt(pathSampleAssignments, origResults, fmt='%s')
#     np.save(pathSampleSpec, testSpectra)
# else:
#     origResults: List[str] = list(np.genfromtxt(pathSampleAssignments, dtype=str))
#     testSpectra: np.ndarray = np.load(pathSampleSpec)
#
# numSpectra: int = testSpectra.shape[1] - 1
# print(f'loading {len(origResults)} spectra took {time.time()-t0} seconds')

nSpecs = 10
nMaxDesc = 20
numVariationsTraining = 1000
numVariationsTesting = 1000

title = f'{nSpecs} differnt spectra, {nMaxDesc} max Descriptors, {numVariationsTraining} Variations for training\n' \
        f'{numVariationsTesting} Variations for testing'
print(title)
database = io.get_database(maxSpectra=nSpecs)
numSpectra = database.getNumberOfSpectra()

origResults = database._spectraNames.copy() * numVariationsTraining
testSpectra = create_n_distorted_copies(database.getSpectra(), numVariationsTraining-1, level=0.3, seed=1337)

descriptors: DescriptorLibrary = DescriptorLibrary()
descriptors.generate_from_specDatabase(database, maxDescPerSet=200)
# descriptors.getDescriptorPlot().show()
descriptors.optimize_descriptorSets(maxDescriptorsPerSet=nMaxDesc)
# descriptors.getDescriptorPlot().show()

featureMat: np.ndarray = descriptors.getCorrelationMatrixToSpectra(testSpectra)
featureMat = StandardScaler().fit_transform(featureMat)
X, y = featureMat.copy(), origResults.copy()
# X, y = balanceDataset(X, y)
t0 = time.time()
clf, uniqueAssignments = test_randForestClassifier(featureMat, origResults)
print(f'creating rdf classifier took {round(time.time()-t0, 2)} seconds')

testSpectra = create_n_distorted_copies(database.getSpectra(), numVariationsTesting-1, level=0.1, seed=1338)
origResults = database._spectraNames.copy() * numVariationsTesting

results = []
totalQualities = [[], []]
specPlotIndices = np.random.randint(testSpectra.shape[1]-1, size=5)
seed = 0
for i in range(10):
    print(f'----------------ITERATION {i+1} ----------------')
    if i > 0:
        testSpectra = add_noise(testSpectra, level=0.5, seed=seed)
        testSpectra = add_distortions(testSpectra, level=0.5, seed=seed)
        testSpectra = add_ghost_peaks(testSpectra, level=0.4, seed=seed)
        seed += 1

    if i % 2 == 0:
        fig = plt.figure()
        ax = fig.add_subplot()
        for offset, ind in enumerate(specPlotIndices):
            specToPlot = testSpectra[:, ind+1]
            specToPlot -= specToPlot.min()
            specToPlot /= specToPlot.max()
            ax.plot(testSpectra[:, 0], specToPlot + offset*0.2)
        ax.set_title(f'Random spectra of iteration {i+1}')

    t0 = time.time()
    dbResults = correlate_spectra(testSpectra, database)
    resultQualityDB, dbResultDict = compareResultLists(origResults, dbResults)
    print(f'Spec correlation took {round(time.time()-t0, 2)} seconds, {round(resultQualityDB)} % correct hits')

    t0 = time.time()
    featureMat = descriptors.getCorrelationMatrixToSpectra(testSpectra)
    featureMat = StandardScaler().fit_transform(featureMat)
    descriptorResults = [uniqueAssignments[i] for i in clf.predict(featureMat)]
    resultQualityDesc, descResultDict = compareResultLists(origResults, descriptorResults)
    print(f'Spectra Descriptor Application took {round(time.time()-t0, 2)} seconds, {round(resultQualityDesc)} % correct hits')

    totalQualities[0].append(resultQualityDB)
    totalQualities[1].append(resultQualityDesc)
    results.append([dbResultDict, descResultDict])

colorCycle = plt.rcParams['axes.prop_cycle'].by_key()['color']

resultFig = plt.figure()
ax = resultFig.add_subplot()
ax.plot(totalQualities[0], label='database matching')
ax.plot(totalQualities[1], label='RDF Spec Descriptors')
ax.set_xlabel('-- Decreasing spectra quality -->', fontsize=15)
ax.set_ylabel('Hit Quality (%)', fontsize=15)
ax.set_ylim(0, 100)
ax.legend(fontsize=13)
ax.set_title(title)
resultFig.show()
