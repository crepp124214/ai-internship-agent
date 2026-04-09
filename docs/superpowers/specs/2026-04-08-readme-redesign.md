# README 重设计

> 日期：2026-04-08 | 状态：草稿

## 决策

- 面向受众：HR + 普通用户（双受众）
- 方案 A：技术内容降级，主 README 易读，技术细节折叠到子文档

## 新 README 结构

```
1. tagline + 核心定位（1-2句，非技术人员看懂）
2. 三个核心功能（配简短说明，无术语）
3. 快速体验（3步命令，不需要懂代码）
4. 技术栈表格（名称+用途，5分钟理解）
5. 快速链接
6. License
```

## 技术内容迁移

| 内容 | 移到哪里 |
|------|----------|
| 架构 ASCII 图 | `docs/planning/memory-bank/architecture.md` |
| ReAct Loop / StateMachine / ToolRegistry 代码 | `docs/planning/memory-bank/architecture.md` |
| 完整 API 示例 | /docs（启动后访问） |
| 快速开始详细步骤 | CONTRIBUTING.md |

## 快速链接区块

```
## 想了解更多？

- [架构与 Agent 系统设计](docs/planning/memory-bank/architecture.md) — 技术架构图、ReAct Loop、ToolRegistry 详解
- [完整 API 文档](http://localhost:8000/docs) — 启动后访问
- [本地开发指南](CONTRIBUTING.md) — 环境搭建、测试运行
- [贡献指南](CONTRIBUTING.md) — Fork/PR 流程

## License

MIT
```
