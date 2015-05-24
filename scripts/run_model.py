from math import sqrt
from os.path import abspath, dirname, join
import sys
from time import localtime, strftime

sys.path.append(abspath(dirname(dirname(__file__))))
from utils.data_io import load_numpy_array_from_file
from utils.data_stats import load_stats_from_file
from utils.data_paths import DATA_DIR_PATH, RESULTS_DIR_PATH


def calculate_rmse(true_ratings, predictions):
    return sqrt(((predictions - true_ratings) ** 2).mean())


def predict_and_save_rmse(model, test_points, train_set_name, test_set_name, epochs=None):
    print('Predicting "{test}" ratings'.format(test=test_set_name))
    predictions = model.predict(test_points)
    true_ratings = test_points[:, 3]
    rmse = calculate_rmse(true_ratings, predictions)
    print('RMSE:', rmse)
    epochs_string = '' if epochs is None else ('_%sepochs' % epochs)
    features = model.num_features
    features_string = '' if features is None else ('_%sfeatures' % features)
    time_format = '%b-%d-%Hh-%Mm'
    rmse_file_name = ('{name}_{train}{e}{f}_rmse_{test}_{time}.txt'
                      .format(name=model.__class__.__name__,
                              train=train_set_name, test=test_set_name,
                              e=epochs_string, f=features_string,
                              time=strftime(time_format, localtime())))
    rmse_file_name = rmse_file_name
    save_rmse(rmse, rmse_file_name, append=True)


def save_model(model, train_set_name, epochs=None, feature_epoch_order=False):
    time_format = '%b-%d-%Hh-%Mm'
    times = strftime(time_format, localtime())
    times += '_to_' + strftime(time_format, localtime())
    epochs_string = '' if epochs is None else ('_%sepochs' % epochs)
    features = model.num_features
    features_string = '' if features is None else ('_%sfeatures' % features)
    order_string = '' if feature_epoch_order is False else ('_feature_epoch_order')
    template_file_name = ('{name}_{train}{e}{f}_xxx{order}_{times}'
                          .format(name=model.__class__.__name__,
                                  train=train_set_name, e=epochs_string,
                                  f=features_string, order=order_string, times=times))
    model_file_name = template_file_name.replace('xxx', 'model') + '.p'
    model.save(model_file_name)


def run(model, train_set_name, test_set_name, epochs=None, features=None,
        feature_epoch_order=False, create_files=True, run_multi=False):
    print('Training {model_class} on "{train}" ratings'
          .format(model_class=model.__class__.__name__, train=train_set_name))
    if not create_files:
        print("WARNING: 'nofile' flag detected. No model file will be " +
              "saved to disk after this run.\n***MODEL WILL BE LOST.")
        confirm = input("Are you sure you want to continue? [Y/n]")
        if confirm == 'Y' or confirm == 'y' or confirm == '':
            pass
        else:
            return
    if epochs is not None:
        print('Number of epochs:', epochs)
    if features is not None:
        print('Number of features:', features)
    train_file_path = join(DATA_DIR_PATH, train_set_name + '.npy')
    stats_file_path = join(DATA_DIR_PATH, train_set_name + '_stats.p')

    model.debug = True
    train_points = load_numpy_array_from_file(train_file_path)
    stats = load_stats_from_file(stats_file_path)
    test_file_path = join(DATA_DIR_PATH, test_set_name + '.npy')
    test_points = load_numpy_array_from_file(test_file_path)
    if not run_multi:
        if not feature_epoch_order:
            model.train(train_points, stats=stats, epochs=epochs)
        else:
            model.train_feature_epoch(train_points=train_points, stats=stats, epochs=epochs)
    else:
        print("Training multi")
        for epoch in range(epochs):
            if epoch == 0:
                model.train(train_points, stats=stats, epochs=1)
            else:
                model.train_more(epochs=1)
            if create_files:
                predict_and_save_rmse(model, test_points=test_points,
                                      train_set_name=train_set_name,
                                      test_set_name=test_set_name,
                                      epochs=epoch+1)

    model.train_points = None

    if create_files:
        save_model(model, train_set_name=train_set_name,
                   epochs=epochs, feature_epoch_order=feature_epoch_order)
        if not run_multi:
            # duplicate save if run_multi
            predict_and_save_rmse(model, test_points=test_points,
                                  train_set_name=train_set_name,
                                  test_set_name=test_set_name,
                                  epochs=epochs)


def old_run_multi(model, train_set_name, test_set_name, epochs=None, features=None):
    print('Training {model_class} on "{train}" ratings'
          .format(model_class=model.__class__.__name__, train=train_set_name))
    if epochs is not None:
        print('Maximum number of epochs:', epochs)
    if features is not None:
        print('Number of features:', features)

    train_file_path = join(DATA_DIR_PATH, train_set_name + '.npy')
    stats_file_path = join(DATA_DIR_PATH, train_set_name + '_stats.p')
    train_points = load_numpy_array_from_file(train_file_path)
    stats = load_stats_from_file(stats_file_path)
    test_file_path = join(DATA_DIR_PATH, test_set_name + '.npy')
    test_points = load_numpy_array_from_file(test_file_path)

    epochs_string = '' if epochs is None else ('_%sepochs' % epochs)
    features_string = '' if features is None else ('_%sfeatures' % features)
    time_format = '%b-%d-%Hh-%Mm'
    rmse_file_name = ('svd_{train}{e}{f}_rmse_{test}_{time}.txt'
                      .format(train=train_set_name, test=test_set_name,
                              e=epochs_string, f=features_string,
                              time=strftime(time_format, localtime())))

    model.debug = True
    for epoch in range(epochs):
        print('Training epoch {}:'.format(epoch))
        if epoch == 0:
            model.train(train_points, stats=stats, epochs=1)
        else:
            model.train_more(epochs=1)
        print('Predicting "{test}" ratings'.format(test=test_set_name))
        predictions = model.predict(test_points)
        true_ratings = test_points[:, 3]
        rmse = calculate_rmse(true_ratings, predictions)
        print('RMSE:', rmse)
        rmse_file_name = rmse_file_name
        save_rmse(rmse, rmse_file_name, append=True)
    model.train_points = None


def save_predictions(predictions, predictions_file_name):
    predictions_file_path = join(RESULTS_DIR_PATH, predictions_file_name)
    with open(predictions_file_path, 'w+') as predictions_file:
        predictions_file.writelines(['{:.3f}\n'.format(p) for p in predictions])


def save_rmse(rmse, rmse_file_name, append=False):
    rmse_file_path = join(RESULTS_DIR_PATH, rmse_file_name)
    write_format = 'w+'
    if append:
        write_format = 'a+'
    with open(rmse_file_path, write_format) as rmse_file:
        rmse_file.write('{}\n'.format(rmse))