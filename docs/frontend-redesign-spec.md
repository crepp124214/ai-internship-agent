# AI 实习求职 Agent — 前端 UI 重构设计规范

> 基于 Linear / Vercel / Notion / Cursor / Raycast / Claude 的设计语言

---

## 一、设计哲学

**核心理念**：极度克制，让用户专注于任务本身。

参考标杆：
- **Linear** — SaaS 高效工作流设计标杆，极简暗色模式，无缝键盘交互
- **Vercel** — 教科书级别的 Dashboard，卡片式设计，大圆角无阴影
- **Claude** — 大模型产品中最佳阅读体验，排版、字体、间距

**关键词**：克制、精确、留白、动作驱动、键盘优先

---

## 二、设计系统

### 2.1 色彩体系

```css
/* 暗色 Sidebar */
--color-deep: #0D0D0D;           /* 深黑，Linear 风格 */
--color-deep-elevated: #171717;  /* 卡片/面板背景 */

/* 亮色主区域 */
--color-canvas: #FAFAFA;         /* 主背景，极浅灰 */
--color-surface: #FFFFFF;         /* 卡片表面 */
--color-surface-hover: #F5F5F5;  /* 悬停状态 */

/* 边框与分割线 */
--color-border: #E5E5E5;           /* 常规边框 */
--color-border-subtle: #F0F0F0;   /* 极淡分割线 */

/* 文字层次 */
--color-ink-primary: #171717;     /* 主要文字 */
--color-ink-secondary: #737373;   /* 次要文字 */
--color-ink-tertiary: #A3A3A3;    /* 占位符/禁用 */

/* Accent（强调色） */
--color-accent: #FF5C00;          /* 活力橙，Vercel 风格 */
--color-accent-hover: #E54D00;    /* Accent 悬停 */

/* 语义色 */
--color-success: #22C55E;
--color-warning: #F59E0B;
--color-error: #EF4444;
--color-info: #3B82F6;

/* Diff 专用色 */
--color-diff-add: #22C55E;
--color-diff-add-bg: rgba(34, 197, 94, 0.1);
--color-diff-remove: #EF4444;
--color-diff-remove-bg: rgba(239, 68, 68, 0.1);
```

### 2.2 字体系统

```css
/* Display / 标题 */
font-family: 'Geist', 'Inter', -apple-system, sans-serif;

/* Body / 正文 */
font-family: 'Geist', 'Inter', -apple-system, sans-serif;

/* Code / 等宽 */
font-family: 'Geist Mono', 'JetBrains Mono', 'SF Mono', monospace;

/* 字重 */
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

**对比现行方案**：从 `DM Sans` 切换到 `Geist`（Vercel 自家字体，业界评价极高）

### 2.3 间距系统

```css
/* 基础单位：4px */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;

/* 页面内边距 */
--page-padding-x: 32px;   /* 桌面端 */
--page-padding-y: 24px;

/* 卡片圆角 */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 20px;
--radius-2xl: 24px;      /* Vercel 风格大圆角 */
```

### 2.4 阴影与层次

```css
/* 废弃传统阴影，改用 Border + Subtle Background 区分层次 */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);

/* 卡片：仅用 border 区分，不使用阴影 */
.card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
}
```

---

## 三、布局重构

### 3.1 整体框架

**现状**：左侧深色 Sidebar + 右侧内容区

**重构方向**：参考 Vercel Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  Sidebar (0D0D0D)  │  Main Content Area (FAFAFA)               │
│  - Logo/Brand      │  ┌──────────────────────────────────────┐  │
│  - Nav Items        │  │  Topbar (white, minimal)             │  │
│  - User Profile     │  │  - Breadcrumb / Page Title          │  │
│                     │  │  - Keyboard Shortcuts Hint (⌘K)     │  │
│                     │  └──────────────────────────────────────┘  │
│                     │  ┌──────────────────────────────────────┐  │
│                     │  │  Content (scrollable)                │  │
│                     │  │                                      │  │
│                     │  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Sidebar 重构

**现状**：72px 宽，深色背景，白色文字

**重构**（参考 Linear）：

```tsx
// 宽度：240px（可折叠至 56px）
// 背景：--color-deep (#0D0D0D)
// 文字：白色 70% opacity，激活态 100%

