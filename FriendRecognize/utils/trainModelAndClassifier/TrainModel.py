import os
import random

from tqdm import tqdm

from FriendRecognize.utils.UsefulMethods import ImageType, Labeler, extract_features_for_training, Feature
from FriendRecognize.utils.object.TrainImage import TrainImage
from FriendRecognize.utils.trainModelAndClassifier.Classifier import Classifier, print_metrics


def get_image_with_feature(config, feature):
    path = config['data']['training'] + config['features']['with'][feature]
    img_type = ImageType.FEATURE.value
    return {'path': path, 'type': img_type}


def get_image_without_feature(config, feature):
    path = config['data']['training'] + config['features']['without'][feature]
    img_type = ImageType.NO_FEATURE.value
    return {'path': path, 'type': img_type}


def get_model(config, feature):
    return config['models'][feature]


def generate_empty_dataset():
    return {'train': {0: [], 1: []}, 'val': {0: [], 1: []}}


def generation_datasets(images_with_feature, images_without_feature, train_val_ratio, kind_of_feature):
    src = [images_without_feature, images_with_feature]
    desc_train = ["Fill trainingSet set of No ", "Fill trainingSet set of "]
    desc_val = ["Fill validation set of No ", "Fill validation set of "]
    dataset = generate_empty_dataset()
    # Fill trainingSet and validation set
    for source in src:
        folder_path = source['path']
        files = os.listdir(folder_path)
        has_feature = source['type']
        number_of_files = int(len(files) * train_val_ratio)
        for file_name in tqdm(random.sample(files, number_of_files),
                              desc=desc_train[has_feature] + str(kind_of_feature)):
            dataset['train'][has_feature].append(TrainImage(file_name, folder_path))
        for file_name in tqdm(files, desc=desc_val[has_feature] + str(kind_of_feature)):
            if not any(train_image.is_equal(file_name) for train_image in dataset['train'][has_feature]):
                dataset['val'][has_feature].append(TrainImage(file_name, folder_path))
    return dataset


def generation_features(images_with_feature, images_without_feature, train_val_ratio, predictor, detector,
                        kind_of_feature):
    print("\nDataset...")
    dataset_images = generation_datasets(images_with_feature,
                                         images_without_feature,
                                         train_val_ratio,
                                         kind_of_feature)
    print("\nLabeler...")
    labeler = Labeler(dataset_images)
    print("\nFeature...")
    return extract_features_for_training(dataset_images,
                                         labeler,
                                         detector,
                                         predictor,
                                         kind_of_feature)


def training(X_train, y_train, X_val, y_val, fitted_model_path, metrics=True):
    model = Classifier()
    print("\nFit...")
    y_pred = model.fit(X_train, y_train, X_val)
    if metrics:
        print_metrics(y_val, y_pred)
    model.save(fitted_model_path)
    return y_pred


def train(config, features, detector, predictor, train_ratio=0.7):
    for feature in features:
        images_with_feature = get_image_with_feature(config, feature)
        images_without_feature = get_image_without_feature(config, feature)
        fitted_model = get_model(config, feature)
        kind_of_feature = Feature(feature)
        if not os.path.exists(fitted_model):
            os.makedirs(fitted_model)
        # Generation feature
        X_train, y_train, X_val, y_val = generation_features(images_with_feature,
                                                             images_without_feature,
                                                             train_ratio,
                                                             predictor,
                                                             detector,
                                                             kind_of_feature)
        # Fitting and prediction
        training(X_train,
                 y_train,
                 X_val,
                 y_val,
                 fitted_model)
