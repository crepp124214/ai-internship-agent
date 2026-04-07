# Phase 7.5：数据初始化 设计文档

> 版本: v1.0.0 | 状态: 设计完成 | 日期: 2026-04-07

---

## 一、目标

1. **文件导入**：支持 PDF/DOCX 简历上传 + CSV/Excel JD 批量导入
2. **结构化解析**：从简历中提取姓名、学历、技能、工作经历
3. **示例数据**：预置 2-3 个简历 + 5-10 个 JD，一键初始化

---

## 二、功能详细设计

### 2.1 简历导入

**支持格式**：PDF、DOCX

**解析字段**：
- 姓名
- 学历（本科/硕士/博士）
- 技能标签
- 工作经历摘要
- 原始文本

**流程**：
```
用户上传 PDF/DOCX
    ↓
前端 Base64 编码
    ↓
POST /api/import/resume
    ↓
后端解析文件
    ↓
结构化提取
    ↓
存储到数据库
    ↓
返回解析结果
```

### 2.2 JD 批量导入

**支持格式**：CSV、Excel (.xlsx)

**字段映射**：
| CSV/Excel 列 | 数据库字段 |
|-------------|----------|
| title | 岗位名称 |
| company | 公司名称 |
| description | 岗位描述 |
| requirements | 任职要求 |
| location | 工作地点 |
| salary | 薪资范围 |

**流程**：
```
用户上传 CSV/Excel
    ↓
前端 FormData 提交
    ↓
POST /api/import/jds
    ↓
后端解析文件（pandas）
    ↓
批量插入数据库
    ↓
返回导入结果（成功数/失败数）
```

### 2.3 示例数据初始化

**方式一：脚本初始化**
```bash
python scripts/seed_demo.py
```

**方式二：前端触发**
- 登录后检测是否有数据
- 无数据则显示"加载示例数据"按钮
- 点击触发 POST /api/seed/example-data

**示例数据内容**：
- 2-3 个不同行业的简历（技术、金融、市场）
- 5-10 个 JD（覆盖不同岗位类型）

### 2.4 数据库迁移

- 依赖 Alembic 迁移脚本
- 初始化前检测表是否存在
- 已有数据时跳过，避免重复

---

## 三、文件结构

```
src/data_access/parsers/
  __init__.py
  resume_parser.py     # 新增：简历文件解析
  jd_parser.py         # 新增：JD 批量导入解析

src/presentation/api/v1/
  import.py            # 新增：导入 API 端点

scripts/
  seed_demo.py         # 修改：增加示例数据

frontend/src/pages/components/
  DataImportModal.tsx  # 新增：导入弹窗组件
```

---

## 四、API 设计

### 4.1 简历导入

```
POST /api/v1/import/resume
Content-Type: multipart/form-data

Request:
  file: PDF/DOCX 文件
  user_id: 用户 ID

Response:
  {
    "success": true,
    "resume_id": 123,
    "parsed": {
      "name": "张三",
      "education": "本科",
      "skills": ["Python", "Java"],
      "experience": "3年开发经验"
    }
  }
```

### 4.2 JD 批量导入

```
POST /api/v1/import/jds
Content-Type: multipart/form-data

Request:
  file: CSV/Excel 文件
  user_id: 用户 ID

Response:
  {
    "success": true,
    "total": 10,
    "imported": 9,
    "failed": 1,
    "errors": ["第5行格式错误"]
  }
```

### 4.3 示例数据

```
POST /api/v1/seed/example-data
Authorization: Bearer <token>

Response:
  {
    "success": true,
    "resumes_created": 3,
    "jobs_created": 8
  }
```

---

## 五、技术选型

| 组件 | 技术 |
|------|------|
| PDF 解析 | PyPDF2 / pdfplumber |
| DOCX 解析 | python-docx |
| Excel/CSV | pandas |
| 文件存储 | 数据库 BLOB 或文件系统 |

---

## 六、验收标准

1. 支持 PDF/DOCX 上传并正确解析
2. 支持 CSV/Excel 批量导入 JD
3. 示例数据脚本可独立运行
4. 前端可触发示例数据加载
5. 已有数据时不会重复创建
