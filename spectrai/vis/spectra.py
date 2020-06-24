import numpy as np
import matplotlib.pyplot as plt


def plot_spectra(X, X_names, figsize=(18, 5), sample=20):
    with plt.style.context(('ggplot')):
        fig, ax = plt.subplots(figsize=figsize)
        idx = np.random.randint(X.shape[0], size=sample)
        ax.set_xlim(np.max(X_names), np.min(X_names))
        plt.xlabel('Wavenumber')
        _ = ax.plot(X_names, X[idx, :].T)
