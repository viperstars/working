# -*- coding: utf-8 -*-

"""
    自定义的一个分页类，可以利用现有宏来进行分页
"""

import MySQLdb
from math import ceil
from functools import partial

config = dict(user='root', passwd='', host='127.0.0.1', port=3306, db='testdb', charset='utf8')

connection = partial(MySQLdb.connect, **config)


class Pagination(object):

    @staticmethod
    def get_total(table, condition, order,):
        """
        获取表的行数
        参数：表名
        返回值：行数
        """
        query = 'select count(*) from {0} {1} {2}'.format(table, condition, order)
        con = connection()
        cur = con.cursor()
        cur.execute(query)
        con.commit()
        result = cur.fetchall()
        cur.close()
        con.close()
        if result:
            return result[0][0]
        else:
            return 0

    @staticmethod
    def get_item(table, columns, condition, order, page, per_page):
        """
        获取对应页码中的数据
        参数：表名，页码，每页数据数
        返回值：从数据库中获取的对应数据
        """
        start = (page - 1) * per_page
        if columns:
            query = "select {0} from {1} {2} {3} limit {4}, {5}".format(columns, table, condition, order, start,
                                                                        per_page)
        else:
            query = "select * from {0} {1} {2} limit {3}, {4}".format(table, condition, order, start, per_page)
        print query
        con = connection()
        cur = con.cursor()
        cur.execute(query)
        con.commit()
        result = cur.fetchall()
        cur.close()
        con.close()
        if result:
            return result
        else:
            return ()

    def __init__(self, table, page, per_page, condition, order, columns=None):
        """
        初始化方法
        参数：表名，页码，每页数据数，条件，排序方式，列名
        """
        self.table = table
        self.page = page
        self.per_page = per_page
        self.condition = condition
        self.order = order
        if columns:
            self.columns = ', '.join(columns)
        else:
            self.columns = None
        self.total = Pagination.get_total(self.table, self.condition, self.order)
        self.item = Pagination.get_item(self.table, self.columns, self.condition, self.order, self.page, self.per_page)

    @property
    def pages(self):
        """
        计算这个对象分页后对应的页数
        """
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self):
        """
        前一页
        返回一个 Pagination对象
        """
        return Pagination(self.table, self.page - 1, self.per_page)

    @property
    def prev_num(self):
        """
        返回前一页页码
        """
        return self.page - 1

    @property
    def has_prev(self):
        """
        判断是否有前一页
        """
        return self.page > 1

    def next(self):
        """
        下一页
        返回一个 Pagination对象
        """
        return Pagination(self.table, self.page + 1, self.per_page)

    @property
    def has_next(self):
        """
        判断是否有下一页
        """
        return self.page < self.pages

    @property
    def next_num(self):
        """
        返回下一页页码
        """
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """
        页码生成器
        """
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and
                     num < self.page + right_current) or \
                     num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
