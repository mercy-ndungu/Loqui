import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { AuthProvider } from "@/context/AuthProvider";
import { useAuth } from "@/hooks/useAuth";
import ChallengesHub from "./pages/ChallengesHub";
import Dashboard from "./pages/Dashboard";
import FeedbackResults from "./pages/FeedbackResults";
import ImprovChallenge from "./pages/ImprovChallenge";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import RecordPresentation from "./pages/RecordPresentation";
import TopicChallenge from "./pages/TopicChallenge";
import UploadPresentation from "./pages/UploadPresentation";

function PublicLoginRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <Login />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<PublicLoginRoute />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/challenges"
          element={
            <ProtectedRoute>
              <ChallengesHub />
            </ProtectedRoute>
          }
        />
        <Route
          path="/challenges/improv"
          element={
            <ProtectedRoute>
              <ImprovChallenge />
            </ProtectedRoute>
          }
        />
        <Route
          path="/challenges/topics"
          element={
            <ProtectedRoute>
              <TopicChallenge />
            </ProtectedRoute>
          }
        />
        <Route
          path="/presentations/upload"
          element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/presentations/:id/upload"
          element={
            <ProtectedRoute>
              <UploadPresentation />
            </ProtectedRoute>
          }
        />
        <Route
          path="/presentations/:id/record"
          element={
            <ProtectedRoute>
              <RecordPresentation />
            </ProtectedRoute>
          }
        />
        <Route
          path="/feedback/:recordingId"
          element={
            <ProtectedRoute>
              <FeedbackResults />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
