# AI生成

## Qwen3-Coder

好的，我们将根据上一步基于 GB/T 36344-2018 标准对 `sys_api` 表进行的数据质量维度分析，为每个相关的二级指标生成用于评估的 SQL 脚本。

这些脚本将计算每个指标的符合记录数（A）和总记录数（B），以便后续计算符合度（X = A/B）。我们将针对每个可能适用的二级指标编写脚本。

---

### **1. 规范性 (Conformity)**

#### **0101 - 数据标准 (Data Standard)**

* **示例：检查 `method` 字段是否符合标准 HTTP 方法集。**

    ```sql
    -- 0101 - 数据标准 - 检查 method 字段是否符合标准 HTTP 方法
    SELECT
        '0101' AS 指标编号,
        '数据标准' AS 指标名称,
        '检查 method 字段是否符合标准 HTTP 方法 (GET, POST, PUT, DELETE, PATCH)' AS 指标描述,
        COUNT(CASE WHEN method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH') THEN 1 END) AS A_满足标准的记录数,
        COUNT(*) AS B_总记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH') THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0'; -- 通常只评估未删除的数据

    ```

    *(你可以根据实际允许的HTTP方法列表修改 `IN (...)` 部分)*

#### **0102 - 数据模型 (Data Model)**

* **示例：检查 `app_id` 是否为非空（假设这是数据模型要求的）。**

    ```sql
    -- 0102 - 数据模型 - 检查 app_id 是否非空 (作为数据模型要求)
    SELECT
        '0102' AS 指标编号,
        '数据模型' AS 指标名称,
        '检查 app_id 字段是否满足数据模型要求 (非空)' AS 指标描述,
        COUNT(CASE WHEN app_id IS NOT NULL THEN 1 END) AS A_满足要求的记录数,
        COUNT(*) AS B_总记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN app_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0';

    ```

    *(你可以添加更多检查，例如 `path` 是否非空等，根据数据模型定义)*

* **示例：检查 `app_id` 字段是否都存在于 `sys_app` 表中，即外键定义。**

    ```sql
    -- 计算 app_id 字段符合外键约束的比率
    SELECT 
        COUNT(CASE WHEN sa.app_id IS NOT NULL THEN 1 END) AS A, -- app_id 存在于 sys_app 表中的记录数
        COUNT(*) AS B, -- sys_api 表中的总记录数
        ROUND(
            COUNT(CASE WHEN sa.app_id IS NOT NULL THEN 1 END) * 1.0 / 
            COUNT(*), 
            4
        ) AS data_model_ratio -- 数据模型比率
    FROM sys_api sa
    LEFT JOIN sys_app app ON sa.app_id = app.id -- 假设 sys_app 的主键是 id
    WHERE sa.is_delete = b'0'; -- 仅评估未删除的数据
    ```

    *(你可以添加更多外键约束检查，根据数据模型定义)*

    ```sql
    -- ============================================================================
    -- 计算 sys_api 表中 app_id 字段与 sys_app 表中 id 字段的主外键关联校验通过率
    -- ============================================================================

    SELECT 
    -- sys_api 表中 app_id 非空的总记录数
    COUNT(*) AS total_api_records,
    
    -- 在 sys_app 表中能找到对应 id 的 app_id 记录数（有效引用数）
    COUNT(sa.id) AS valid_referenced_app_records,
    
    -- 计算主外键关联校验通过率，保留两位小数
    -- 公式：(有效引用数 / 总记录数) * 100%
    ROUND(
        (COUNT(sa.id) / COUNT(api.app_id)) * 100, 
        2
    ) AS reference_validation_pass_rate

    FROM 
    -- 主表：sys_api，别名为 api
    ${src_table} api

    LEFT JOIN 
    -- 关联表：sys_app，别名为 sa
    sys_app sa ON api.app_id = sa.id;
    ```

    ```sql
    -- ============================================================================
    -- 输出异常记录：查找所有未在 sys_app 中找到对应 id 的 sys_api 记录（悬空引用）
    -- ============================================================================
    SELECT *
    FROM sys_api api
    LEFT JOIN sys_app sa ON api.app_id = sa.id
    WHERE sa.id IS NULL AND api.app_id IS NOT NULL;
    ```

