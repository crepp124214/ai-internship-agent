import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '../auth/protected-route'
import { AuthenticatedAppShell } from '../layout/authenticated-app-shell'
import { DashboardPage } from '../pages/dashboard-page'
import { InterviewPage } from '../pages/interview-page'
import { JdCustomizePage } from '../pages/jd-customize-page'
import { JobsPage } from '../pages/jobs-page'
import { LoginPage } from '../pages/login-page'
import { ResumePage } from '../pages/resume-page'
import { AgentConfigPage } from '../pages/settings/agent-config-page'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AuthenticatedAppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="/dashboard" element={<Navigate replace to="/" />} />
        <Route path="/jobs-explore" element={<JobsPage />} />
        <Route path="/resume" element={<ResumePage />} />
        <Route path="/jd-customize" element={<JdCustomizePage />} />
        <Route path="/jobs" element={<Navigate replace to="/jobs-explore" />} />
        <Route path="/dashboard" element={<Navigate replace to="/" />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/settings/agent-config" element={<AgentConfigPage />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/dashboard" />} />
    </Routes>
  )
}
