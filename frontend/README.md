# 前端工作台（React + Vite）

这是 `AI 实习求职 Agent 系统` 的前端工作台。

当前前端已经覆盖：

- `/login` 登录页
- `/dashboard` 仪表盘
- `/resume` 简历中心
- `/jobs` 岗位匹配工作区
- `/interview` 面试准备工作区
- `/tracker` 投递追踪工作区

## 技术栈

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Tailwind CSS

## 本地启动

```bash
npm install
npm run dev
```

默认开发地址通常为 `http://127.0.0.1:5173`。

## 环境变量

- `VITE_API_BASE_URL`
  - 后端服务地址
  - 默认值：`http://127.0.0.1:8000`

如需修改，可编辑：

```text
frontend/.env
```

## 常用命令

```bash
npm run build
npm test
```

## 当前边界

当前前端重点是把现有后端能力整理为可演示、可联调的工作台。

已完成：

- 六个核心页面的统一产品化文案
- 认证后应用壳
- 与现有后端接口的基础联调

后续优先项：

- 文件上传闭环
- 更完整的页面状态与交互深化
