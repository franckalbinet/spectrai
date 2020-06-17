"""Clean, bundle and create API to load KSSL data

The KSSL database is provided as a Microsoft Access database designed
as an OLTP. The purposes of this module are: (i) to export all tables
as independent .csv files to make it platform independent; (ii) to
make it amenable to multi-dimensional analytical queries (OLAP);
(iii) to provide an API for easy loading of the dataset.
"""
import subprocess
from pathlib import Path
from .base import DATA_HOME, select_rows
import pandas as pd
import re
import opusFC  # Ref.: https://stuart-cls.github.io/python-opusfc-dist/
from tqdm import tqdm


DATA_KSSL = DATA_HOME / 'kssl'
DATA_NORM = DATA_KSSL / 'normalized'
DATA_SPECTRA = DATA_KSSL / 'spectra'
DB_NAME = 'All_Spectra_Access_Portable 2-20-20.accdb'


def access_to_csv(in_folder=None, out_folder=DATA_NORM, db_name=DB_NAME):
    """Export KSSL '.accdb' tables to individual '.csv' files

    Linux-like OS only as depends on 'mdbtools'
    https://github.com/brianb/mdbtools

    Parameters
    ----------
    in_folder: string, optional
        Specify the path of the folder containing the '.accdb' KSSL file

    out_folder: string, optional
        Specify the path of the folder that will contain exported tables

    db_name: string, optional
        Specify name of the KSSL Microsoft Access database

    Returns
    -------
    None
    """
    in_folder = Path(in_folder)
    out_folder = Path(out_folder)

    if not in_folder.exists():
        raise IOError('in_folder not found.')

    if not out_folder.exists():
        out_folder.mkdir(parents=True)

    script_name = Path(__file__).parent / 'scripts/access2csv.sh'
    out = subprocess.run([script_name, in_folder / DB_NAME, out_folder])

    if out.returncode == 0:
        print('KSSL tables exported successfully to .csv files.')
    else:
        raise OSError('Execution of access2csv.sh failed.')


def _get_layer_analyte_tbl():
    """Return relevant subset of `layer_analyte.csv` KSSL DB table

    Notes
    ----
    Only `master_prep_id` relevant to MIRS analysis selected

    `calc_value` are by default `str` as possibly containing
    values such as (slight, 1:2, ...). Only numeric ones are
    selected
    """
    return pd.read_csv(DATA_NORM / 'layer_analyte.csv', low_memory=False) \
        .dropna(subset=['analyte_id', 'calc_value']) \
        .pipe(select_rows, {
            'master_prep_id': lambda d: d in [18, 19, 27, 28],
            'calc_value': lambda d: re.search(r'[a-zA-Z]|:|\s', str(d)) is None}) \
        .loc[:, ['lay_id', 'analyte_id', 'calc_value']] \
        .astype({'calc_value': float})


def _get_layer_tbl():
    """Return relevant subset of `analyte.csv` KSSL DB table"""
    return pd.read_csv(DATA_NORM / 'layer.csv', low_memory=False) \
        .loc[:, ['lay_id', 'lims_pedon_id', 'lims_site_id', 'lay_depth_to_top']] \
        .dropna() \
        .astype({'lims_pedon_id': 'int32', 'lims_site_id': 'int32'})


def _get_sample_tbl():
    """Return relevant subset of `sample.csv` KSSL DB table"""
    return pd.read_csv(DATA_NORM / 'sample.csv', low_memory=False) \
        .pipe(select_rows, {'smp_id': lambda d: d > 1000}) \
        .loc[:, ['smp_id', 'lay_id']]


def _get_mirs_det_tbl(valid_name=['XN', 'XS']):
    """TO BE TESTED"""
    return pd.read_csv(DATA_NORM / 'mir_scan_det_data.csv', low_memory=False) \
        .dropna(subset=['scan_path_name', 'mir_scan_mas_id']) \
        .loc[:, ['mir_scan_mas_id', 'scan_path_name']] \
        .pipe(select_rows, {
            'scan_path_name': lambda d: re.search(r'X.', str(d))[0] in valid_name})


def _get_mirs_mas_tbl():
    """TO BE TESTED"""
    return pd.read_csv(DATA_NORM / 'mir_scan_mas_data.csv', low_memory=False) \
        .loc[:, ['smp_id', 'mir_scan_mas_id']]


def _get_lookup_smp_id_scan_path():
    """TO BE TESTED"""
    return pd.merge(_get_mirs_mas_tbl(), _get_mirs_det_tbl(), on='mir_scan_mas_id', how='inner') \
        .loc[:, ['smp_id', 'scan_path_name']] \
        .astype({'smp_id': int, 'scan_path_name': 'string'})


def build_analyte_dim_tbl(out_folder=DATA_KSSL):
    """Return relevant subset of `analyte.csv` KSSL DB table"""
    df = pd.read_csv(DATA_NORM / 'analyte.csv') \
        .loc[:, ['analyte_id', 'analyte_name', 'analyte_abbrev', 'uom_abbrev']]
    df.to_csv(out_folder / 'analyte_dim_tbl.csv', index=False)
    return df


