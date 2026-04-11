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

  it('shows single overview panel with summary and latest activity', () => {
    renderDashboardPage()

    // 第一层：单一资源总览面板
    expect(screen.getByText(/暂无数据/)).toBeInTheDocument()
    expect(screen.getByText(/最新活动/)).toBeInTheDocument()
  })

  it('shows three management entry cards', () => {
    renderDashboardPage()

    // 第二层：三张管理入口卡
    expect(screen.getByText('简历管理')).toBeInTheDocument()
    expect(screen.getByText('岗位管理')).toBeInTheDocument()
    expect(screen.getByText('面试管理')).toBeInTheDocument()
  })

  it('dashboard is NOT navigation distribution, no function entry cards, no quick entry title', () => {
    renderDashboardPage()
    // 删除功能入口卡
    expect(screen.queryByText('求职 Agent')).not.toBeInTheDocument()
    expect(screen.queryByText('简历优化')).not.toBeInTheDocument()
    expect(screen.queryByText('面试教练')).not.toBeInTheDocument()
    expect(screen.queryByText('申请追踪')).not.toBeInTheDocument()
    // 删除快速入口标题
    expect(screen.queryByText('快速入口')).not.toBeInTheDocument()
    // 删除导入
    expect(screen.queryByText('导入数据')).not.toBeInTheDocument()
  })
})