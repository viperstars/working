#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import datetime
import json

TIME_FORMAT='%Y-%m-%d %H:%M:%S'
now = datetime.datetime.now()

def insert(hosts,res):
    res = json.dumps(res)
    conn=MySQLdb.connect(user='root', passwd='123456', host='192.168.1.116', port=3306, db='ansible')
    cur=conn.cursor()
    sql='insert into status(hosts,result,date) values(%s, %s, %s)'
    cur.execute(sql, (hosts, res, now.strftime(TIME_FORMAT)))
    conn.commit()
    conn.close()

class CallbackModule(object):
    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        insert(host,res)

    def runner_on_ok(self, host, res):
        insert(host,res)

    def runner_on_unreachable(self, host, res):
        insert(host,res)

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_stats(self, stats):
        hosts = stats.processed.keys()
        for i in hosts:
            info = stats.summarize(i)
            if info['failures'] > 0 or info['unreachable'] > 0:
                has_errors = True
                msg ="Hostinfo: %s, ok: %d, failures: %d, unreachable: %d, changed: %d, skipped: %d" % (i, info['ok'], info['failures'], info['unreachable'], info['changed'], info['skipped'])
                print msg