def build_taxonomy_dim_tbl(out_folder=DATA_KSSL):
    """Return relevant subset of `lims_ped_tax_hist.csv` KSSL DB table

    Notes
    ----
    A same `lims_pedon_id` column as duplicates (several classifi. version).
    Only `taxonomic_classification_type` = `'sampled as'` should be considered.
    """
    df = pd.read_csv(DATA_NORM / 'lims_ped_tax_hist.csv') \
        .pipe(select_rows, {'taxonomic_classification_type': lambda d: d == 'sampled as'}) \
        .loc[:, ['lims_pedon_id', 'taxonomic_order', 'taxonomic_suborder',
                 'taxonomic_great_group', 'taxonomic_subgroup']]
    df.to_csv(out_folder / 'taxonomy_dim_tbl.csv', index=False)
    return df


def build_location_dim_tbl(out_folder=DATA_KSSL):
    pass


def build_sample_analysis_fact_tbl(out_folder=DATA_KSSL):
    df = pd.merge(
        pd.merge(_get_layer_tbl(), _get_sample_tbl(), on='lay_id'),
        _get_layer_analyte_tbl(), on='lay_id')

    df.to_csv(out_folder / 'sample_analysis_fact_tbl.csv', index=False)
    return df


def build_kssl_star_tbl():
    print('Building analyte_dim_tbl...')
    build_analyte_dim_tbl()
    print('Building taxonomy_dim_tbl...')
    build_taxonomy_dim_tbl()
    print('Building spectra_dim_tbl...')
    bundle_spectra_dim_tbl()
    print('Building sample_analysis_fact_tbl...')
    build_sample_analysis_fact_tbl()
    print('Success!')


def _slices(len_array, nb_chunks=3):
    step = len_array // nb_chunks
    bounds = [x*step for x in range(nb_chunks)] + [len_array]
    return zip(bounds, bounds[1:])


def export_spectra(in_folder=None, out_folder=DATA_KSSL,
                   nb_decimals=4, max_wavenumber=4000, valid_name=['XN', 'XS'], nb_chunks=1):
    """TO BE TESTED"""
    in_folder = Path(in_folder)
    out_folder = Path(out_folder)

    if not in_folder.exists():
        raise IOError('in_folder not found.')

    if not out_folder.exists():
        out_folder.mkdir(parents=True)

    columns = None
    valid_files = [f for f in in_folder.rglob('*.0')
                   if re.search(r'X.', f.name)[0] in valid_name]

    for (l_bound, u_bound) in list(_slices(len(valid_files), nb_chunks)):
        columns = None
        rows_list = []
        for i, f in enumerate(tqdm(valid_files[l_bound:u_bound])):
            dbs = opusFC.listContents(f)
            if dbs:
                data = opusFC.getOpusData(str(f), dbs[0])
                row = [f.name] + list(data.y[data.x <= max_wavenumber])
                rows_list.append(row)
                if columns is None:
                    columns = list((data.x[data.x <= max_wavenumber]).astype(int))
        df = pd.DataFrame(rows_list, columns=['id'] + list(columns))
        df = df.round(nb_decimals)
        df.to_csv(out_folder / 'spectra_{}_{}.csv'.format(l_bound, u_bound-1), index=False)


def bundle_spectra_dim_tbl(in_folder=DATA_SPECTRA, out_folder=DATA_KSSL, with_replicates=False):
    """TO BE TESTED"""
    all_files = list(in_folder.glob('*.csv'))
    li = []
    columns = None
    for filename in tqdm(all_files):
        if columns is None:
            columns = pd.read_csv(filename).columns
        df = pd.read_csv(filename, header=None, skiprows=1)
        df.columns = columns
        df = _get_lookup_smp_id_scan_path() \
            .merge(df, left_on='scan_path_name', right_on='id', how='inner') \
            .drop(['id', 'scan_path_name'], axis=1)

        if not with_replicates:
            df = df.groupby('smp_id').mean()

        li.append(df)

    df = pd.concat(li)
    df = df.reset_index()
    print('Writing spectra_dim_tbl.csv...')
    df.to_csv(out_folder / 'spectra_dim_tbl.csv', index=False)
    return df.reset_index()


def load_spectra(in_folder=DATA_KSSL):
    return pd.read_csv(in_folder / 'spectra_dim_tbl.csv')


def load_taxonomy(in_folder=DATA_KSSL):
    return pd.read_csv(in_folder / 'taxonomy_dim_tbl.csv') \
            .replace({'mollisol': 'mollisols'})


def load_fact_tbl(in_folder=DATA_KSSL):
    return pd.read_csv(in_folder / 'sample_analysis_fact_tbl.csv')


def load_analytes(in_folder=DATA_KSSL):
    return pd.read_csv(in_folder / 'analyte_dim_tbl.csv')


def get_analytes_like(substring='otas'):
    df = load_analytes()
    return df[df['analyte_name'].str.contains(substring)]


def load_target(analyte=[725]):
    df = load_fact_tbl()
    df = df[df['analyte_id'].isin(analyte)]
    df_tax = load_taxonomy()[['lims_pedon_id', 'taxonomic_order']]
    df = df.merge(df_tax, on='lims_pedon_id', how='left')
    return df[['smp_id', 'taxonomic_order', 'calc_value']]


def load_data_kssl(in_folder=DATA_KSSL, analyte=[]):
    # merge spectra-target
    # return as tuples (X, y, X_names, y_names)
    pass
