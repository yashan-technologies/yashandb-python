"""executemany 中 None 与 LOB(超长字符串) 数组绑定的回归测试。

覆盖三处修复：
  1. 首行 None 时重建 AnpVar 丢失已绑定 indicator（核心 bug）
  2. LOB 数组绑定 locator 按 arrayPos 固定槽位写（带 None 时不错位）
  3. char -> LOB 跨界重建时迁移已写数据到 locator
"""

import test_base
import yaspy
from decimal import Decimal

# 超过 CONVERT_TO_LOB_SIZE(65534)，触发 char -> clob 转换
LONG = 70000


class TestCase(test_base.TestBaseCase):
    def _roundtrip(self, table, cols_sql, data):
        """建表 -> executemany -> 按 id 读回，返回读取结果。"""
        self.cursor.execute(f"drop table if exists {table}")
        self.cursor.execute(f"create table {table}(id int, {cols_sql})")
        ph = ",".join(["?"] * len(data[0]))
        self.cursor.executemany(f"insert into {table} values({ph})", data)
        self.cursor.execute(f"select * from {table} order by id")
        rows = self.cursor.fetchall()
        self.cursor.execute(f"drop table {table}")
        return rows

    def test_executemany_none_first_str(self):
        # 首行 None + 字符串：旧实现重建 var 时丢失首行 NULL 标记导致错乱
        data = [(1, None), (2, 'b'), (3, 'c')]
        rows = self._roundtrip("t_em_none_first_str", "c1 varchar(50)", data)
        self.assertEqual(data, rows)

    def test_executemany_none_first_int(self):
        data = [(1, None), (2, 100), (3, 200)]
        rows = self._roundtrip("t_em_none_first_int", "c1 int", data)
        self.assertEqual(data, rows)

    def test_executemany_none_first_float(self):
        data = [(1, None), (2, 1.5), (3, 2.5)]
        rows = self._roundtrip("t_em_none_first_float", "c1 double", data)
        self.assertEqual(data, rows)

    def test_executemany_none_first_bytes(self):
        data = [(1, None), (2, b'ab'), (3, b'cd')]
        rows = self._roundtrip("t_em_none_first_bytes", "c1 blob", data)
        self.assertEqual(data, rows)

    def test_executemany_all_none(self):
        data = [(1, None), (2, None), (3, None)]
        rows = self._roundtrip("t_em_all_none", "c1 varchar(50)", data)
        self.assertEqual(data, rows)

    def test_executemany_multicol_mixed_none(self):
        # 每列 None 出现在不同位置：验证多 var 独立复用互不影响
        data = [
            (1, None, 'a', 'x'),
            (2, 'b', 'b', None),
            (3, 'c', None, 'z'),
        ]
        rows = self._roundtrip("t_em_multicol_mixed",
                               "c1 varchar(50), c2 varchar(50), c3 varchar(50)", data)
        self.assertEqual(data, rows)

    def test_executemany_none_first_decimal(self):
        data = [(1, None), (2, Decimal('1.23')), (3, Decimal('4.56'))]
        rows = self._roundtrip("t_em_none_first_decimal", "c1 number(10,2)", data)
        self.assertEqual(data, rows)

    # ---- LOB(超长字符串) 场景 ----

    def test_executemany_none_first_longstr(self):
        # 首行 None + 超长(触发 char->clob)：locator 固定槽位不因 None 错位
        data = [(1, None), (2, 'x' * LONG), (3, 'y' * LONG)]
        rows = self._roundtrip("t_em_none_first_long", "c1 clob", data)
        self.assertEqual(data, rows)

    def test_executemany_str_first_longstr(self):
        # 首行短字符串 + 后续超长：char->clob 跨界，首行数据需迁移到 locator
        data = [(1, 'a'), (2, 'x' * LONG), (3, 'y' * LONG)]
        rows = self._roundtrip("t_em_str_first_long", "c1 clob", data)
        self.assertEqual(data, rows)

    def test_executemany_longstr_then_short(self):
        # 首行超长(转 clob)后复用 var 写短字符串
        data = [(1, 'x' * LONG), (2, 'a'), (3, 'b')]
        rows = self._roundtrip("t_em_long_then_short", "c1 clob", data)
        self.assertEqual(data, rows)

    def test_executemany_consecutive_longstr(self):
        # 连续多行超长：验证不再因后续超长值重复重建丢失前面 LOB 数据
        data = [(1, 'x' * LONG), (2, 'y' * LONG), (3, 'z' * LONG)]
        rows = self._roundtrip("t_em_consecutive_long", "c1 clob", data)
        self.assertEqual(data, rows)