#### **0103 - 元数据 (Metadata)**

* **示例：检查 `encrypt` 字段是否只包含 `0` 或 `1`（符合 `bit(1)` 的元数据定义）。**

    ```sql
    -- 0103 - 元数据 - 检查 encrypt 字段值是否符合 bit(1) 定义
    SELECT
        '0103' AS 指标编号,
        '元数据' AS 指标名称,
        '检查 encrypt 字段值是否符合元数据定义 (bit(1) -> 0 or 1)' AS 指标描述,
        COUNT(CASE WHEN encrypt IN (b'0', b'1') THEN 1 END) AS A_满足定义的记录数,
        COUNT(*) AS B_总记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN encrypt IN (b'0', b'1') THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0';

    ```

    *(可以为其他有严格值域定义的字段添加类似检查)*

* **示例：检查 `version` 字段是否符合 `vX.Y.Z` 的版本号格式。**

    ```sql
    -- 计算 version 字段符合元数据定义（版本号格式）的比率
    -- 使用正则表达式匹配 v1.0.0 这类格式
    SELECT 
        COUNT(CASE WHEN version REGEXP '^v[0-9]+\\.[0-9]+\\.[0-9]+$' THEN 1 END) AS A, -- 符合版本号格式的记录数
        COUNT(*) AS B, -- 总记录数
        ROUND(
            COUNT(CASE WHEN version REGEXP '^v[0-9]+\\.[0-9]+\\.[0-9]+$' THEN 1 END) * 1.0 / 
            COUNT(*), 
            4
        ) AS metadata_ratio -- 元数据比率
    FROM sys_api 
    WHERE is_delete = b'0' AND version IS NOT NULL; -- 仅评估未删除且version不为空的数据
    ```

#### **0104 - 业务规则 (Business Rule)**

* **示例：检查当 `type` 为 'inner_api' 时，`enabled` 是否为 `1`。**

    ```sql
    -- 0104 - 业务规则 - 检查内部API必须启用
    SELECT
        '0104' AS 指标编号,
        '业务规则' AS 指标名称,
        '检查当 type 为 ''inner_api'' 时，enabled 是否为 1' AS 指标描述,
        COUNT(*) AS B_总相关记录数, -- 只看 type='inner_api' 的记录
        COUNT(CASE WHEN enabled = b'1' THEN 1 END) AS A_满足规则的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN enabled = b'1' THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND type = 'inner_api'; -- 只评估相关记录

    ```

    *(需要根据实际的业务规则调整条件)*

* **示例：检查当 `register_type` 为 'manual' 时，`create_by` 字段是否为 'not null'。**

    ```sql
    -- 计算符合业务规则（手动注册的创建者应为not null）的比率
    SELECT 
        COUNT(CASE 
            WHEN register_type = 'manual' AND create_by IS NOT NULL THEN 1
            WHEN register_type != 'manual' THEN 1 -- 其他情况也视为符合规则
            ELSE 0 
        END) AS A, -- 符合业务规则的记录数
        COUNT(*) AS B, -- 总记录数
        ROUND(
            COUNT(CASE 
                WHEN register_type = 'manual' AND create_by IS NULL THEN 1
                WHEN register_type != 'manual' THEN 1
                ELSE 0
            END) * 1.0 /
            COUNT(*),
            4
        ) AS business_rule_ratio -- 业务规则比率
    FROM sys_api 
    WHERE is_delete = b'0'; -- 仅评估未删除的数据
    ```

#### **0105 - 权威参考数据 (Authoritative Reference Data)**

检查字段值是否在预定义的有效值列表中，属于验证数据是否引用了正确的参考值的范畴。

