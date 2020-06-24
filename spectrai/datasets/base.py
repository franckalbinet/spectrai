
def select_rows(df, where):
    """Perform a series of rows selection in a DataFrame

    Pandas provides several methods to select rows.
    Using lambdas allows to select rows in a uniform and
    more flexible way.

    Parameters
    ----------
    df:  DataFrame
        DataFrame whose rows should be selected

    where: dict
        Dictionary with DataFrame columns name as keys
        and predicates (as lambdas) as values.
        For instance: {'a': lambda d: d == 1, 'b': lambda d: d == 3}

    Returns
    -------
    Pandas DataFrame
        New DataFrame with selected rows
    """
    df = df.copy()
    for col, f in where.items():
        df = df[df[col].apply(f)]
    return df
