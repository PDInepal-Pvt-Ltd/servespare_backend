# __init__.py
from decouple import config

# Check DEV_MODE to conditionally configure pymysql
DEV_MODE = config('DEV_MODE', default=False, cast=bool)

if not DEV_MODE:
    # Only configure pymysql for production (MySQL database)
    import pymysql

    # Fake a high-enough version to satisfy Django's mysqlclient check (>=2.2.1)
    pymysql.version_info = (2, 2, 1, 'final', 0)

    # Make PyMySQL act as MySQLdb
    pymysql.install_as_MySQLdb()