* **示例：检查 `response_data_type` 是否在预定义列表中。**

    ```sql
    -- 0105 - 权威参考数据 - 检查 response_data_type 是否在参考列表中
    SELECT
        '0105' AS 指标编号,
        '权威参考数据' AS 指标名称,
        '检查 response_data_type 是否在预定义的参考数据列表中 (JSON, XML, TEXT, BINARY)' AS 指标描述,
        COUNT(CASE WHEN response_data_type IN ('JSON', 'XML', 'TEXT', 'BINARY') THEN 1 END) AS A_满足要求的记录数,
        COUNT(*) AS B_总记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN response_data_type IN ('JSON', 'XML', 'TEXT', 'BINARY') THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND response_data_type IS NOT NULL; -- 只评估非空字段

    ```

    *(需要根据实际的参考数据列表调整 `IN (...)`)*

* **目标：检查 `openapi_type` 字段是否为空或在预定义的权威列表中。**

    ```sql
    -- 计算 openapi_type 字段引用权威参考数据的比率
    -- 假设权威列表为：'data', 'function'
    SELECT 
        COUNT(CASE WHEN openapi_type IS NULL OR openapi_type IN ('data', 'function') THEN 1 END) AS A,
        COUNT(*) AS B,
        ROUND(
            COUNT(CASE WHEN openapi_type IS NULL OR openapi_type IN ('data', 'function') THEN 1 END) * 1.0 / 
            COUNT(*), 
            4
        ) AS reference_data_ratio
    FROM sys_api 
    WHERE is_delete = b'0';
    ```

#### **0106 - 安全规范 (Security Specification)**

* **示例：检查当 `type` 为 'outer_api' 时且 `path` 包含通配符 `* ,** ,*.*`，`enabled` 是否为 `0`。**

    ```sql
    -- 0106 - 安全规范 - 检查外部API且包含通配符的路径禁用状态
    SELECT
        '0106' AS 指标编号,
        '安全规范' AS 指标名称,
        '检查当 type 为 ''outer_api'' 时且 path 包含通配符 ''*'' 或 ''*.*''，enabled 是否为 0' AS 指标描述,
        COUNT(*) AS B_总相关记录数, -- 只看 type='outer_api' 的记录
        COUNT(CASE WHEN enabled = b'0' THEN 1 END) AS A_满足规则的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN enabled = b'0' THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND type = 'outer_api'; -- 只评估相关记录

    ```

    *(需要根据实际的业务规则调整条件)*

* **示例：检查 `api_secret` 和 `api_secret_private` 是否不为明文存储（这里简化为检查是否为空，实际可能需要更复杂逻辑）。**

    ```sql
    -- 0106 - 安全规范 - 检查秘钥字段是否存储 (简化示例)
    -- 注意：严格来说，检查是否明文需要解密逻辑，这里仅检查是否存在
    SELECT
        '0106' AS 指标编号,
        '安全规范' AS 指标名称,
        '检查 api_secret 和 api_secret_private 字段是否已存储 (简化检查)' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN (api_secret IS NOT NULL AND api_secret != '') OR (api_secret_private IS NOT NULL AND api_secret_private != '') THEN 1 END) AS A_已存储秘钥的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN (api_secret IS NOT NULL AND api_secret != '') OR (api_secret_private IS NOT NULL AND api_secret_private != '') THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND (api_secret IS NOT NULL OR api_secret_private IS NOT NULL); -- 只看需要检查秘钥的记录

    -- 或者，检查已启用但未设置秘钥的API (反向检查)
    -- SELECT
    --     '0106' AS 指标编号,
    --     '安全规范' AS 指标名称,
    --     '检查已启用API是否设置了秘钥 (反向检查)' AS 指标描述,
    --     COUNT(*) AS B_总启用记录数,
    --     COUNT(CASE WHEN (api_secret IS NOT NULL AND api_secret != '') OR (api_secret_private IS NOT NULL AND api_secret_private != '') THEN 1 END) AS A_已设置秘钥的启用记录数,
    --     CASE WHEN COUNT(*) = 0 THEN NULL ELSE ROUND(COUNT(CASE WHEN (api_secret IS NOT NULL AND api_secret != '') OR (api_secret_private IS NOT NULL AND api_secret_private != '') THEN 1 END) * 100.0 / COUNT(*), 2) END AS 符合度百分比_X
    -- FROM sys_api
    -- WHERE is_delete = b'0' AND enabled = b'1';

    ```