const sidebarStyles = {
  width: '240px',
  background: '#0D0D0D',
  borderRight: 'none',  // 无边框，纯色
}

// Nav Item 悬停态
'hover:bg-white/8 hover:text-white'

// Nav Item 激活态
'bg-white text-[#0D0D0D]'  // 白色背景，黑色文字，Linear 标志性风格
```

**关键细节**：
- Logo 区域：仅保留图标，hover 显示文字
- 导航项目：左侧竖条指示器（4px accent 色）替代背景色
- 底部用户区：极简，圆形头像 + 名称 + 退出按钮

---

## 四、四大模块重构方案

### 4.1 岗位匹配模块（参考 Linear + Vercel）

#### 现状问题
- 表格布局紧凑，信息密度过高
- 操作按钮分散
- 缺乏视觉层次

#### 重构方案

**卡片式岗位列表**（参考 Vercel Cards）：

```tsx
// 岗位卡片
const JobCard = ({ job, matchScore }) => (
  <div
    style={{
      background: 'white',
      border: '1px solid var(--color-border)',
      borderRadius: '20px',  // Vercel 风格大圆角
      padding: '20px 24px',
      transition: 'all 0.15s ease',
    }}
    className="hover:border-[var(--color-accent)] hover:scale-[1.01]"
  >
    {/* Header */}
    <div className="flex items-start justify-between mb-3">
      <div>
        <h3 className="font-semibold text-[var(--color-ink-primary)]">
          {job.title}
        </h3>
        <p className="text-sm text-[var(--color-ink-secondary)]">
          {job.company} · {job.location}
        </p>
      </div>
      {/* 匹配度徽章 */}
      <MatchBadge score={matchScore} />
    </div>

    {/* 技能标签 */}
    <div className="flex flex-wrap gap-2 mb-4">
      {job.tags?.slice(0, 4).map(tag => (
        <span
          key={tag}
          style={{
            background: 'var(--color-canvas)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '12px',
            color: 'var(--color-ink-secondary)',
          }}
        >
          {tag}
        </span>
      ))}
    </div>

    {/* 操作区 */}
    <div className="flex items-center gap-3 pt-3 border-t border-[var(--color-border-subtle)]">
      <button className="text-sm text-[var(--color-accent)] hover:underline">
        查看详情
      </button>
      <button className="text-sm text-[var(--color-ink-secondary)]">
        一键优化简历 →
      </button>
    </div>
  </div>
)

