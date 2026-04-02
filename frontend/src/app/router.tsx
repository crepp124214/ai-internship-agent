import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '../auth/protected-route'
import { AuthenticatedAppShell } from '../layout/authenticated-app-shell'
import { DashboardPage } from '../pages/dashboard-page'
import { InterviewPage } from '../pages/interview-page'
import { JobsPage } from '../pages/jobs-page'
import { LoginPage } from '../pages/login-page'
import { ResumePage } from '../pages/resume-page'
import { TrackerPage } from '../pages/tracker-page'

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
        <Route index element={<Navigate replace to="/dashboard" />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/resume" element={<ResumePage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/tracker" element={<TrackerPage />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/dashboard" />} />
    </Routes>
  )
}
