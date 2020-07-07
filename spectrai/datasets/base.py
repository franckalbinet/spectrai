def select_rows(df, where):
    """Performs a series of rows selection in a DataFrame

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


def chunk(len_array, nb_chunks=3):
    """Chunks an array in a list of several equal (when odd) length chunks

    Parameters
    ----------
    len_array: int
        Length of the array to be chunked

    nb_chunks: int
        Number of chunks

    Returns
    -------
    Iterator
        e.g list(chunk(10, 3)) would return [(0, 3), (3, 6), (6, 10)]
    """
    assert nb_chunks <= len_array, "nb_chunks should be lower or equal than len_array"
    step = len_array // nb_chunks
    bounds = [x*step for x in range(nb_chunks)] + [len_array]
    return zip(bounds, bounds[1:])
