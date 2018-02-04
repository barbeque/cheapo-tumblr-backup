import yaml, os.path

# TODO: Generate config file on first run?

def get_from_config(config_key):
    config_path = 'config.yml'
    if not os.path.isfile(config_path):
        raise Exception("Cannot find config file. Please create a config file named {config_path} with the key {config_key} inside it.".format(config_path = config_path, config_key = config_key))
    with open(config_path, 'r') as c:
        s = c.read()
        y = yaml.safe_load(s)
        if y == None or (type(y) is not str and config_key not in y):
            raise Exception("Cannot find the config key {config_key} in the config file. Please add it to {config_path}.".format(config_path = config_path, config_key = config_key))
        if type(y) is str:
            raise Exception("{config_path} is not a valid YAML dictionary.".format(config_path = config_path))
        return y[config_key]
