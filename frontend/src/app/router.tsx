import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '../auth/protected-route'
import { AuthenticatedAppShell } from '../layout/authenticated-app-shell'
import { DashboardPage } from '../pages/dashboard-page'
import { InterviewPage } from '../pages/interview-page'
import { JdCustomizePage } from '../pages/jd-customize-page'
import { JobsPage } from '../pages/jobs-page'
import { LoginPage } from '../pages/login-page'
import { ResumePage } from '../pages/resume-page'
import { SettingsPage } from '../pages/settings/settings-page'
import { SettingsResumesPage } from '../pages/settings/settings-resumes-page'
import { SettingsJobsPage } from '../pages/settings/settings-jobs-page'
import { SettingsInterviewsPage } from '../pages/settings/settings-interviews-page'
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
        <Route path="/jobs-explore" element={<JobsPage />} />
        <Route path="/resume" element={<ResumePage />} />
        <Route path="/jd-customize" element={<JdCustomizePage />} />
        <Route path="/jobs" element={<Navigate replace to="/jobs-explore" />} />
        <Route path="/dashboard" element={<Navigate replace to="/" />} />
        <Route path="/interview" element={<InterviewPage />} />

        {/* Settings pages */}
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/settings/resumes" element={<SettingsResumesPage />} />
        <Route path="/settings/jobs" element={<SettingsJobsPage />} />
        <Route path="/settings/interviews" element={<SettingsInterviewsPage />} />
        <Route path="/settings/agent-config" element={<AgentConfigPage />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}
