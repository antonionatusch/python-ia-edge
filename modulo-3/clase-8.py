# este script es sun lo visto en: https://www.youtube.com/watch?v=il8dMDlXrIE
import os
import pickle
from skimage.io import imread
from skimage.transform import resize
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

# prepare data
input_dir = "/home/tusch/Desktop/ia-edge-tech-lab/python-ia-edge/modulo-3/clf-data/"
categories = ["empty", "not_empty"]
resize_output_shape = (15, 15)

data = []
labels = []

# iterate, load/read, format images that fits classifier

for category_idx, category in enumerate(categories):
    for file in os.listdir(os.path.join(input_dir, category)):
        img_path = os.path.join(input_dir, category, file)
        # read and save to list
        img = imread(img_path)
        img = resize(img, resize_output_shape)
        data.append(img.flatten())  # pyright: ignore[reportAttributeAccessIssue]
        labels.append(category_idx)

data = np.asarray(data)
labels = np.asarray(labels)

# train / test split
x_train, x_test, y_train, y_test = train_test_split(
    data, labels, test_size=0.2, shuffle=True, stratify=labels
)

# train image classifier
classifier = SVC()

# train 3x4 = 12 classifiers, choose the best.
parameters = [{"gamma": [0.01, 0.001, 0.0001], "C": [1, 10, 100, 1000]}]

grid_search = GridSearchCV(classifier, parameters)

grid_search.fit(x_train, y_train)

# test performance

# gets best classifier
best_estimator = grid_search.best_estimator_

y_prediction = best_estimator.predict(x_test)

score = accuracy_score(y_prediction, y_test)

print("{}% of samples were correctly classified".format(str(score * 100)))

pickle.dump(best_estimator, open("./model.p", "wb"))