* **示例：检查 `api_secret` 字段是否经过加密（例如，长度大于16位且为随机字符串，或通过加密函数处理,SQL中的简单推断）。**

    ```sql
    -- **警告**：这是一个非常简化的示例，仅检查长度。
    -- 真实场景中，明文密码/密钥是严重安全问题，应通过应用日志或安全扫描工具检查。
    SELECT 
        COUNT(CASE WHEN LENGTH(api_secret) > 32 THEN 1 END) AS A, -- 假设长字符串更可能是密文
        COUNT(*) AS B,
        ROUND(
            COUNT(CASE WHEN LENGTH(api_secret) > 32 THEN 1 END) * 1.0 / 
            COUNT(*), 
            4
        ) AS security_spec_ratio
    FROM sys_api 
    WHERE is_delete = b'0' AND api_secret IS NOT NULL;
    ```

### **2. 完整性 (Completeness)**

#### **0201 - 数据元素完整性 (Data Element Completeness)**

* **示例：检查核心字段 `name`, `path`, `method`, `app_id` 是否都非空。**

    ```sql
    -- 0201 - 数据元素完整性 - 检查核心字段是否完整
    SELECT
        '0201' AS 指标编号,
        '数据元素完整性' AS 指标名称,
        '检查核心字段 name, path, method, app_id 是否都非空' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN name IS NOT NULL AND name != '' AND path IS NOT NULL AND path != '' AND method IS NOT NULL AND method != '' AND app_id IS NOT NULL THEN 1 END) AS A_核心字段完整的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN name IS NOT NULL AND name != '' AND path IS NOT NULL AND path != '' AND method IS NOT NULL AND method != '' AND app_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0';

    ```

#### **0202 - 数据记录完整性 (Data Record Completeness)**

* **示例：检查已启用的API是否也填写了示例字段（业务规则要求）。**

    ```sql
    -- 0202 - 数据记录完整性 - 检查启用API是否填写了示例 (业务规则)
    SELECT
        '0202' AS 指标编号,
        '数据记录完整性' AS 指标名称,
        '检查已启用的API是否填写了 request_params_example 和 response_data_example' AS 指标描述,
        COUNT(*) AS B_总启用记录数,
        COUNT(CASE WHEN (request_params_example IS NOT NULL AND request_params_example != '') AND (response_data_example IS NOT NULL AND response_data_example != '') THEN 1 END) AS A_示例完整的启用记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN (request_params_example IS NOT NULL AND request_params_example != '') AND (response_data_example IS NOT NULL AND response_data_example != '') THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND enabled = b'1';

    ```

### **3. 准确性 (Accuracy)**

#### **0301 - 数据内容正确性 (Data Content Correctness)**

* **示例：检查 `path` 是否以 `/` 开头（假设这是业务要求的正确格式）。**

    ```sql
    -- 0301 - 数据内容正确性 - 检查 path 是否以 / 开头
    SELECT
        '0301' AS 指标编号,
        '数据内容正确性' AS 指标名称,
        '检查 path 字段是否以 / 开头' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN path LIKE '/%' THEN 1 END) AS A_内容正确的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN path LIKE '/%' THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND path IS NOT NULL AND path != '';

    ```

#### **0302 - 数据格式合规性 (Data Format Compliance)**

* **示例：检查 `create_time` 和 `update_time` 是否为合法的 datetime 格式（MySQL 通常能保证，但可检查非空和逻辑关系）。**

    ```sql
    -- 0302 - 数据格式合规性 - 检查时间字段非空且 create_time <= update_time
    SELECT
        '0302' AS 指标编号,
        '数据格式合规性' AS 指标名称,
        '检查时间字段非空且 create_time <= update_time' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN create_time IS NOT NULL AND update_time IS NOT NULL AND create_time <= update_time THEN 1 END) AS A_格式合规的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN create_time IS NOT NULL AND update_time IS NOT NULL AND create_time <= update_time THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0';

    ```

#### **0303 - 数据重复率 (Data Duplication Rate)**

