from sklearn.base import BaseEstimator, TransformerMixin
from scipy.signal import savgol_filter


class TakeDerivative(BaseEstimator, TransformerMixin):
    """Creates scikit-learn derivation custom transformer

    Parameters
    ----------
    window_length: int, optional
        Specify savgol filter smoothing window length

    polyorder: int, optional
        Specify order of the polynom used to interpolate derived signal

    deriv: int, optional
        Specify derivation degree

    Returns
    -------
    scikit-learn custom transformer
    """

    def __init__(self, window_length=11, polyorder=1, deriv=1):
        self.window_length = window_length
        self.polyorder = polyorder
        self.deriv = deriv

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return savgol_filter(X, self.window_length, self.polyorder, self.deriv)
