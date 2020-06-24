from pathlib import Path
import re
import pandas as pd
from os.path import join
from spectrai.core import get_astorga_config


DATA_SPECTRA, DATA_MEASUREMENTS = get_astorga_config()


def load_spectra(path=DATA_SPECTRA):
    """ Returns DRIFT/MIRs spectra, Romina's data, Argentina, 2015"""
    path = Path(path)
    df_list = []
    for i, f in enumerate(path.glob('*.CSV')):
        result = re.search('AR(.*)Average', f.name)
        usecols = [0, 1] if i == 0 else [1]
        names = ['wavenumber', 'AR' + '{}'.format(result.group(1))]
        df_list.append(pd.read_csv(join(f), sep=';',
                                   usecols=usecols, names=names))

    df = pd.concat(df_list, axis=1).set_index('wavenumber')
    return df[sorted(df.columns)].sort_index(ascending=False)


def load_measurements(path=DATA_MEASUREMENTS,
                      analytes=['Fe', 'Ti', 'Ca', 'P', 'Ba']):
    """ Returns XRF measurements of soil samples, Argentina, 2015"""
    path = Path(path)
    df_labels = pd.read_excel(path, sheet_name='XRF contents FINAL')
    df_labels.drop([0, 31], axis=0, inplace=True)
    return df_labels[['Arg Code'] + analytes]


def load_data(path_X=DATA_SPECTRA,
              path_y=DATA_MEASUREMENTS):
    """ Returns all available data amenable to DL models as numpy arrays."""
    path_X = Path(path_X)
    path_y = Path(path_y)
    X = load_spectra(path_X)
    y = load_measurements(path_y)

    X_names = X.index.values
    instances_id = X.columns.values
    X = X.to_numpy(dtype='float32').T
    y_names = y.iloc[:, 1:].columns.values
    y = y.iloc[:, 1:].to_numpy(dtype='float32')
    return (X, X_names, y, y_names, instances_id)
