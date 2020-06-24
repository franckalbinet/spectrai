from pathlib import Path
import toml


#
# Config
#
def load_config(path=None):
    """Loads as dictionary from configuration file."""
    default_path = Path('~/.spectrai_config/config.toml').expanduser()
    if not path and default_path.is_file():
        path = default_path
    assert path, 'Either path argument or ~/.spectrai_config/config.toml is required.'

    config = toml.load(path)
    assert config, "Unable to parse config file"

    return config


def get_astorga_config():
    config = load_config()['DATA_ASTORGA_ARG']
    config = path_expand(config)
    return (config['SPECTRA'], config['MEASUREMENTS'])


def get_schmitter_config():
    config = load_config()['DATA_SCHMITTER_VNM']
    config = path_expand(config)
    return (config['SPECTRA'], config['SPECTRA_REP'], config['MEASUREMENTS'])


def get_kssl_config():
    config = load_config()['DATA_KSSL']
    config = path_expand(config, exclude = ['DB_NAME'])
    return (config['HOME'], config['NORM'], config['SPECTRA'], config['DB_NAME'])


def path_expand(config, exclude=[]):
    for k, v in config.items():
        if k not in exclude:
            config[k] = Path(v).expanduser()
    return config
