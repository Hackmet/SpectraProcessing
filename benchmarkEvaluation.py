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
from typing import List
import numpy as np

import importData as io
from descriptors import DescriptorLibrary
from classification import RandomDecisionForest
from evaluationTest import testEvaluationOnSpectra
from specCorrelation import CorrelationMode
from testSpectra import TestSpectra

preprocessSpectra: bool = True  # Whether or not subtract baseline and normalize spectra for database search
correlationModes: List[CorrelationMode] = [CorrelationMode.PEARSON, CorrelationMode.SFEC]
nMaxDBSpecs: int = 50  # maximum number of spectra in the database
nMaxDesc: int = 20  # maximum number of descriptors per spectrum

testSpecObj = TestSpectra()
# testSpecObj.loadFromNPY()
testSpecObj.generateFromRefSpecs(plasticContent=1.0, numVariations=100, maxPlastTypes=nMaxDBSpecs)
# testSpecObj.generateFromSampleDir()

database = io.get_database(maxSpectra=nMaxDBSpecs, includeNonPlastic=False)
database.preprocessSpectra()

descriptors: DescriptorLibrary = DescriptorLibrary()
descriptors.generate_from_specDatabase(database, maxDescPerSet=200)
descriptors.optimize_descriptorSets(maxDescriptorsPerSet=nMaxDesc)
rdf: RandomDecisionForest = RandomDecisionForest(descriptors)

trainSpectra: np.ndarray = testSpecObj.getPolymerSpectra()
trainAssignments: List[str] = testSpecObj.getPolymerAssignments()
rdf.trainWithSpectra(trainSpectra, trainAssignments)

testSpectra = testSpecObj.getAllSpectra()
testAssignments = testSpecObj.getAllAssignments()
print("testing with", testSpecObj.getNumberOfPlastics(), "plastic spectra, plastic content:", testSpecObj.getPlasticContent())

figure, results = testEvaluationOnSpectra(testSpectra, testAssignments, database, rdf, preprocessSpectra,
                                          numIterations=10, dbCutoff=0.0, corrModes=correlationModes)
figure.show()
