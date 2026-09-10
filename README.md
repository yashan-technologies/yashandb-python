# yaspy|崖山数据库python语言驱动程序

yaspy 是 YashanDB 官方 Python 语言数据库驱动，依赖崖山数据库C驱动。

### 特性

- ✅ Python 3.6+
- ✅ 连接池支持
- ✅ 预处理语句与批量操作
- ✅ 事务支持
- ✅ 多版本运行时检测与自动适配
- ✅ NUMBER 读出类型可配置（`number_as`：decimal/float/int/str）

### NUMBER 读出类型（number_as）

默认将 `NUMBER` 映射为 `decimal.Decimal`。可通过连接或连接池参数切换：

```python
conn = yaspy.connect(user="u", password="p", dsn="host:1688", number_as="float")
# number_as: "decimal"(默认) | "float" | "int" | "str"（大小写不敏感）
# 别名: float64, int64, string
# 仅支持关键字参数，例如 number_as="FLOAT"
print(conn.number_as)
```

---

### 兼容性说明

| 驱动版本 | 版本发布时间 | 新特性         | 最低兼容C驱动版本 | 完全支持C驱动版本 |
| -------- | ------------ | -------------- | ----------------- | ----------------- |
| 1.0.1    | 2026.3.18    | 支持线程池能力 | v23.4.1.100       | v23.4.4.100       |
