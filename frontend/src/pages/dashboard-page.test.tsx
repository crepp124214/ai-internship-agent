import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { DashboardPage } from './dashboard-page'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router', async () => {
  const actual = await vi.importActual('react-router')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function renderDashboardPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

describe('DashboardPage', () => {
  it('renders system overview with title', () => {
    renderDashboardPage()

    // 页面标题更新为系统总览
    expect(screen.getByRole('heading', { name: '系统总览' })).toBeInTheDocument()
  })

  it('shows system stats cards with navigation', () => {
    renderDashboardPage()

    // 显示系统状态卡片
    expect(screen.getByText('简历库')).toBeInTheDocument()
    expect(screen.getByText('目标岗位')).toBeInTheDocument()
    expect(screen.getByText('面试练习')).toBeInTheDocument()
    expect(screen.getByText('申请跟踪')).toBeInTheDocument()
  })

  it('shows console entry buttons', () => {
    renderDashboardPage()

    // 显示控制台入口
    expect(screen.getByText('求职 Agent')).toBeInTheDocument()
    expect(screen.getByText('简历优化')).toBeInTheDocument()
    expect(screen.getByText('面试教练')).toBeInTheDocument()
    expect(screen.getByText('申请追踪')).toBeInTheDocument()

    // 快速入口标题
    expect(screen.getByText('快速入口')).toBeInTheDocument()
  })

  it('dashboard is system overview type, no import, no recent activities, no inline ai assistant', () => {
    renderDashboardPage()
    // 删除导入数据按钮
    expect(screen.queryByText('导入数据')).not.toBeInTheDocument()
    // 删除最近活动
    expect(screen.queryByText('最近活动')).not.toBeInTheDocument()
    // 删除页面内 AI 助手入口
    expect(screen.queryByText('AI 求职助手')).not.toBeInTheDocument()
  })
})