* **示例：检查 `app_id`, `path`, `method` 组合的重复记录数。**

    ```sql
    -- 0303 - 数据重复率 - 检查 app_id, path, method 组合的重复
    WITH DuplicateGroups AS (
        SELECT app_id, path, method, COUNT(*) as cnt
        FROM sys_api
        WHERE is_delete = b'0'
        GROUP BY app_id, path, method
        HAVING COUNT(*) > 1
    )
    SELECT
        '0303' AS 指标编号,
        '数据重复率' AS 指标名称,
        '检查 app_id, path, method 组合的重复记录数' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COALESCE(SUM(dg.cnt), 0) AS A_重复记录总数, -- 计算所有重复组的记录数总和
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COALESCE(SUM(dg.cnt), 0) * 100.0 / COUNT(*), 2)
        END AS 重复率百分比_X
    FROM sys_api sa
    LEFT JOIN DuplicateGroups dg ON sa.app_id = dg.app_id AND sa.path = dg.path AND sa.method = dg.method
    WHERE sa.is_delete = b'0';

    ```

#### **0304 - 数据唯一性 (Data Uniqueness)**

* **示例：检查 `id` 主键的唯一性（数据库保证，但可验证）。**

    ```sql
    -- 0304 - 数据唯一性 - 检查 id 主键的唯一性 (数据库层面保证)
    -- 这个查询如果返回行，则表示有重复主键，违反唯一性
    SELECT
        '0304' AS 指标编号,
        '数据唯一性' AS 指标名称,
        '检查 id 主键的唯一性' AS 指标描述,
        COUNT(*) AS B_总记录数,
        (COUNT(*) - COUNT(DISTINCT id)) AS A_违反唯一性的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND((COUNT(*) - COUNT(DISTINCT id)) * 100.0 / COUNT(*), 2)
        END AS 违反唯一性百分比_X
    FROM sys_api
    WHERE is_delete = b'0';
    ```

* **示例：检查业务上的记录唯一性。**

    ```sql
    -- 0304 - 数据唯一性 - 检查业务上的唯一性，即 app_id、path 和 method 三个字段组合的唯一性
    -- 如果存在重复的组合，则意味着同一个应用下定义了路径和方法完全相同的API，这通常是不允许的
    SELECT
        '0304' AS 指标编号,
        '数据唯一性' AS 指标名称,
        '检查 app_id、path 和 method 三个字段组合的唯一性' AS 指标描述,
        COUNT(*) AS B_总记录数,
        (COUNT(*) - COUNT(DISTINCT CONCAT(app_id, '|', path, '|', method))) AS A_违反唯一性记录数,
        CASE WHEN COUNT(*) = 0 THEN NULL ELSE ROUND((COUNT(*) - COUNT(DISTINCT CONCAT(app_id, '|', path, '|', method))) * 100.0 / COUNT(*), 2) END AS 违反唯一性百分比_X
    FROM sys_api
    WHERE is_delete = b'0'; -- 仅评估未删除的有效数据
    ```

#### **0305 - 脏数据出现率 (Dirty Data Occurrence Rate)**

* **示例：检查 `response_code` 是否包含非数字或不在合理范围内的值。**

    ```sql
    -- 0305 - 脏数据出现率 - 检查 response_code 是否为合理数字
    SELECT
        '0305' AS 指标编号,
        '脏数据出现率' AS 指标名称,
        '检查 response_code 是否为 100-599 范围内的数字' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN response_code REGEXP '^[0-9]+$' AND CAST(response_code AS UNSIGNED) BETWEEN 100 AND 599 THEN 1 END) AS A_格式正确的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND((COUNT(*) - COUNT(CASE WHEN response_code REGEXP '^[0-9]+$' AND CAST(response_code AS UNSIGNED) BETWEEN 100 AND 599 THEN 1 END)) * 100.0 / COUNT(*), 2)
        END AS 脏数据率百分比_X -- 计算不符合的比率
    FROM sys_api
    WHERE is_delete = b'0' AND response_code IS NOT NULL AND response_code != '';

    ```

### **4. 一致性 (Consistency)**

#### **0401 - 相同数据一致性 (Same Data Consistency)**

