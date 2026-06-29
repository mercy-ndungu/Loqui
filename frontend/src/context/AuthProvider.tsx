import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { getMe } from "@/services/users";
import { logout as apiLogout } from "@/services/auth";
import type { User } from "@/types";
import { hasAuthenticatedFlag, setAuthenticatedFlag } from "@/utils/security";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginSuccess: (user: User) => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
      setAuthenticatedFlag(true);
    } catch {
      setUser(null);
      setAuthenticatedFlag(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      if (hasAuthenticatedFlag()) {
        await refreshUser();
      }
      setIsLoading(false);
    };
    void init();

    const onUnauthorized = () => {
      setUser(null);
      setAuthenticatedFlag(false);
    };
    window.addEventListener("loqui:unauthorized", onUnauthorized);
    return () => window.removeEventListener("loqui:unauthorized", onUnauthorized);
  }, [refreshUser]);

  const loginSuccess = useCallback((loggedInUser: User) => {
    setUser(loggedInUser);
    setAuthenticatedFlag(true);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
      setAuthenticatedFlag(false);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      loginSuccess,
      logout,
      refreshUser,
    }),
    [user, isLoading, loginSuccess, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
