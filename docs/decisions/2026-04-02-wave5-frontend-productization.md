# Wave 5: Frontend Productization

## 背景

Wave 4 结束后，前端已经具备基础页面和接口联动能力，但仍存在两个明显问题：

1. 六个核心页面残留大量乱码和失真文案
2. 页面虽然能调用后端接口，但整体仍更像“接口演示壳”，而不是统一的产品工作台

因此本阶段不继续扩功能边界，而是先完成一次前端产品化收口。

## 阶段目标

- 修复 Login、Dashboard、Resume、Jobs、Interview、Tracker 六个核心页面中的乱码
- 统一应用壳、标题、按钮、提示、空状态和结果区的产品表达
- 保持后端 API 契约不变
- 为这轮前端收口补充最小可回归测试

## 核心决策

### D5.1 保持“文案和产品表达收口”为主，不在本阶段扩展后端契约

- 理由：当前最明显的问题不是 API 不够，而是前端表达失真，先收口用户感知层风险最低、收益最高。

### D5.2 六个页面统一收口到“AI 求职工作台 / 作品集展示版”的产品叙事

- 理由：需要形成一致的演示语境，避免登录页、仪表盘和业务页各说各话。

### D5.3 新增最小前端烟雾测试，而不是一次性补很多页面级测试

- 理由：本阶段重点是稳定产品化文案和应用壳；用小而稳的测试先锁住高价值结果，避免测试成本无边界膨胀。

## 影响范围

### 代码

- `frontend/src/pages/login-page.tsx`
- `frontend/src/pages/dashboard-page.tsx`
- `frontend/src/layout/authenticated-app-shell.tsx`
- `frontend/src/pages/resume-page.tsx`
- `frontend/src/pages/jobs-page.tsx`
- `frontend/src/pages/interview-page.tsx`
- `frontend/src/pages/tracker-page.tsx`
- `frontend/src/pages/wave5-smoke.test.tsx`

### 文档

- `.sisyphus/plans/PLAN.md`
- `.sisyphus/plans/progress.md`
- `docs/decisions/README.md`
- `PROJECT_MEMORY.md`

## 验证结果

### 前端构建

- `npm run build`
- 结果：通过

### 前端测试

- `npm test`
- 结果：通过，3 个测试文件 / 6 个测试

## 当前判断

Wave 5 已完成。前端不再停留在“页面能打开”的层面，而是形成了统一、可读、可演示的工作台表达。

本阶段没有解决的内容包括：

- 文件上传闭环
- 更完整的页面级交互深化
- 真实 LLM provider 接入

## 下一推荐任务

进入 `Wave 6: Frontend Capability Completion`，优先推进简历文件上传与更完整的前端交互闭环。