* **错误示例：检查 `sys_api` 中的 `app_id` 是否在 `sys_app` 中存在。**

    ```sql
    -- 0401 - 相同数据一致性 - 检查 app_id 是否在 sys_app 中存在
    -- 假设存在 sys_app 表，且有 id 字段
    SELECT
        '0401' AS 指标编号,
        '相同数据一致性' AS 指标名称,
        '检查 sys_api 中的 app_id 是否在 sys_app 表中存在' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN sa.id IS NOT NULL THEN 1 END) AS A_一致的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN sa.id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api s_api
    LEFT JOIN sys_app sa ON s_api.app_id = sa.id -- 假设关联字段
    WHERE s_api.is_delete = b'0';

    ```

#### **0402 - 关联数据一致性 (Associated Data Consistency)**

* **示例：检查当 `enabled` 为 `0` 时，`flow_control_rule` 和 `degrade_rule` 是否也为空或标记为无效。**

    ```sql
    -- 0402 - 关联数据一致性 - 检查禁用API的规则字段
    SELECT
        '0402' AS 指标编号,
        '关联数据一致性' AS 指标名称,
        '检查当 enabled=0 时，flow_control_rule 和 degrade_rule 是否为空或无效' AS 指标描述,
        COUNT(*) AS B_总禁用记录数,
        COUNT(CASE WHEN (flow_control_rule IS NULL OR flow_control_rule = '') AND (degrade_rule IS NULL OR degrade_rule = '') THEN 1 END) AS A_一致的禁用记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN (flow_control_rule IS NULL OR flow_control_rule = '') AND (degrade_rule IS NULL OR degrade_rule = '') THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND enabled = b'0';
    ```

### **5. 时效性 (Timeliness)**

#### **0501 - 基于时间段的正确性 (Correctness Based on Time Period)**

* **示例：检查 `create_time` 是否在过去一年内（假设业务要求）。**

    ```sql
    -- 0501 - 基于时间段的正确性 - 检查 create_time 是否在过去一年内
    SELECT
        '0501' AS 指标编号,
        '基于时间段的正确性' AS 指标名称,
        '检查 create_time 是否在过去一年内' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN create_time >= DATE_SUB(NOW(), INTERVAL 1 YEAR) THEN 1 END) AS A_在时间段内的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN create_time >= DATE_SUB(NOW(), INTERVAL 1 YEAR) THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' AND create_time IS NOT NULL;

    ```

#### **0502 - 基于时间点及时性 (Timeliness Based on Time Point)**

* **示例：检查 `update_time` 与 `create_time` 的差异，计算平均更新延迟（假设业务有要求）。**

    ```sql
    -- 0502 - 基于时间点及时性 - 计算平均更新延迟 (天数)
    SELECT
        '0502' AS 指标编号,
        '基于时间点及时性' AS 指标名称,
        '计算平均更新延迟 (天数)' AS 指标描述,
        'N/A - 计算平均值' AS B_总记录数, -- 这个指标计算方式不同
        AVG(DATEDIFF(update_time, create_time)) AS A_平均延迟天数,
        NULL AS 符合度百分比_X -- 需要业务定义阈值来判断是否及时
    FROM sys_api
    WHERE is_delete = b'0' AND update_time IS NOT NULL AND create_time IS NOT NULL AND update_time > create_time;

    -- 或者，检查更新是否在创建后 N 天内发生
    -- SELECT
    --     '0502' AS 指标编号,
    --     '基于时间点及时性' AS 指标名称,
    --     '检查更新是否在创建后 30 天内发生' AS 指标描述,
    --     COUNT(*) AS B_总记录数,
    --     COUNT(CASE WHEN DATEDIFF(update_time, create_time) <= 30 THEN 1 END) AS A_及时更新的记录数,
    --     CASE WHEN COUNT(*) = 0 THEN NULL ELSE ROUND(COUNT(CASE WHEN DATEDIFF(update_time, create_time) <= 30 THEN 1 END) * 100.0 / COUNT(*), 2) END AS 符合度百分比_X
    -- FROM sys_api
    -- WHERE is_delete = b'0' AND update_time IS NOT NULL AND create_time IS NOT NULL AND update_time > create_time;

    ```

