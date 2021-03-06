from spectrai.datasets.base import select_rows, chunk
from pandas.testing import assert_frame_equal
import pandas as pd


def test_select_rows():
    where = {'a': lambda d: d == 1, 'b': lambda d: d == 3}
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    assert_frame_equal(select_rows(df, where),
                       pd.DataFrame({'a': [1], 'b': [3]}))


def test_chunk():
    assert list(chunk(10, 3)) == [(0, 3), (3, 6), (6, 10)]
