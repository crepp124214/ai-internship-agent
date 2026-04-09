# 稳定试用就绪实施计划（Implementation Plan）

日期：2026-04-09  
对应设计：`docs/superpowers/specs/2026-04-09-stability-trial-readiness-design.md`

## 1. 目标

将系统从“可演示”提升到“可稳定试用”，并达到以下封板标准：

- 连续 20 次主链路通过率 >= 95%
- P0/P1 问题为 0
- 关键失败都可定位（含 request_id）

主链路：登录 -> 岗位探索 -> 简历优化 -> 面试准备 -> 设置中心。

## 2. 执行原则

- 仅做稳定性与体验保障，不扩展业务功能。
- 保持分层约束：`presentation -> business_logic -> data_access`。
- 先“防线”后“验证”：先补门控与错误语义，再跑回归与连续跑。
- 每个阶段都要有可执行验收命令和明确退出条件。

## 3. 任务拆分与责任边界

### 后端任务（Claude）

1. ReadinessGate 集中化
- 统一 DB/Redis/关键配置检查入口
- `/ready` 与关键接口可复用同一就绪判断

2. ApiErrorTranslator 落地
- 统一错误结构：`code/message/retryable/request_id`
- 关键接口（认证/岗位/简历/面试）消除裸 500 返回

3. request_id 贯通
- 错误响应中统一返回 `X-Request-ID`（或响应体字段）
- 日志中能按 request_id 追踪

4. 后端回归测试补齐
- 关键接口成功/失败路径
- 依赖不可用时返回 `503 + SERVICE_NOT_READY`

### 前端任务（OpenCode）

1. FrontendServiceStatus
- 应用启动探测 `/ready` 与 API baseURL 可达性
- 全局状态可消费

2. UserFacingFallbackPolicy
- 关键动作失败时统一反馈和重试入口
- 未就绪状态禁用关键按钮并展示原因

3. 路由与认证防线
- 设置中心主页可访问
- ProtectedRoute 恢复并纳入验收

4. 前端回归验证
- 主链路交互可恢复（失败有提示、可重试）

## 4. 执行阶段（顺序）

### Phase A：后端防线

输出：
- ReadinessGate + ApiErrorTranslator + request_id 基础能力
- 关键接口错误语义一致

退出条件：
- 依赖失效场景下关键接口不再出现裸 500
- API 错误结构稳定

### Phase B：前端防线

输出：
- 全局服务状态检测
- 关键交互降级/禁用/重试路径
- 路由和认证入口恢复完整

退出条件：
- 主链路任意失败都能给出可理解提示
- 设置中心可访问，未登录访问受控

### Phase C：回归与连续跑

输出：
- API 回归结果
- 前端主链路回归结果
- 20 次连续跑统计报告

退出条件：
- 通过率 >= 95%
- P0/P1 = 0
- 失败带 request_id 且可归因

## 5. 派发顺序（严格执行）

1. 派发 Claude：Phase A  
2. `pend claude` 直到完成  
3. 审查 Claude 结果，不通过则返修  
4. 派发 OpenCode：Phase B  
5. `pend opencode` 直到完成  
6. 审查 OpenCode 结果，不通过则返修  
7. 双方通过后，派发任一可用节点执行 Phase C 连续跑与结果汇总  
8. 最终验收并输出封板结论

降级规则：
- Claude 不可用：`[降级接管]` 交给 OpenCode
- OpenCode 不可用：`[降级接管]` 交给 Claude

## 6. 验证命令基线

后端测试：
- `APP_ENV=development python -m pytest tests/unit tests/integration --ignore=tests/unit/data_access/test_entities.py -q`

覆盖率：
- `APP_ENV=development python -m pytest tests/unit tests/integration --cov=src --cov-report=term --ignore=tests/unit/data_access/test_entities.py`

前端构建：
- `cd frontend && npm run build`

连续跑：
- 按固定主链路脚本执行 20 次，输出通过率与失败明细（含 request_id）。

## 7. 风险与缓解

风险 1：依赖未就绪导致链路误报可用  
缓解：以 `/ready` 和服务状态为唯一可用信号，不以 `/health` 判定可试用。

风险 2：错误码漂移导致前端回退到字符串判断  
缓解：错误码契约写入接口文档，回归中强校验 `code/retryable`。

风险 3：本地环境差异影响回归稳定性  
缓解：统一 `APP_ENV=development` 验证口径，并记录运行前置条件。

## 8. 完成定义（Definition of Done）

- 设计中定义的三层防线全部落地
- API 与前端回归全部通过
- 20 次连续跑达标（>=95%，无 P0/P1）
- 发布结论可追踪（含问题清单、证据、request_id）