* **示例：此指标需要外部事件触发，无法仅用SQL完成。SQL只能查询 `update_time` 的分布。**

    ```sql
    -- 查询最近更新的API数量，作为时效性的一个侧面反映
    SELECT 
        COUNT(CASE WHEN update_time >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) AS updated_last_24h,
        COUNT(*) AS total_active,
        ROUND(
            COUNT(CASE WHEN update_time >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) * 1.0 / 
            COUNT(*), 
            4
        ) AS update_timeliness_proxy
    FROM sys_api 
    WHERE is_delete = b'0';
    ```

#### **0503 - 时序性 (Sequentiality)**

* **示例：检查 `create_time` <= `update_time` <= `delete_time` (如果已删除)。**

    ```sql
    -- 0503 - 时序性 - 检查 create_time <= update_time <= delete_time
    SELECT
        '0503' AS 指标编号,
        '时序性' AS 指标名称,
        '检查时间字段的时序关系 create_time <= update_time <= delete_time' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE
            WHEN create_time IS NOT NULL AND update_time IS NOT NULL AND (delete_time IS NULL OR delete_time IS NOT NULL) THEN
                CASE
                    WHEN create_time <= update_time AND (delete_time IS NULL OR (update_time <= delete_time)) THEN 1
                    ELSE 0
                END
            ELSE 0
        END) AS A_满足时序的记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE
                WHEN create_time IS NOT NULL AND update_time IS NOT NULL AND (delete_time IS NULL OR delete_time IS NOT NULL) THEN
                    CASE
                        WHEN create_time <= update_time AND (delete_time IS NULL OR (update_time <= delete_time)) THEN 1
                        ELSE 0
                    END
                ELSE 0
            END) * 100.0 / COUNT(*), 2)
        END AS 符合度百分比_X
    FROM sys_api
    WHERE is_delete = b'0' OR (is_delete = b'1' AND delete_time IS NOT NULL); -- 只检查有时序意义的记录

    ```

---

### **6. 可访问性 (Accessibility)**

#### **0601 - 可访问 (Accessible)**

* **示例：此指标通常在应用层面测试（如API调用成功率），数据库层面难以直接用SQL评估。**

    ```sql
    -- 0601 - 可访问 - 数据库层面难以直接评估
    -- 此指标通常通过应用监控、API网关日志或专门的可访问性测试工具来衡量。
    -- SQL 可以检查是否存在记录，但无法模拟“访问”过程。
    SELECT
        '0601' AS 指标编号,
        '可访问' AS 指标名称,
        '数据库层面难以直接评估，请通过应用监控检查' AS 指标描述,
        'N/A' AS A_满足要求的记录数,
        'N/A' AS B_总记录数,
        'N/A' AS 符合度百分比_X;

    ```

#### **0602 - 可用性 (Availability)**

* **示例：检查 `is_delete=0` 的记录占总记录的比例（假设未删除即为可用）。**

    ```sql
    -- 0602 - 可用性 - 检查 is_delete=0 的记录比例
    SELECT
        '0602' AS 指标编号,
        '可用性' AS 指标名称,
        '检查 is_delete=0 的记录比例 (假设未删除即为可用)' AS 指标描述,
        COUNT(*) AS B_总记录数,
        COUNT(CASE WHEN is_delete = b'0' THEN 1 END) AS A_可用记录数,
        CASE
            WHEN COUNT(*) = 0 THEN NULL
            ELSE ROUND(COUNT(CASE WHEN is_delete = b'0' THEN 1 END) * 100.0 / COUNT(*), 2)
        END AS 可用性百分比_X
    FROM sys_api;

    ```

## **使用说明**

这些 SQL 脚本提供了对 `sys_api` 表进行 GB/T 36344-2018 数据质量评价的基础。你可以根据实际的业务规则、数据标准和参考数据列表调整脚本中的具体条件和逻辑。

1. 请根据您实际的数据库环境（如MySQL, PostgreSQL等）调整SQL语法（例如正则表达式函数）。
2. 将脚本中的表名（如 `sys_app`）和预定义值列表替换为您系统中的真实值。
3. 这些脚本提供了量化指标的基础，您可以将结果集成到数据质量监控平台中。
