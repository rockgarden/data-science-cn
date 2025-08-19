# 数据质量维度关系图

```mermaid
graph TD
    A[数据质量 Data Quality] --> B[完整性 Completeness]
    A --> C[有效性 Validity]
    A --> D[一致性 Consistency]
    A --> E[准确性 Accuracy]
    A --> F[唯一性 Uniqueness]
    A --> G[及时性 Timeliness]

    %% 完整性（Completeness）
    B --> B1[缺失率 Missing Rate]
    B --> B2[有效非空率<br>Valid Non-Missing Rate]
    B --> B3[联合缺失率 Joint Missing Rate]
    B --> B4[加权缺失率 Weighted Missing Rate]
    B --> B5[必填字段合规率<br>Mandatory Field Compliance]

    style B fill:#4CAF50,stroke:#388E3C,color:white

    %% 有效性（Validity）
    C --> C1[格式合规性<br>Format Validation]
    C --> C2[值域合规性<br>Value Range]
    C --> C3[码表一致性<br>Lookup Table Match]
    C --> C4[身份证/手机号校验]

    style C fill:#2196F3,stroke:#1976D2,color:white

    %% 一致性（Consistency）
    D --> D1[跨系统一致性]
    D --> D2[跨字段逻辑一致性<br>Logical Completeness]
    D --> D3[时间顺序合理性<br>e.g., 注册时间 ≤ 登录时间]
    D --> D4[状态流转合规性<br>e.g., 待支付 → 已发货 ❌]

    style D fill:#FF9800,stroke:#F57C00,color:white

    %% 准确性（Accuracy）
    E --> E1[与真实世界一致]
    E --> E2[人工抽样核验]
    E --> E3[第三方数据比对]

    %% 完整性与有效性的交集
    B2 -.->|依赖| C1
    B2 -.->|依赖| C4

    %% 一致性与完整性的关系
    D2 -.->|输入| B
    D2 -.->|输入| C

    %% 示例说明
    classDef green fill:#4CAF50,stroke:#388E3C,color:white;
    classDef blue fill:#2196F3,stroke:#1976D2,color:white;
    classDef orange fill:#FF9800,stroke:#F57C00,color:white;

    class B1,B2,B3,B4,B5 green
    class C1,C2,C3,C4 blue
    class D1,D2,D3,D4 orange

    click B2 "https://example.com/validity-rules" "有效非空率依赖有效性规则"
    click D2 "https://example.com/logical-consistency" "逻辑完整性需综合完整与有效数据"

```

## 图解说明

| 区块 | 说明 |
|------|------|
| 🟩 **绿色：完整性** | 关注“是否应填尽填”，你提出的所有指标（缺失率、有效非空率等）都归属或服务于这一维度 |
| 🔵 **蓝色：有效性** | 关注“是否符合预定义格式与规则”，为“有效非空率”提供判断依据 |
| 🟠 **橙色：一致性** | 关注“跨字段/跨系统是否合理”，你提到的“逻辑完整性”真正归属于此 |
| ⬅️ **箭头虚线** | 表示“依赖关系”：例如“有效非空率”的计算依赖“有效性规则” |

## 特别说明：关于“有效非空率”的定位

在图中：

- “**有效非空率**” 属于 **完整性维度**
- 但它 **依赖于有效性规则** 来判断一个非空值是否“真正有效”

👉 这体现了实际业务中的常见做法：
> 我们仍然希望回答“这个字段有多完整？”，但答案不再只是“非空比例”，而是“**既非空又合法的比例**”。

## 可扩展建议

你还可以在此基础上增加：

1. 增加“数据丰度指数”作为顶层指标

    ```mermaid
    H[数据丰度指数] --> B
    H --> C
    H --> D
    ```

2. 增加“监控场景”应用层

    ```mermaid
    UseCase[应用场景] --> UC1[建模数据准入]
    UseCase --> UC2[监管合规报告]
    UseCase --> UC3[客户分层分析]

    UC1 --> B2
    UC1 --> D2
    UC2 --> B5
    UC3 --> H
    ```