// 匹配度徽章
const MatchBadge = ({ score }) => {
  const color = score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'
  return (
    <div
      style={{
        background: `var(--color-${color})`,
        opacity: 0.1,
        borderRadius: '8px',
        padding: '4px 12px',
        fontSize: '12px',
        fontWeight: 600,
        color: `var(--color-${color})`,
      }}
    >
      {score}% 匹配
    </div>
  )
}
```

**键盘快捷键支持**（参考 Linear）：
- `J` / `K` — 上/下选择岗位
- `Enter` — 查看详情
- `⌘ + Enter` — 一键流转到简历优化
- `/` — 聚焦搜索框

**匹配度可视化**（参考 Linear 进度条）：
- 横向进度条，颜色渐变（红 → 黄 → 绿）
- 80% 以上：绿色，80-60%：黄色，60% 以下：红色

---

### 4.2 简历定制模块（参考 Notion + Cursor）

#### 现状问题
- 左侧简历原文，右侧操作区，交互割裂
- AI 修改建议以纯文本展示，不够直观
- 缺乏类似代码 review 的采纳/拒绝体验

#### 重构方案

**Notion 风格悬浮工具栏**：

```tsx
// 选中文字时的悬浮菜单
const FloatingToolbar = ({ selectedText, onAIEnhance, onAISummarize }) => (
  <div
    style={{
      position: 'absolute',
      top: '-40px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: '#171717',
      borderRadius: '8px',
      padding: '4px 8px',
      display: 'flex',
      gap: '4px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      animation: 'fadeInUp 0.15s ease',
    }}
  >
    <ToolbarButton onClick={onAIEnhance}>✨ 优化</ToolbarButton>
    <ToolbarButton onClick={onAISummarize}>📝 摘要</ToolbarButton>
    <ToolbarButton>💬 解释</ToolbarButton>
  </div>
)
```

**Cursor 风格 Diff 视图**（核心创新）：

```tsx
const ResumeDiffView = ({ original, optimized, onAccept, onReject }) => (
  <div
    style={{
      border: '1px solid var(--color-border)',
      borderRadius: '16px',
      overflow: 'hidden',
    }}
  >
    {/* Header */}
    <div
      style={{
        background: 'var(--color-canvas)',
        padding: '12px 20px',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <span className="text-sm font-medium">AI 修改建议</span>
      <div className="flex gap-2">
        <button
          onClick={onReject}
          style={{
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '13px',
            color: 'var(--color-ink-secondary)',
          }}
        >
          拒绝
        </button>
        <button
          onClick={onAccept}
          style={{
            background: 'var(--color-accent)',
            border: 'none',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '13px',
            fontWeight: 500,
            color: 'white',
          }}
        >
          采纳
        </button>
      </div>
    </div>

    {/* Diff Content */}
    <div
      style={{
        background: 'white',
        padding: '20px 24px',
        fontFamily: 'var(--font-mono)',
        fontSize: '14px',
        lineHeight: 1.7,
      }}
    >
      <DiffContent original={original} optimized={optimized} />
    </div>

    {/* 变更摘要 */}
    <div
      style={{
        background: 'var(--color-canvas)',
        padding: '12px 20px',
        borderTop: '1px solid var(--color-border-subtle)',
        fontSize: '13px',
        color: 'var(--color-ink-secondary)',
      }}
    >
      <span className="text-[var(--color-diff-add)]">+12 词新增</span>
      {' · '}
      <span className="text-[var(--color-diff-remove)]">-5 词删除</span>
    </div>
  </div>
)

// 渲染 Diff 片段
const DiffContent = ({ original, optimized }) => {
  // 使用 word-level diff 算法
  const diffs = computeWordDiff(original, optimized)

  return (
    <span>
      {diffs.map(([type, text], i) => {
        if (type === 'equal') return <span key={i}>{text}</span>
        if (type === 'insert') {
          return (
            <span
              key={i}
              style={{
                background: 'var(--color-diff-add-bg)',
                color: 'var(--color-diff-add)',
                textDecoration: 'underline',
                textDecorationStyle: 'wavy',
              }}
            >
              {text}
            </span>
          )
        }
        if (type === 'delete') {
          return (
            <span
              key={i}
              style={{
                background: 'var(--color-diff-remove-bg)',
                color: 'var(--color-diff-remove)',
                textDecoration: 'line-through',
              }}
            >
              {text}
            </span>
          )
        }
      })}
    </span>
  )
}
```

---

### 4.3 Agent 助手（参考 Raycast）

#### 现状问题
- AgentAssistantPanel 固定在页面右侧，占用空间
- 只能在本页面使用，无法跨模块调用
- 缺乏全局调起体验

#### 重构方案

**Raycast 风格 Command Palette**：

```tsx
// 全局快捷键：⌘ + K（在 useEffect 中注册）
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      setCommandPaletteOpen(true)
    }
  }
  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [])

