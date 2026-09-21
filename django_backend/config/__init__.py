"""Password Strength Analyzer - Django project package.

On Windows, PyMySQL replaces the mysqlclient driver (which needs a C compiler).
Django's MySQL backend transparently uses it after install_as_MySQLdb().
"""

import pymysql

pymysql.install_as_MySQLdb()

__version__ = '1.0.0'