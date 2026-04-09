# Release 封板 - 发布候选文件清单

> 基于当前 git status (`git status --short`) 生成

---

## 建议纳入发布的文件

### Backend (后端)
| 文件 | 状态 | 说明 |
|------|------|------|
| `pytest.ini` | M | 测试配置更新 |
| `scripts/run_tests.sh` | M | 测试脚本更新 |
| `src/main.py` | M | 主应用入口 |
| `src/presentation/schemas/interview.py` | M | Interview Schema 更新 |
| `src/utils/logger.py` | M | 日志工具更新 |

### Backend Tests (后端测试)
| 文件 | 状态 | 说明 |
|------|------|------|
| `tests/conftest.py` | M | 测试环境配置 |
| `tests/integration/api/test_interview_api.py` | M | Interview API 测试 |
| `tests/integration/api/test_jobs_api.py` | M | Jobs API 测试 |
| `tests/integration/api/test_system_api.py` | M | System API 测试 |
| `tests/integration/api/test_user_llm_configs_api.py` | M | LLM Configs API 测试 |
| `tests/unit/test_release_assets.py` | M | Release 资产测试 |

### Frontend (前端)
| 文件 | 状态 | 说明 |
|------|------|------|
| `frontend/package.json` | M | 依赖更新 (zustand) |
| `frontend/package-lock.json` | M | 依赖锁文件 |
| `frontend/src/app/providers.tsx` | M | 服务状态检测集成 |
| `frontend/src/auth/auth-provider.tsx` | M | 移除 TEMP auto-login |
| `frontend/src/auth/protected-route.tsx` | M | 恢复认证检查 |
| `frontend/src/lib/api.ts` | M | API 错误处理更新 |
| `frontend/src/pages/interview-page.tsx` | M | 面试页面更新 |
| `frontend/src/pages/jobs-page.tsx` | M | 岗位页面更新 |
| `frontend/src/pages/resume-page.tsx` | M | 简历页面更新 |
| `frontend/src/pages/settings/settings-interviews-page.tsx` | M | 设置页面更新 |

### Frontend Tests (前端测试)
| 文件 | 状态 | 说明 |
|------|------|------|
| `frontend/src/pages/interview-page.test.tsx` | M | Interview 测试修复 |
| `frontend/src/pages/jobs-page.test.tsx` | M | Jobs 测试修复 |
| `frontend/src/pages/resume-page.test.tsx` | M | Resume 测试修复 |
| `frontend/src/pages/wave5-smoke.test.tsx` | M | 烟雾测试修复 |

### Frontend New Files (前端新增)
| 文件 | 状态 | 说明 |
|------|------|------|
| `frontend/src/hooks/use-service-status.ts` | ?? | 服务状态管理 |
| `frontend/src/test/phase-c-flow.test.tsx` | ?? | Phase C 连续跑测试 |

### Docs (文档)
| 文件 | 状态 | 说明 |
|------|------|------|
| `.claude/settings.local.json` | M | Claude 本地设置 |
| `CLAUDE.md` | M | Claude 指令文件 |
| `Makefile` | M | 构建命令 |
| `docs/planning/memory-bank/architecture.md` | M | 架构文档 |
| `docs/planning/memory-bank/implementation-plan.md` | M | 实施计划 |
| `docs/release/known-issues.md` | M | 已知问题文档 |

### Docs New Files (文档新增)
| 文件 | 状态 | 说明 |
|------|------|------|
| `docs/frontend-redesign-spec.md` | ?? | 前端重构规格 |
| `docs/release/demo-script.md` | ?? | Demo 脚本 |
| `docs/release/portfolio-summary.md` | ?? | Portfolio 摘要 |
| `docs/superpowers/plans/*.md` | ?? | 多个实施计划文档 |

---

## 建议排除的文件

### 临时/本地文件
| 文件 | 状态 | 说明 |
|------|------|------|
| `.ccb/` | ?? | 本地会话缓存 |
| `.env.test` | ?? | 本地测试环境配置 |
| `msg2.txt` | ?? | 临时消息文件 |
| `opencode.json` | ?? | OpenCode 本地配置 |
| `phase_c_results.json` | ?? | Phase C 测试结果 |
| `run_main_chain.py` | ?? | 临时脚本 |
| `AGENTS.md` | ?? | 本地 Agent 配置 |

### 新增但可能不需要的模块
| 文件 | 状态 | 说明 |
|------|------|------|
| `design/` | ?? | 设计稿目录 |
| `src/business_logic/readiness/` | ?? | 就绪检查模块 (可能不完整) |
| `src/core/errors/` | ?? | 错误处理模块 (可能不完整) |
| `src/presentation/api/middleware/request_id.py` | ?? | Request ID 中间件 |
| `tests/unit/test_api_error_translator.py` | ?? | 错误翻译器测试 |

---

## 可执行命令

### 1. 检查待发布文件
```bash
# 仅查看 Modified 文件
git status --short | grep "^ M"

# 仅查看新增文件
git status --short | grep "^??"
```

### 2. 分批 add (推荐)

**批次 1: 核心后端**
```bash
git add pytest.ini scripts/run_tests.sh src/main.py src/presentation/schemas/interview.py src/utils/logger.py
```

**批次 2: 后端测试**
```bash
git add tests/conftest.py tests/integration/api/test_interview_api.py tests/integration/api/test_jobs_api.py tests/integration/api/test_system_api.py tests/integration/api/test_user_llm_configs_api.py tests/unit/test_release_assets.py
```

**批次 3: 前端核心**
```bash
git add frontend/package.json frontend/package-lock.json frontend/src/app/providers.tsx frontend/src/auth/auth-provider.tsx frontend/src/auth/protected-route.tsx frontend/src/lib/api.ts
```

**批次 4: 前端页面**
```bash
git add frontend/src/pages/interview-page.tsx frontend/src/pages/jobs-page.tsx frontend/src/pages/resume-page.tsx frontend/src/pages/settings/settings-interviews-page.tsx
```

**批次 5: 前端测试**
```bash
git add frontend/src/pages/interview-page.test.tsx frontend/src/pages/jobs-page.test.tsx frontend/src/pages/resume-page.test.tsx frontend/src/pages/wave5-smoke.test.tsx
```

**批次 6: 前端新增**
```bash
git add frontend/src/hooks/use-service-status.ts frontend/src/test/phase-c-flow.test.tsx
```

**批次 7: 文档**
```bash
git add .claude/settings.local.json CLAUDE.md Makefile docs/planning/memory-bank/architecture.md docs/planning/memory-bank/implementation-plan.md docs/release/known-issues.md
```

### 3. 最终复核
```bash
# 查看已暂存文件
git diff --cached --stat

# 排除不需要的文件 (如临时文件)
git reset .ccb/ msg2.txt opencode.json phase_c_results.json run_main_chain.py

# 确认无遗漏
git status --short
```

---

## 摘要

- **修改文件 (M)**: 30 个
- **新增文件 (?)**: 15 个
- **建议纳入**: 30 + 9 = 39 个核心文件
- **建议排除**: 7 个临时/本地文件 + 6 个可能不完整模块

**推荐操作**: 按上述分批 add 命令执行，确保核心功能纳入发布，排除临时文件。