// Command Palette Modal
const CommandPalette = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const commands = [
    { icon: '📄', label: '分析简历', action: () => navigate('/resume') },
    { icon: '💼', label: '搜索岗位', action: () => navigate('/jobs-explore') },
    { icon: '🎤', label: '开始面试', action: () => navigate('/interview') },
    { icon: '✨', label: '优化简历', action: () => dispatch优化简历() },
    { icon: '🔍', label: 'JD 分析', action: () => dispatchJD分析() },
  ]

  const filteredCommands = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '120px',
        zIndex: 9999,
        animation: 'fadeIn 0.1s ease',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '600px',
          maxHeight: '400px',
          background: 'white',
          borderRadius: '16px',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.2)',
          overflow: 'hidden',
          animation: 'slideUp 0.15s ease',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '20px' }}>🔍</span>
          <input
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0) }}
            placeholder="输入命令或问题..."
            autoFocus
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontSize: '16px',
              background: 'transparent',
            }}
          />
          <kbd
            style={{
              background: 'var(--color-canvas)',
              border: '1px solid var(--color-border)',
              borderRadius: '4px',
              padding: '2px 6px',
              fontSize: '12px',
              color: 'var(--color-ink-tertiary)',
            }}
          >
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div style={{ maxHeight: '320px', overflow: 'auto', padding: '8px' }}>
          {filteredCommands.map((cmd, i) => (
            <div
              key={cmd.label}
              onClick={() => { cmd.action(); onClose() }}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                background: i === selectedIndex ? 'var(--color-canvas)' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <span style={{ fontSize: '16px' }}>{cmd.icon}</span>
              <span className="text-sm">{cmd.label}</span>
              {i === selectedIndex && (
                <span className="ml-auto text-xs text-[var(--color-ink-tertiary)]">
                  ⏎ 运行
                </span>
              )}
            </div>
          ))}

          {/* AI 实时回答模式 */}
          {query.length > 2 && filteredCommands.length === 0 && (
            <div style={{ padding: '16px' }}>
              <p className="text-sm text-[var(--color-ink-secondary)] mb-3">
                按 Enter 搜索 "{query}"
              </p>
              <div
                style={{
                  background: 'var(--color-canvas)',
                  borderRadius: '8px',
                  padding: '12px',
                  fontSize: '14px',
                }}
              >
                <p className="text-xs text-[var(--color-ink-tertiary)] mb-2'>AI 回答</p>
                <p>正在分析 "{query}"...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

**关键交互**：
- `⌘ + K` — 全局唤起（任何页面）
- `↑` / `↓` — 选择命令
- `Enter` — 执行
- `ESC` — 关闭
- 输入文字 → 实时搜索 + AI 解读

---

### 4.4 AI 模拟面试（参考 Claude）

#### 现状问题
- ChatBubble 样式紧凑，气泡感过重
- 评分和建议与对话混在一起，层次不清
- 缺乏 Claude 那种优雅的阅读体验

#### 重构方案

**Claude 风格对话流**：

```tsx
// 面试对话容器
const InterviewConversation = ({ messages, onAnswerSubmit }) => (
  <div
    style={{
      maxWidth: '720px',
      margin: '0 auto',
      padding: '48px 32px',  // Claude 风格大边距
    }}
  >
    {messages.map((msg, i) => (
      <MessageBlock key={i} message={msg} />
    ))}
  </div>
)

// 消息块
const MessageBlock = ({ message }) => {
  const isUser = message.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        gap: '16px',
        marginBottom: '32px',  // Claude 风格大段落间距
        animation: 'fadeIn 0.2s ease',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: isUser ? 'var(--color-accent)' : 'var(--color-deep)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '14px',
          flexShrink: 0,
        }}
      >
        {isUser ? '🙂' : '🤖'}
      </div>

      {/* Content */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: '15px',
            lineHeight: 1.7,
            color: 'var(--color-ink-primary)',
          }}
        >
          {message.content}
        </div>

        {/* 评分卡片（仅 AI 消息） */}
        {message.score && (
          <ScoreCard score={message.score} feedback={message.feedback} />
        )}
      </div>
    </div>
  )
}

// 评分卡片
const ScoreCard = ({ score, feedback }) => (
  <div
    style={{
      marginTop: '16px',
      padding: '16px 20px',
      background: 'var(--color-canvas)',
      borderRadius: '12px',
      border: '1px solid var(--color-border-subtle)',
    }}
  >
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '8px',
      }}
    >
      <span
        style={{
          fontSize: '24px',
          fontWeight: 700,
          color: score >= 80 ? 'var(--color-success)' : score >= 60 ? 'var(--color-warning)' : 'var(--color-error)',
        }}
      >
        {score}
      </span>
      <span className="text-sm text-[var(--color-ink-secondary)]">/ 100</span>
    </div>
    <p className="text-sm text-[var(--color-ink-secondary)]">{feedback}</p>
  </div>
)

// 用户回答输入区
const AnswerInput = ({ onSubmit, disabled }) => (
  <div
    style={{
      position: 'sticky',
      bottom: 0,
      background: 'linear-gradient(transparent, white 20%)',
      padding: '24px 32px',
    }}
  >
    <div
      style={{
        maxWidth: '720px',
        margin: '0 auto',
        display: 'flex',
        gap: '12px',
      }}
    >
      <textarea
        placeholder="输入你的回答... (Shift + Enter 换行)"
        disabled={disabled}
        style={{
          flex: 1,
          padding: '14px 18px',
          border: '1px solid var(--color-border)',
          borderRadius: '12px',
          fontSize: '15px',
          lineHeight: 1.6,
          resize: 'none',
          minHeight: '52px',
          maxHeight: '200px',
          outline: 'none',
          transition: 'border-color 0.15s',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--color-accent)'}
        onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
      />
      <button
        disabled={disabled}
        style={{
          padding: '14px 24px',
          background: disabled ? 'var(--color-border)' : 'var(--color-accent)',
          color: 'white',
          border: 'none',
          borderRadius: '12px',
          fontWeight: 500,
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        提交
      </button>
    </div>
  </div>
)
```

**关键细节**：
- 大量留白（Claude 标志特点）
- 评分卡片内联插入对话流，而非单独的反馈区
- sticky 输入框，背景渐变遮罩
- 消息动画淡入

---

## 五、交互动效规范

### 5.1 全局动画

```css
/* 基础动画时长 */
--duration-fast: 0.1s;
--duration-normal: 0.15s;
--duration-slow: 0.25s;

/* 缓动函数 */
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);     /* 自然减速 */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1); /* 均衡 */

/* 关键动画 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
```

### 5.2 组件级动画

```tsx
// 卡片悬停
.card {
  transition: all var(--duration-fast) var(--ease-out);
}
.card:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
}

// 按钮按压
.button:active {
  transform: scale(0.97);
  transition: transform 0.05s;
}

// 页面切换
.page-enter {
  animation: fadeInUp 0.2s var(--ease-out);
}

// 模态框
.modal {
  animation: scaleIn 0.15s var(--ease-out);
}
```

---

## 六、键盘快捷键体系

参考 Linear，实现全局键盘优先体验：

| 快捷键 | 功能 | 作用域 |
|--------|------|--------|
| `⌘ K` | 打开 Command Palette | 全局 |
| `G D` | 跳转到仪表盘 | 全局 |
| `G J` | 跳转到岗位探索 | 全局 |
| `G R` | 跳转到简历优化 | 全局 |
| `G I` | 跳转到面试准备 | 全局 |
| `J / K` | 上/下选择 | 列表页 |
| `Enter` | 确认/查看详情 | 列表页 |
| `⌘ Enter` | 执行主操作 | 列表页 |
| `ESC` | 关闭模态框/取消 | 全局 |
| `?` | 显示快捷键帮助 | 全局 |

---

### 4.5 Agent 配置页面（参考 Vercel Settings）

#### 现状问题
- 三个 Agent 卡片平铺，视觉平淡
- 编辑表单与查看状态切换生硬
- Provider 选择下拉框缺乏品牌感

#### 重构方案

**Vercel 风格配置面板**：

```tsx
const AgentConfigCard = ({ agent, config, onSave, onDelete }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [formData, setFormData] = useState({ ...config })

  return (
    <div
      style={{
        background: 'white',
        border: `1px solid ${isExpanded ? 'var(--color-accent)' : 'var(--color-border)'}`,
        borderRadius: '16px',
        overflow: 'hidden',
        transition: 'all 0.15s ease',
      }}
    >
      {/* Card Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: '100%',
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <div className="flex items-center gap-4">
          {/* Agent Icon */}
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '10px',
              background: `linear-gradient(135deg, var(--color-accent), #FF8C42)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
            }}
          >
            {agent.icon}
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-ink-primary)]">
              {agent.label}
            </h3>
            <p className="text-sm text-[var(--color-ink-secondary)]">
              {agent.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {config ? (
            <div className="flex items-center gap-3">
              <ProviderBadge provider={config.provider} />
              <span className="text-sm text-[var(--color-ink-tertiary)]">
                {config.model}
              </span>
            </div>
          ) : (
            <span
              style={{
                padding: '4px 12px',
                background: 'var(--color-canvas)',
                borderRadius: '6px',
                fontSize: '12px',
                color: 'var(--color-ink-secondary)',
              }}
            >
              使用默认配置
            </span>
          )}
          <ChevronIcon expanded={isExpanded} />
        </div>
      </button>

      {/* Expanded Form */}
      {isExpanded && (
        <div
          style={{
            padding: '0 24px 24px',
            borderTop: '1px solid var(--color-border-subtle)',
            animation: 'fadeInUp 0.15s ease',
          }}
        >
          <div className="grid grid-cols-2 gap-4 mt-4">
            {/* Provider */}
            <div className="col-span-2">
              <label className="block text-xs font-medium text-[var(--color-ink-secondary)] mb-2">
                Provider
              </label>
              <ProviderSelector
                value={formData.provider}
                onChange={p => setFormData({ ...formData, provider: p })}
              />
            </div>

            {/* Model */}
            <div>
              <label className="block text-xs font-medium text-[var(--color-ink-secondary)] mb-2">
                Model
              </label>
              <input
                type="text"
                value={formData.model}
                onChange={e => setFormData({ ...formData, model: e.target.value })}
                placeholder="例如：gpt-4o-mini"
                className="input-field"
              />
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-xs font-medium text-[var(--color-ink-secondary)] mb-2">
                Temperature
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={e => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="flex-1"
                />
                <span className="text-sm w-8">{formData.temperature}</span>
              </div>
            </div>

            {/* API Key */}
            <div className="col-span-2">
              <label className="block text-xs font-medium text-[var(--color-ink-secondary)] mb-2">
                API Key
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={formData.api_key}
                  onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder="sk-..."
                  className="input-field pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-ink-tertiary)]"
                >
                  {showApiKey ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            {/* Base URL */}
            <div className="col-span-2">
              <label className="block text-xs font-medium text-[var(--color-ink-secondary)] mb-2">
                Base URL <span className="text-[var(--color-ink-tertiary)]">(可选)</span>
              </label>
              <input
                type="text"
                value={formData.base_url}
                onChange={e => setFormData({ ...formData, base_url: e.target.value })}
                placeholder="https://api.openai.com/v1"
                className="input-field"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 mt-6">
            <button
              onClick={() => onSave(formData)}
              style={{
                padding: '10px 20px',
                background: 'var(--color-accent)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              保存配置
            </button>
            {config && (
              <button
                onClick={onDelete}
                style={{
                  padding: '10px 20px',
                  background: 'transparent',
                  color: 'var(--color-error)',
                  border: '1px solid var(--color-error)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                }}
              >
                删除配置
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Provider 徽章
const ProviderBadge = ({ provider }) => {
  const colors = {
    'OpenAI': '#10A37F',
    'Anthropic': '#D4A574',
    'MiniMax': '#5C9FFF',
    'DeepSeek': '#7C3AED',
    '智谱 AI': '#7C3AED',
    '通义千问': '#7C3AED',
    'Moonshot': '#7C3AED',
    'SiliconFlow': '#7C3AED',
  }
  return (
    <span
      style={{
        padding: '4px 10px',
        borderRadius: '6px',
        fontSize: '12px',
        fontWeight: 500,
        background: `${colors[provider]}15`,
        color: colors[provider],
      }}
    >
      {provider}
    </span>
  )
}
```

**Provider 选择器（品牌色）**：

```tsx
const PROVIDERS = [
  { id: 'OpenAI', name: 'OpenAI', color: '#10A37F', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  { id: 'Anthropic', name: 'Anthropic', color: '#D4A574', models: ['claude-3-5-sonnet', 'claude-3-opus'] },
  { id: 'MiniMax', name: 'MiniMax', color: '#5C9FFF', models: ['abab6.5s-chat', 'abab6-chat'] },
  { id: 'DeepSeek', name: 'DeepSeek', color: '#7C3AED', models: ['deepseek-chat', 'deepseek-coder'] },
  // ... others
]

const ProviderSelector = ({ value, onChange }) => (
  <div className="grid grid-cols-4 gap-2">
    {PROVIDERS.map(p => (
      <button
        key={p.id}
        onClick={() => onChange(p.id)}
        style={{
          padding: '10px 12px',
          border: `1px solid ${value === p.id ? p.color : 'var(--color-border)'}`,
          borderRadius: '8px',
          background: value === p.id ? `${p.color}10` : 'white',
          cursor: 'pointer',
          textAlign: 'center',
          transition: 'all 0.15s',
        }}
      >
        <div
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: p.color,
            margin: '0 auto 6px',
          }}
        />
        <span style={{ fontSize: '11px', fontWeight: 500 }}>{p.name}</span>
      </button>
    ))}
  </div>
)
```

---

## 七、实施优先级

### Phase 1：基础设计系统（1-2天）
- [ ] 更新 CSS 变量（色彩、字体、间距）
- [ ] 引入 Geist 字体
- [ ] 重构 index.css / global.css
- [ ] 动画关键帧定义

### Phase 2：布局与导航（2-3天）
- [ ] Sidebar 重构（Linear 风格）
- [ ] Topbar 重构（添加快捷键提示）
- [ ] 全局 Command Palette 组件

### Phase 3：岗位匹配模块（2-3天）
- [ ] 岗位卡片组件
- [ ] 匹配度可视化（进度条 + 徽章）
- [ ] 列表页键盘导航

### Phase 4：简历定制模块（2-3天）
- [ ] Notion 风格悬浮工具栏
- [ ] Cursor 风格 Diff 视图
- [ ] Accept/Reject 交互

### Phase 5：面试模块（2天）
- [ ] Claude 风格对话流
- [ ] 评分卡片组件
- [ ] 优雅的输入区

### Phase 6：Agent 助手（1-2天）
- [ ] Raycast Command Palette 完善
- [ ] 全局快捷键绑定
- [ ] AI 实时搜索模式

### Phase 7：Agent 配置页面（1天）
- [ ] Agent 配置卡片组件
- [ ] Provider 选择器（品牌色网格）
- [ ] API Key 显示/隐藏切换
- [ ] 折叠/展开动画

---

## 八、技术注意事项

1. **字体加载**：使用 `Geist` 字体（Vercel 开源），通过 Google Fonts 或自托管
2. **Diff 算法**：引入 `diff` 库（npm）进行 word-level diff 计算
3. **键盘事件**：使用 `useHotkeys` hook（推荐 `react-hotkeys-hook`）管理快捷键
4. **动画性能**：优先使用 `transform` 和 `opacity`，避免布局抖动
5. **无障碍**：确保所有交互元素可通过键盘访问，使用 ARIA 标签
