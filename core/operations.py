# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Sli <antoine@bartuccio.fr>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
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
