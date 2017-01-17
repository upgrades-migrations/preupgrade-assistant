# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'OS'
        db.create_table(u'report_os', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('major', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('minor', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'report', ['OS'])

        # Adding model 'Host'
        db.create_table(u'report_host', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ssh_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ssh_password', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('sudo_password', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('su_login', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('local', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('os', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.OS'], null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['Host'])

        # Adding model 'TestGroup'
        db.create_table(u'report_testgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('xccdf_id', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.TestGroup'], null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['TestGroup'])

        # Adding model 'TestGroupResult'
        db.create_table(u'report_testgroupresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.TestGroup'])),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.Result'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='direct_children_set', null=True, to=orm['report.TestGroupResult'])),
            ('root', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='all_children_set', null=True, to=orm['report.TestGroupResult'])),
            ('test_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0, null=True, blank=True)),
            ('failed_test_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0, null=True, blank=True)),
            ('ni_test_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0, null=True, blank=True)),
            ('na_test_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0, null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['TestGroupResult'])

        # Adding model 'Run'
        db.create_table(u'report_run', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt_submitted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('dt_finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['Run'])

        # Adding model 'HostRun'
        db.create_table(u'report_hostrun', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt_finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.Host'])),
            ('run', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.Run'])),
            ('state', self.gf('django.db.models.fields.CharField')(default='r', max_length=1, db_index=True)),
            ('risk', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=16, null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['HostRun'])

        # Adding model 'Result'
        db.create_table(u'report_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt_submitted', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt_finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('hostrun', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['report.HostRun'], unique=True)),
            ('identity', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('test_count', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('failed_test_count', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('ni_test_count', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('na_test_count', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['Result'])

        # Adding model 'Address'
        db.create_table(u'report_address', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.GenericIPAddressField')(max_length=39)),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.Result'])),
        ))
        db.send_create_signal(u'report', ['Address'])

        # Adding model 'Test'
        db.create_table(u'report_test', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('id_ref', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('component', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('fix', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('fix_type', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('fixtext', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.TestGroup'], null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['Test'])

        # Adding model 'TestResult'
        db.create_table(u'report_testresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=3, db_index=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('test', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.Test'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='testresult_set', to=orm['report.TestGroupResult'])),
            ('root_group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='all_tests', to=orm['report.TestGroupResult'])),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.Result'])),
        ))
        db.send_create_signal(u'report', ['TestResult'])

        # Adding model 'TestLog'
        db.create_table(u'report_testlog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.TestResult'])),
        ))
        db.send_create_signal(u'report', ['TestLog'])

        # Adding model 'Risk'
        db.create_table(u'report_risk', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['report.TestResult'])),
        ))
        db.send_create_signal(u'report', ['Risk'])


    def backwards(self, orm):
        # Deleting model 'OS'
        db.delete_table(u'report_os')

        # Deleting model 'Host'
        db.delete_table(u'report_host')

        # Deleting model 'TestGroup'
        db.delete_table(u'report_testgroup')

        # Deleting model 'TestGroupResult'
        db.delete_table(u'report_testgroupresult')

        # Deleting model 'Run'
        db.delete_table(u'report_run')

        # Deleting model 'HostRun'
        db.delete_table(u'report_hostrun')

        # Deleting model 'Result'
        db.delete_table(u'report_result')

        # Deleting model 'Address'
        db.delete_table(u'report_address')

        # Deleting model 'Test'
        db.delete_table(u'report_test')

        # Deleting model 'TestResult'
        db.delete_table(u'report_testresult')

        # Deleting model 'TestLog'
        db.delete_table(u'report_testlog')

        # Deleting model 'Risk'
        db.delete_table(u'report_risk')


    models = {
        u'report.address': {
            'Meta': {'object_name': 'Address'},
            'address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.Result']"})
        },
        u'report.host': {
            'Meta': {'object_name': 'Host'},
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'os': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.OS']", 'null': 'True', 'blank': 'True'}),
            'ssh_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'su_login': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'report.hostrun': {
            'Meta': {'ordering': "('-run__dt_submitted',)", 'object_name': 'HostRun'},
            'dt_finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'risk': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'run': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.Run']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'r'", 'max_length': '1', 'db_index': 'True'})
        },
        u'report.os': {
            'Meta': {'ordering': "('major', 'minor')", 'object_name': 'OS'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'major': ('django.db.models.fields.SmallIntegerField', [], {}),
            'minor': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'report.result': {
            'Meta': {'object_name': 'Result'},
            'dt_finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'failed_test_count': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'hostrun': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['report.HostRun']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'na_test_count': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ni_test_count': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'test_count': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'report.risk': {
            'Meta': {'object_name': 'Risk'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.TestResult']"})
        },
        u'report.run': {
            'Meta': {'ordering': "('-dt_submitted',)", 'object_name': 'Run'},
            'dt_finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_submitted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'report.test': {
            'Meta': {'object_name': 'Test'},
            'component': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'fix': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'fix_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'fixtext': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.TestGroup']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_ref': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'report.testgroup': {
            'Meta': {'ordering': "('title',)", 'object_name': 'TestGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.TestGroup']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'xccdf_id': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'report.testgroupresult': {
            'Meta': {'ordering': "('group',)", 'object_name': 'TestGroupResult'},
            'failed_test_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.TestGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'na_test_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'ni_test_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'direct_children_set'", 'null': 'True', 'to': u"orm['report.TestGroupResult']"}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.Result']"}),
            'root': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'all_children_set'", 'null': 'True', 'to': u"orm['report.TestGroupResult']"}),
            'test_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'})
        },
        u'report.testlog': {
            'Meta': {'object_name': 'TestLog'},
            'date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.TestResult']"})
        },
        u'report.testresult': {
            'Meta': {'ordering': "('state',)", 'object_name': 'TestResult'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'testresult_set'", 'to': u"orm['report.TestGroupResult']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.Result']"}),
            'root_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_tests'", 'to': u"orm['report.TestGroupResult']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '3', 'db_index': 'True'}),
            'test': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['report.Test']"})
        }
    }

    complete_apps = ['report']