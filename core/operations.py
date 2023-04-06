# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

"""
This page is useful for custom migration tricks.
Sometimes, when you need to have a migration hack and you think it can be
useful again, put it there, we never know if we might need the hack again.
"""

from django.db import connection, migrations


class PsqlRunOnly(migrations.RunSQL):
    """
    This is an SQL runner that will launch the given command only if
    the used DBMS is PostgreSQL.
    It may be useful to run Postgres' specific SQL, or to take actions
    that would be non-senses with backends other than Postgre, such
    as disabling particular constraints that would prevent the migration
    to run successfully.

    See `club/migrations/0010_auto_20170912_2028.py` as an example.
    Some explanations can be found here too:
    https://stackoverflow.com/questions/28429933/django-migrations-using-runpython-to-commit-changes
    """

    def _run_sql(self, schema_editor, sqls):
        if connection.vendor == "postgresql":
            super(PsqlRunOnly, self)._run_sql(schema_editor, sqls)
