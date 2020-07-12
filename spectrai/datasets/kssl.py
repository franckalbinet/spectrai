"""Clean, bundle and create API to load KSSL data

The KSSL database is provided as a Microsoft Access database designed
as an OLTP. The purposes of this module are: (i) to export all tables
as independent .csv files to make it platform independent; (ii) to
make it amenable to multi-dimensional analytical queries (OLAP);
(iii) to provide an API for easy loading of the dataset as numpy arrays.

For further information on KSSL database contact:
    * https://www.nrcs.usda.gov/wps/portal/nrcs/main/soils/research/
"""
import subprocess
from pathlib import Path
from .base import select_rows, chunk
from spectrai.core import get_kssl_config
import pandas as pd
import re
import opusFC  # Ref.: https://stuart-cls.github.io/python-opusfc-dist/
from tqdm import tqdm


DATA_KSSL, DATA_NORM, DATA_SPECTRA, DB_NAME = get_kssl_config()


def access_to_csv(in_folder=None, out_folder=DATA_NORM, db_name=DB_NAME):
    """Exports KSSL '.accdb' tables to individual '.csv' files.

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
    """Returns relevant clean subset of `layer_analyte.csv` KSSL DB table.

    Notes
    ----
    Only `master_prep_id` relevant to MIRS analysis selected

    `calc_value` are by default `str` as possibly containing
    values such as (slight, 1:2, ...). Only numeric ones are
    selected

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    return pd.read_csv(DATA_NORM / 'layer_analyte.csv', low_memory=False) \
        .dropna(subset=['analyte_id', 'calc_value']) \
        .pipe(select_rows, {
            'master_prep_id': lambda d: d in [18, 19, 27, 28],
            'calc_value': lambda d: re.search(r'[a-zA-Z]|:|\s', str(d)) is None}) \
        .loc[:, ['lay_id', 'analyte_id', 'calc_value']] \
        .astype({'calc_value': float})


def _get_layer_tbl():
    """Returns relevant clean subset of `analyte.csv` KSSL DB table.

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    return pd.read_csv(DATA_NORM / 'layer.csv', low_memory=False) \
        .loc[:, ['lay_id', 'lims_pedon_id', 'lims_site_id', 'lay_depth_to_top']] \
        .dropna() \
        .astype({'lims_pedon_id': 'int32', 'lims_site_id': 'int32'})


def _get_sample_tbl():
    """Returns relevant clean subset of `sample.csv` KSSL DB table.

    Notes
    ----
    Only `smp_id` > 1000  relevant to MIRS analysis selected

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    return pd.read_csv(DATA_NORM / 'sample.csv', low_memory=False) \
        .pipe(select_rows, {'smp_id': lambda d: d > 1000}) \
        .loc[:, ['smp_id', 'lay_id']]


def _get_mirs_det_tbl(valid_name=['XN', 'XS']):
    """Returns relevant clean subset of `mir_scan_det_data.csv` KSSL DB table.

    Notes
    ----
    Only `scan_path_name` containing valid substring `['XN', 'XS'] by default.

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    return pd.read_csv(DATA_NORM / 'mir_scan_det_data.csv', low_memory=False) \
        .dropna(subset=['scan_path_name', 'mir_scan_mas_id']) \
        .loc[:, ['mir_scan_mas_id', 'scan_path_name']] \
        .pipe(select_rows, {
            'scan_path_name': lambda d: re.search(r'X.', str(d))[0] in valid_name})


def _get_mirs_mas_tbl():
    """Returns relevant clean subset of `mir_scan_mas_data.csv` KSSL DB table.

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    return pd.read_csv(DATA_NORM / 'mir_scan_mas_data.csv', low_memory=False) \
        .loc[:, ['smp_id', 'mir_scan_mas_id']]


def _get_lookup_smp_id_scan_path():
    """Returns relevant clean subset of `mir_scan_mas_data.csv` KSSL DB table.

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    return pd.merge(_get_mirs_mas_tbl(), _get_mirs_det_tbl(), on='mir_scan_mas_id', how='inner') \
        .loc[:, ['smp_id', 'scan_path_name']] \
        .astype({'smp_id': int, 'scan_path_name': 'string'})


def build_analyte_dim_tbl(out_folder=DATA_KSSL):
    """Builds/creates analyte_dim dim table (star schema) for KSSL dataset

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """

    df = pd.read_csv(DATA_NORM / 'analyte.csv') \
        .loc[:, ['analyte_id', 'analyte_name', 'analyte_abbrev', 'uom_abbrev']]
    df.to_csv(out_folder / 'analyte_dim_tbl.csv', index=False)
    return df


def build_taxonomy_dim_tbl(out_folder=DATA_KSSL):
    """Returns relevant subset of `lims_ped_tax_hist.csv` KSSL DB table

    Notes
    ----
    A same `lims_pedon_id` column as duplicates (several classifi. version).
    Only `taxonomic_classification_type` = `'sampled as'` should be considered.

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
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
    """Builds/creates sample_analysis fact table (star schema) for KSSL dataset

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected columns, rows
    """
    df = pd.merge(
        pd.merge(_get_layer_tbl(), _get_sample_tbl(), on='lay_id'),
        _get_layer_analyte_tbl(), on='lay_id')

    df.to_csv(out_folder / 'sample_analysis_fact_tbl.csv', index=False)
    return df


