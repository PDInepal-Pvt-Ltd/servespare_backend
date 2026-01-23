import os
from pathlib import Path

from decouple import (
    Config,
    RepositoryEnv,
)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_PATH = BASE_DIR / ".env"

# .env.local is a secret env that is to be gitignored
ENV_LOCAL_PATH = BASE_DIR / ".env.local"


def env_reader_with_path(path):
    """
    Takes a path, and returns decouple Config that reads
    variables from that path

    :param path: Path where the env file is stored
    :return: A decouple config object
    """
    if os.path.exists(ENV_LOCAL_PATH):
        return Config(RepositoryEnv(path))
    else:
        # Fallback to default env path if the provided path doesn't exist
        return Config(RepositoryEnv(ENV_PATH))


def read_env(*args, **kwargs):
    """
    Takes the environment variable name (and, optionally,
    options taken by decouple config object)  and returns
    the value of that variable in ENV_PATH

    :return: Value of the environment variable in ENV_PATH
    """
    return env_reader_with_path(ENV_PATH)(*args, **kwargs)


def read_env_local(*args, **kwargs):
    """
    Takes the environment variable name (and, optionally,
    options taken by decouple config object)  and returns
    the value of that variable in ENV_LOCAL_PATH

    :return: Value of the environment variable in ENV_LOCAL_PATH
    """
    return env_reader_with_path(ENV_LOCAL_PATH)(*args, **kwargs)