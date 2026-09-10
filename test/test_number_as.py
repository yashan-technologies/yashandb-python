from decimal import Decimal
import math
import unittest
import uuid

import yaspy
import test_base


class TestNumberAsCase(test_base.TestBaseCase):
    def _unique_table(self, suffix):
        # Avoid cross-test / parallel collisions on a shared table name.
        token = uuid.uuid4().hex[:8]
        return f"t_num_as_{suffix}_{token}"

    def _drop_table(self, cursor, table_name):
        cursor.execute(f"drop table if exists {table_name}")

    def test_default_decimal(self):
        table_name = self._unique_table("dec")
        self.assertEqual(self.connection.number_as, "decimal")
        self._drop_table(self.cursor, table_name)
        try:
            self.cursor.execute(
                f"create table {table_name}("
                f"col_dec number(4,2), col_int number(2,0), col_null number)"
            )
            self.cursor.execute(
                f"insert into {table_name}(col_dec, col_int, col_null) "
                f"values(:1, :2, :3)",
                [Decimal("12.34"), 10, None],
            )
            self.connection.commit()
            self.cursor.execute(
                f"select col_dec, col_int, col_dec * col_int, col_null "
                f"from {table_name}"
            )
            col_dec, col_int, db_calc, col_null = self.cursor.fetchone()
            self.assertIsInstance(col_dec, Decimal)
            self.assertEqual(col_dec, Decimal("12.34"))
            self.assertIsInstance(col_int, Decimal)
            self.assertEqual(col_int, Decimal("10"))
            self.assertIsInstance(db_calc, Decimal)
            self.assertIsNone(col_null)
        finally:
            self._drop_table(self.cursor, table_name)
            self.connection.commit()

    def test_number_as_float(self):
        table_name = self._unique_table("flt")
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        self.assertEqual(conn.number_as, "float")
        cur = conn.cursor()
        try:
            self._drop_table(cur, table_name)
            cur.execute(
                f"create table {table_name}(col_dec number(4,2), col_int number(2,0))"
            )
            cur.execute(
                f"insert into {table_name} values(:1, :2)",
                [Decimal("12.34"), 10],
            )
            conn.commit()
            cur.execute(
                f"select col_dec, col_int, col_dec * col_int from {table_name}"
            )
            col_dec, col_int, db_calc = cur.fetchone()
            self.assertIsInstance(col_dec, float)
            self.assertIsInstance(col_int, float)
            self.assertIsInstance(db_calc, float)
            py_calc = col_dec * col_int
            self.assertIsInstance(py_calc * 1.23, float)
        finally:
            self._drop_table(cur, table_name)
            conn.commit()
            cur.close()
            conn.close()

    def test_number_as_str(self):
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="str",
        )
        self.assertEqual(conn.number_as, "str")
        cur = conn.cursor()
        cur.execute("select cast(12.34 as number(4,2)) from dual")
        val, = cur.fetchone()
        self.assertIsInstance(val, str)
        self.assertEqual(Decimal(val), Decimal("12.34"))
        cur.close()
        conn.close()

    def test_number_as_int_success(self):
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="int",
        )
        self.assertEqual(conn.number_as, "int")
        cur = conn.cursor()
        cur.execute("select cast(10 as number(2,0)) from dual")
        val, = cur.fetchone()
        self.assertIsInstance(val, int)
        self.assertEqual(val, 10)
        # trailing zeros should still be accepted as integer
        cur.execute("select cast(12.00 as number(4,2)) from dual")
        val, = cur.fetchone()
        self.assertEqual(val, 12)
        cur.close()
        conn.close()

    def test_number_as_int_reject_fraction(self):
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="int",
        )
        cur = conn.cursor()
        cur.execute("select cast(12.34 as number(4,2)) from dual")
        with self.assertRaises(yaspy.DataError):
            cur.fetchone()
        cur.close()
        conn.close()

    def test_number_as_aliases_case_insensitive(self):
        """Each mode: several canonical/alias spellings and mixed case."""
        cases = {
            "decimal": (
                "decimal",
                "Decimal",
                "DECIMAL",
                "DeCiMaL",
                "dEcImAl",
            ),
            "float": (
                "float",
                "Float",
                "FLOAT",
                "FlOaT",
                "float64",
                "FLOAT64",
                "Float64",
                "fLoAt64",
            ),
            "int": (
                "int",
                "Int",
                "INT",
                "iNt",
                "int64",
                "INT64",
                "Int64",
                "iNt64",
            ),
            "str": (
                "str",
                "Str",
                "STR",
                "sTr",
                "string",
                "String",
                "STRING",
                "StRiNg",
            ),
        }
        for expected, aliases in cases.items():
            for alias in aliases:
                with self.subTest(alias=alias, expected=expected):
                    conn = yaspy.connect(
                        dsn=self.getDsn(),
                        user=self.user,
                        password=self.passwd,
                        number_as=alias,
                    )
                    try:
                        self.assertEqual(conn.number_as, expected)
                    finally:
                        conn.close()

    def test_number_as_mixed_case_fetch_behavior(self):
        """Mixed-case number_as must not only parse, but also affect fetch types."""
        # DECIMAL / DeCiMaL → Decimal
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="DeCiMaL",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(12.34 as number(4,2)) from dual")
            val, = cur.fetchone()
            self.assertIsInstance(val, Decimal)
            self.assertEqual(val, Decimal("12.34"))
        finally:
            cur.close()
            conn.close()

        # FlOaT → float
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="FlOaT",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(12.34 as number(4,2)) from dual")
            val, = cur.fetchone()
            self.assertIsInstance(val, float)
            self.assertAlmostEqual(val, 12.34, places=5)
        finally:
            cur.close()
            conn.close()

        # iNt → int (integer value)
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="iNt",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(12.00 as number(4,2)) from dual")
            val, = cur.fetchone()
            self.assertIsInstance(val, int)
            self.assertEqual(val, 12)
        finally:
            cur.close()
            conn.close()

        # StRiNg → str
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="StRiNg",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(12.34 as number(4,2)) from dual")
            val, = cur.fetchone()
            self.assertIsInstance(val, str)
            self.assertEqual(Decimal(val), Decimal("12.34"))
        finally:
            cur.close()
            conn.close()

        # INT64 alias with mixed case still rejects non-integer
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="InT64",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(12.34567 as number) from dual")
            with self.assertRaises(yaspy.DataError) as ctx:
                cur.fetchone()
            self.assertIn("number_as='int'", str(ctx.exception))
        finally:
            cur.close()
            conn.close()

    def test_number_as_invalid(self):
        with self.assertRaises(yaspy.ProgrammingError):
            yaspy.connect(
                dsn=self.getDsn(),
                user=self.user,
                password=self.passwd,
                number_as="double",
            )
        with self.assertRaises(TypeError):
            yaspy.connect(
                dsn=self.getDsn(),
                user=self.user,
                password=self.passwd,
                number_as=1,
            )

    def test_number_as_keyword_only(self):
        # number_as must be passed by keyword, not as 4th positional argument.
        with self.assertRaises(TypeError):
            yaspy.connect(self.getDsn(), self.user, self.passwd, "float")

    def test_session_pool_number_as(self):
        pool = yaspy.SessionPool(
            user=self.user,
            password=self.passwd,
            dsn=self.getDsn(),
            min=1,
            max=2,
            number_as="FLOAT",
        )
        self.assertEqual(pool.number_as, "float")
        conn = pool.acquire()
        self.assertEqual(conn.number_as, "float")
        cur = conn.cursor()
        cur.execute("select cast(1.5 as number(2,1)) from dual")
        val, = cur.fetchone()
        self.assertIsInstance(val, float)
        cur.close()
        pool.release(conn)
        pool.close()

    def test_large_integer_modes(self):
        """20-digit integer: int/str/decimal keep exact value; float may lose precision."""
        big_literal = "12345678901234567890"
        big_int = int(big_literal)

        # exact modes
        for mode, checker in (
            ("int", lambda v: self.assertEqual(v, big_int)),
            ("str", lambda v: self.assertEqual(Decimal(v), Decimal(big_literal))),
            ("decimal", lambda v: self.assertEqual(v, Decimal(big_literal))),
        ):
            conn = yaspy.connect(
                dsn=self.getDsn(),
                user=self.user,
                password=self.passwd,
                number_as=mode,
            )
            cur = conn.cursor()
            try:
                cur.execute(f"select cast({big_literal} as number) from dual")
                val, = cur.fetchone()
                self.assertIsInstance(val, {"int": int, "str": str, "decimal": Decimal}[mode])
                checker(val)
            finally:
                cur.close()
                conn.close()

        # float: still finite, but not bit-exact for 20-digit integers
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        cur = conn.cursor()
        try:
            cur.execute(f"select cast({big_literal} as number) from dual")
            val, = cur.fetchone()
            self.assertIsInstance(val, float)
            self.assertTrue(math.isfinite(val))
            # float64 cannot represent this 20-digit integer exactly
            self.assertNotEqual(int(val), big_int)
            # magnitude should still be in the same ballpark
            self.assertAlmostEqual(val / 1e19, big_int / 1e19, places=6)
        finally:
            cur.close()
            conn.close()

    def test_many_decimals_modes(self):
        """High-scale decimal: decimal/str preserve DB text; float approximates; int rejects."""
        # Use a value with a clear non-zero fractional part after DB cast.
        sql = "select cast(1.23456789012345678901234567890123456789 as number) from dual"

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="decimal",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            dec_val, = cur.fetchone()
            self.assertIsInstance(dec_val, Decimal)
            self.assertNotEqual(dec_val, dec_val.to_integral_value())
            self.assertGreater(len(str(dec_val).replace(".", "").lstrip("-")), 15)
        finally:
            cur.close()
            conn.close()

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="str",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            str_val, = cur.fetchone()
            self.assertIsInstance(str_val, str)
            self.assertEqual(Decimal(str_val), dec_val)
        finally:
            cur.close()
            conn.close()

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            flt_val, = cur.fetchone()
            self.assertIsInstance(flt_val, float)
            self.assertTrue(math.isfinite(flt_val))
            # float cannot keep full decimal precision
            self.assertNotEqual(Decimal(str(flt_val)), dec_val)
        finally:
            cur.close()
            conn.close()

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="int",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            with self.assertRaises(yaspy.DataError) as ctx:
                cur.fetchone()
            msg = str(ctx.exception)
            self.assertIn("cannot convert NUMBER value", msg)
            self.assertIn("number_as='int'", msg)
        finally:
            cur.close()
            conn.close()

    def test_scientific_large_magnitude(self):
        """1e125 is within Yashan NUMBER and float64; int/str/decimal/float should all succeed."""
        sql = "select cast(1e125 as number) from dual"

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="int",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            val, = cur.fetchone()
            self.assertIsInstance(val, int)
            self.assertEqual(val, 10 ** 125)
        finally:
            cur.close()
            conn.close()

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            val, = cur.fetchone()
            self.assertIsInstance(val, float)
            self.assertTrue(math.isfinite(val))
            self.assertEqual(val, 1e125)
        finally:
            cur.close()
            conn.close()

        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="str",
        )
        cur = conn.cursor()
        try:
            cur.execute(sql)
            val, = cur.fetchone()
            self.assertIsInstance(val, str)
            self.assertEqual(Decimal(val), Decimal("1e125"))
        finally:
            cur.close()
            conn.close()

    def test_bind_input_unaffected_by_number_as(self):
        """number_as only affects fetch; bind still accepts Decimal/int/float."""
        table_name = self._unique_table("bind")
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        cur = conn.cursor()
        try:
            self._drop_table(cur, table_name)
            cur.execute(f"create table {table_name}(c1 number, c2 number, c3 number)")
            cur.execute(
                f"insert into {table_name} values(:1, :2, :3)",
                [Decimal("12.34"), 10, 3.5],
            )
            conn.commit()
            cur.execute(f"select c1, c2, c3 from {table_name}")
            c1, c2, c3 = cur.fetchone()
            self.assertIsInstance(c1, float)
            self.assertIsInstance(c2, float)
            self.assertIsInstance(c3, float)
        finally:
            self._drop_table(cur, table_name)
            conn.commit()
            cur.close()
            conn.close()

    def test_number_as_none_means_default_decimal(self):
        """Explicit number_as=None should behave like omitted (decimal)."""
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as=None,
        )
        try:
            self.assertEqual(conn.number_as, "decimal")
            cur = conn.cursor()
            cur.execute("select cast(12.34 as number(4,2)) from dual")
            val, = cur.fetchone()
            self.assertIsInstance(val, Decimal)
            cur.close()
        finally:
            conn.close()

    def test_null_number_all_modes(self):
        """NULL NUMBER must become None under every number_as mode."""
        table_name = self._unique_table("null")
        self._drop_table(self.cursor, table_name)
        try:
            self.cursor.execute(f"create table {table_name}(c1 number)")
            self.cursor.execute(f"insert into {table_name} values(NULL)")
            self.connection.commit()

            for mode in ("decimal", "float", "int", "str"):
                with self.subTest(mode=mode):
                    conn = yaspy.connect(
                        dsn=self.getDsn(),
                        user=self.user,
                        password=self.passwd,
                        number_as=mode,
                    )
                    cur = conn.cursor()
                    try:
                        cur.execute(f"select c1 from {table_name}")
                        val, = cur.fetchone()
                        self.assertIsNone(val)
                    finally:
                        cur.close()
                        conn.close()
        finally:
            self._drop_table(self.cursor, table_name)
            self.connection.commit()

    def test_negative_numbers_all_modes(self):
        """Negative integers/fractions across modes."""
        # negative integer-like value
        for mode, expected_type, check in (
            ("decimal", Decimal, lambda v: self.assertEqual(v, Decimal("-12.00"))),
            ("float", float, lambda v: self.assertAlmostEqual(v, -12.0, places=5)),
            ("int", int, lambda v: self.assertEqual(v, -12)),
            ("str", str, lambda v: self.assertEqual(Decimal(v), Decimal("-12"))),
        ):
            with self.subTest(mode=mode, kind="neg_intish"):
                conn = yaspy.connect(
                    dsn=self.getDsn(),
                    user=self.user,
                    password=self.passwd,
                    number_as=mode,
                )
                cur = conn.cursor()
                try:
                    cur.execute("select cast(-12.00 as number(4,2)) from dual")
                    val, = cur.fetchone()
                    self.assertIsInstance(val, expected_type)
                    check(val)
                finally:
                    cur.close()
                    conn.close()

        # negative fraction rejected by int
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="int",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(-12.34 as number(4,2)) from dual")
            with self.assertRaises(yaspy.DataError) as ctx:
                cur.fetchone()
            self.assertIn("cannot convert NUMBER value", str(ctx.exception))
            self.assertIn("number_as='int'", str(ctx.exception))
        finally:
            cur.close()
            conn.close()

    def test_int_accepts_trailing_zeros_and_rejects_12_34567(self):
        """Explicit 12.00 success and 12.34567 DataError with message check."""
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="int",
        )
        cur = conn.cursor()
        try:
            cur.execute("select cast(12.00 as number(4,2)) from dual")
            val, = cur.fetchone()
            self.assertEqual(val, 12)

            cur.execute("select cast(12.34567 as number) from dual")
            with self.assertRaises(yaspy.DataError) as ctx:
                cur.fetchone()
            msg = str(ctx.exception)
            self.assertIn("cannot convert NUMBER value", msg)
            self.assertIn("12.34567", msg)
            self.assertIn("number_as='int'", msg)
        finally:
            cur.close()
            conn.close()

    def test_fetchmany_fetchall_honor_number_as(self):
        """fetchmany/fetchall must use the same conversion path as fetchone."""
        table_name = self._unique_table("many")
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        cur = conn.cursor()
        try:
            self._drop_table(cur, table_name)
            cur.execute(f"create table {table_name}(id number, val number(4,2))")
            cur.execute(f"insert into {table_name} values(1, 1.10)")
            cur.execute(f"insert into {table_name} values(2, 2.20)")
            conn.commit()
            cur.execute(f"select val from {table_name} order by id")
            rows = cur.fetchall()
            self.assertEqual(len(rows), 2)
            self.assertIsInstance(rows[0][0], float)
            self.assertIsInstance(rows[1][0], float)

            cur.execute(f"select val from {table_name} order by id")
            rows = cur.fetchmany(size=1)
            self.assertEqual(len(rows), 1)
            self.assertIsInstance(rows[0][0], float)
        finally:
            self._drop_table(cur, table_name)
            conn.commit()
            cur.close()
            conn.close()

    def test_session_pool_default_and_invalid_and_keyword_only(self):
        """Pool: default decimal, invalid value, keyword-only number_as."""
        # default (omit number_as)
        pool = yaspy.SessionPool(
            user=self.user,
            password=self.passwd,
            dsn=self.getDsn(),
            min=1,
            max=2,
        )
        try:
            self.assertEqual(pool.number_as, "decimal")
            conn = pool.acquire()
            try:
                self.assertEqual(conn.number_as, "decimal")
                cur = conn.cursor()
                cur.execute("select cast(1 as number) from dual")
                val, = cur.fetchone()
                self.assertIsInstance(val, Decimal)
                cur.close()
            finally:
                pool.release(conn)
        finally:
            pool.close()

        # invalid
        with self.assertRaises(yaspy.ProgrammingError):
            yaspy.SessionPool(
                user=self.user,
                password=self.passwd,
                dsn=self.getDsn(),
                number_as="double",
            )

        # keyword-only: 8th positional must not be accepted as number_as
        with self.assertRaises(TypeError):
            yaspy.SessionPool(
                self.user,
                self.passwd,
                self.getDsn(),
                1,
                2,
                1,
                1,
                "float",
            )

    def test_session_pool_modes_inherit(self):
        """acquire() inherits int/str/decimal as well as float."""
        for mode, sql in (
            ("int", "select cast(10 as number(2,0)) from dual"),
            ("str", "select cast(12.34 as number(4,2)) from dual"),
            ("decimal", "select cast(12.34 as number(4,2)) from dual"),
        ):
            with self.subTest(mode=mode):
                pool = yaspy.SessionPool(
                    user=self.user,
                    password=self.passwd,
                    dsn=self.getDsn(),
                    min=1,
                    max=2,
                    number_as=mode,
                )
                try:
                    self.assertEqual(pool.number_as, mode)
                    conn = pool.acquire()
                    try:
                        self.assertEqual(conn.number_as, mode)
                        cur = conn.cursor()
                        cur.execute(sql)
                        val, = cur.fetchone()
                        if mode == "int":
                            self.assertIsInstance(val, int)
                            self.assertEqual(val, 10)
                        elif mode == "str":
                            self.assertIsInstance(val, str)
                            self.assertEqual(Decimal(val), Decimal("12.34"))
                        else:
                            self.assertIsInstance(val, Decimal)
                            self.assertEqual(val, Decimal("12.34"))
                        cur.close()
                    finally:
                        pool.release(conn)
                finally:
                    pool.close()

    def test_number_as_attribute_readonly(self):
        """number_as should be read-only on connection and pool."""
        conn = yaspy.connect(
            dsn=self.getDsn(),
            user=self.user,
            password=self.passwd,
            number_as="float",
        )
        try:
            with self.assertRaises(AttributeError):
                conn.number_as = "int"
            self.assertEqual(conn.number_as, "float")
        finally:
            conn.close()

        pool = yaspy.SessionPool(
            user=self.user,
            password=self.passwd,
            dsn=self.getDsn(),
            min=1,
            max=2,
            number_as="str",
        )
        try:
            with self.assertRaises(AttributeError):
                pool.number_as = "float"
            self.assertEqual(pool.number_as, "str")
        finally:
            pool.close()


if __name__ == "__main__":
    test_base.run_test_cases()
