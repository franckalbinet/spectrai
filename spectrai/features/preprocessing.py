from sklearn.base import BaseEstimator, TransformerMixin
from scipy.signal import savgol_filter
import numpy as np


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


class SNV(BaseEstimator, TransformerMixin):
    """Creates scikit-learn SNV custom transformer

    Parameters
    ----------
    None

    Returns
    -------
    scikit-learn custom transformer
    """
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        mean, std = np.mean(X, axis=1).reshape(-1, 1), np.std(X, axis=1).reshape(-1, 1)
        return (X - mean)/std


class DropSpectralRegions(BaseEstimator, TransformerMixin):
    """Creates scikit-learn custom transformer dropping specific spectral region(s)

    Parameters
    ----------
    wavenumbers: list
        List of wavenumbers where absorbance measured

    regions: list
        List of region(s) to drop

    Returns
    -------
    scikit-learn custom transformer
    """
    def __init__(self, wavenumbers, regions=[2389,  2269]):
        self.wavenumbers = wavenumbers
        self.regions = regions

    def _sanitize(self, regions):
        nb_regions = len(np.array(regions).shape)
        return np.array([regions]) if nb_regions == 1 else np.array(regions)

    def _exists(self, wavenumbers, regions):
        for wn in regions.flatten():
            assert wn in wavenumbers, 'Wavenumber "{}" does not exist'.format(wn)

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        regions = self._sanitize(self.regions)
        X_transformed = np.copy(X)
        self._exists(self.wavenumbers, regions)
        for region in regions:
            high, low = region
            mask = (self.wavenumbers <= high) & (self.wavenumbers >= low)
            X_transformed[:, mask] = 0

        return X_transformed
