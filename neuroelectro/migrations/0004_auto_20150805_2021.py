# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('neuroelectro', '0003_auto_20150805_1953'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ephysconceptmap',
            unique_together=set([('source', 'dt_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='neuronconceptmap',
            unique_together=set([('source', 'dt_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='neuronephysdatamap',
            unique_together=set([('source', 'dt_id')]),
        ),
    ]
