from pathlib import Path
import re
import pandas as pd
from .base import DATA_RAW
import brukeropusreader


DATA_FOLDER = DATA_RAW / 'schmitter_vnm_2010'
DATA_SPECTRA = DATA_FOLDER / 'mir-models'
DATA_SPECTRA_REP = DATA_FOLDER / 'vietnam-petra'
DATA_MEASUREMENTS = DATA_FOLDER / 'mir-models' / \
    '20090215-soil-database-mirs.xls'


def load_spectra_schmitter_vnm(path=DATA_SPECTRA):
    """ Returns DRIFT/MIRs spectra, Petra's data, Vietnam, 2007-2008"""
    path = Path(path)
    df_list = []
    for i, f in enumerate(path.glob('*.*')):
        if f.suffix != '.xls':
            file = brukeropusreader.read_file(f)
            spectrum = pd.Series(file['AB'])
            spectrum_name = _clean_column_name(f.name)
            if i == 0:
                wavelength = pd.Series(file.get_range("AB"))
                data = {'wavenumber': wavelength, spectrum_name: spectrum}
            else:
                data = {spectrum_name: spectrum}

            df_list.append(pd.DataFrame(data))

    return pd.concat(df_list, axis=1, ignore_index=False, sort=False).set_index('wavenumber')


def load_spectra_rep_schmitter_vnm(path=DATA_SPECTRA_REP):
    """ Returns DRIFT/MIRs spectra and their replicates, Petra's data, Vietnam, 2007-2008"""
    path = Path(path)
    df_list = []
    _ids = []
    for i, f in enumerate(path.glob('*.0')):
        _id = int(re.search(r'(.*?)_', f.name).group(1))
        if (_id in range(3179, 4922)) and (_id not in _ids):
            file = brukeropusreader.read_file(f)
            if 'AB' in file:
                _ids.append(_id)
                spectrum = pd.Series(file['AB'])
                spectrum_name = _id
                if len(df_list) == 0:
                    wavelength = pd.Series(file.get_range('AB'))
                    data = {'wavenumber': wavelength, spectrum_name: spectrum}
                else:
                    data = {spectrum_name: spectrum}

                df_list.append(pd.DataFrame(data))
    df = pd.concat(df_list, axis=1, ignore_index=False, sort=False).set_index('wavenumber')
    return df.reindex(sorted(df.columns), axis=1)


def load_measurements_schmitter_vnm(path=DATA_MEASUREMENTS):
    path = Path(path)
    df_labels = pd.read_excel(path, sheet_name='Sheet1', usecols=list(range(2, 13)), na_values='-')
    df_labels.columns = ['total_label', 'mir_label', 'TC', 'TOC', 'TIC', 'TN',
                         'CEC', 'K', 'FCAVER', 'FCIAVER', 'FSAAVER']
    return df_labels.set_index('mir_label')


def load_data_schmitter_vnm(path_X=DATA_SPECTRA,
                            path_y=DATA_MEASUREMENTS):
    """ Returns all available data amenable to DL models as numpy arrays."""
    path_X = Path(path_X)
    path_y = Path(path_y)
    X = load_spectra_schmitter_vnm(path_X)
    y = load_measurements_schmitter_vnm(path_y)

    common_ids = _get_common_ids(X, y)
    y = y.loc[common_ids, :]
    X = X[common_ids]

    X_names = X.index.values
    instances_id = X.columns.values
    X = X.to_numpy(dtype='float32').T
    y_names = y.columns.values[1:]

    # Total to mir labels lookup table
    lookup = dict(zip(y.iloc[:, 0], instances_id))
    y = y.iloc[:, 1:].to_numpy(dtype='float32')
    return (X, X_names, y, y_names, instances_id, lookup)


def _clean_column_name(name):
    if 'Av' in name:
        return 'Av{:03d}'.format(int(name.split('Av.')[1]))
    elif '.0' in name:
        return name.replace('.0', '')
    else:
        return name


def _get_common_ids(X, y):
    measurement_ids = set(y.index.values)
    spectra_ids = set(list(X.columns))
    common_ids = list(measurement_ids.intersection(spectra_ids))
    common_ids.sort()
    return common_ids
