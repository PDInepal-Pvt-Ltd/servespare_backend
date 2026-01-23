# __init__.py
import pymysql

# Fake a high-enough version to satisfy Django's mysqlclient check (>=2.2.1)
pymysql.version_info = (2, 2, 1, 'final', 0)

# Make PyMySQL act as MySQLdb
pymysql.install_as_MySQLdb()
