# Wave 7：Real LLM Provider Integration

## 背景

OpenAI runtime 早期可用，但 precedence 与 fallback 规则不稳定。

## 目标

- 收口 provider/runtime precedence
- 保留 mock-first 开发体验

## 核心决策

1. 锁定 provider precedence
2. 完整覆盖 string/numeric fallback
3. 显式 settings 才参与有效 fallback
4. generate/chat 默认参数复用加入回归

## 结果

Wave 7 完成并冻结。
