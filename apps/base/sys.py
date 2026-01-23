import os

from apps.base.env_reader import read_env_local


WINDOWS = "windows"
LINUX = "linux"
MAC = "mac"

DEVELOPMENT = "development"
PRODUCTION = "production"
STAGING = "staging"


def get_os():
    # Check if the OS is Windows
    if os.name == "nt":
        return WINDOWS
    # Check if the OS is Linux
    elif os.name == "posix":
        return LINUX
    # Check if the OS is Mac
    elif os.name == MAC:
        return MAC
    # Check if the OS is unknown
    else:
        return None


def is_windows():
    return get_os() == WINDOWS


def is_linux():
    return get_os() == LINUX


def is_mac():
    return get_os() == MAC


def get_environment():
    const = "DEPLOYMENT_MODE"
    # Check if the environment is development
    if read_env_local(const) == DEVELOPMENT:
        return DEVELOPMENT
    # Check if the environment is production
    elif read_env_local(const) == PRODUCTION:
        return PRODUCTION
    # Check if the environment is staging
    elif read_env_local(const) == STAGING:
        return STAGING
    else:
        return None


def is_development_environment():
    return get_environment() == DEVELOPMENT


def is_production_environment():
    return get_environment() == PRODUCTION


def is_staging_environment():
    return get_environment() == STAGING


def is_github_workflow_environment():
    return os.environ.get("GITHUB_WORKFLOW") is not None


__all__ = [
    "get_os",
    "is_windows",
    "is_linux",
    "is_mac",
    "get_environment",
    "is_development_environment",
    "is_production_environment",
    "is_staging_environment",
    "is_github_workflow_environment",
]