def build_kssl_star_tbl():
    """Builds/creates star schema version of the KSSL DB"""
    print('Building analyte_dim_tbl...')
    build_analyte_dim_tbl()
    print('Building taxonomy_dim_tbl...')
    build_taxonomy_dim_tbl()
    print('Building spectra_dim_tbl...')
    bundle_spectra_dim_tbl()
    print('Building sample_analysis_fact_tbl...')
    build_sample_analysis_fact_tbl()
    print('Success!')


def export_spectra(in_folder=None, out_folder=DATA_KSSL,
                   nb_decimals=4, max_wavenumber=4000, valid_name=['XN', 'XS'], nb_chunks=1):
    """Exports KSSL MIRS spectra into a series of .csv files

    Parameters
    ----------
    in_folder: string, optional
        Specify the path of the folder containing the KSSL MIRS spectra

    out_folder: string, optional
        Specify the path of the folder that will contain exported files

    nb_decimals: int, optional
        Specify floating point precision (to save memory)

    max_wavenumber: int, optional
        Specify the max wavenumber to be considered in spectra

    valid_name: list of str, optional
        Specify valid spectra file names

    nb_chunks: int, optional
        Specify tne number of chunks/files to be created

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

    columns = None
    valid_files = [f for f in in_folder.rglob('*.0')
                   if re.search(r'X.', f.name)[0] in valid_name]

    for (l_bound, u_bound) in list(chunk(len(valid_files), nb_chunks)):
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
    """Creates MIRS spectra dimension table of new KSSL star-like schema

    Parameters
    ----------
    in_folder: string, optional
        Specify the path of the folder containing the KSSL MIRS spectra

    out_folder: string, optional
        Specify the path of the folder that will contain exported files

    with_replicates: boolean, optional
        Specify whether to include spectra replicates (averaged otherwise)

    Returns
    -------
    Pandas DataFrame
        Spectra dimension table
    """
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
    """Loads Spectra dimension table"""
    return pd.read_csv(in_folder / 'spectra_dim_tbl.csv')


def load_taxonomy(in_folder=DATA_KSSL):
    """Loads taxonomy dimension table

    Notes
    ----
    'mollisols' order is sometimes mispelled so fixing it
    """
    return pd.read_csv(in_folder / 'taxonomy_dim_tbl.csv') \
        .replace({'mollisol': 'mollisols'})


def get_tax_orders_lookup_tbl(order_to_int=True):
    """Returns a lookup table of taxonomic order names and respective ids"""
    df = load_taxonomy()
    orders = df['taxonomic_order'].unique()
    idx = range(len(orders))
    key_values = zip(orders, idx)
    if not order_to_int:
        key_values = zip(idx, orders)
    return dict(key_values)


def load_fact_tbl(in_folder=DATA_KSSL):
    return pd.read_csv(in_folder / 'sample_analysis_fact_tbl.csv')


def load_analytes(in_folder=DATA_KSSL):
    return pd.read_csv(in_folder / 'analyte_dim_tbl.csv')


def get_analytes(like='otas'):
    """Returns filtered version of analyte dim table containing specified substring"""
    df = load_analytes()
    return df[df['analyte_name'].str.contains(like)]


def count_spectra_by_analytes(like):
    """Returns number of spectra available by analytes containing specifed substring (like)"""
    df = load_fact_tbl() \
        .merge(get_analytes(like=like), on='analyte_id') \
        .loc[:, ['lay_id', 'analyte_name', 'smp_id']]

    df_spectra = load_spectra()
    df = pd.merge(df, df_spectra.reset_index()[['smp_id']], on='smp_id')

    return df \
        .groupby('analyte_name') \
        .count()[['lay_id']] \
        .rename(columns={'lay_id': 'dataset_size'}) \
        .sort_values(by='dataset_size', ascending=False)


def load_target(analytes=[725]):
    """Loads target `calc_value` + auxiliary attributes `lay_depth_to_top`
       and `order_id` for specified analytes"""
    df = load_fact_tbl()
    df = df[df['analyte_id'].isin(analytes)]
    df_tax = load_taxonomy()[['lims_pedon_id', 'taxonomic_order']]
    df = df.merge(df_tax, on='lims_pedon_id', how='left')
    df['order_id'] = df['taxonomic_order'].map(get_tax_orders_lookup_tbl())
    return df[['smp_id', 'lay_depth_to_top', 'order_id', 'calc_value']]


def load_data(in_folder=DATA_KSSL, analytes=[725], shuffle=True):
    """Loads data (spectra + target + auxiliary attributes for specified analytes"""
    df_target = load_target(analytes)
    df_spectra = load_spectra()
    df = df_target.merge(df_spectra, on='smp_id')
    if shuffle:
        df = df.sample(frac=1)
    X_names = df_spectra.iloc[:, 1:].columns.values.astype('int32')
    y_names = df.iloc[:, 1:4].columns.values
    instances_id = df['smp_id'].values
    X = df.iloc[:, 4:].to_numpy('float32')
    y = df.iloc[:, 1:4].to_numpy()
    return (X, X_names, y, y_names, instances_id)
