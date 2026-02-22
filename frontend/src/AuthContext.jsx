import { createContext, useContext, useState, useEffect } from "react";
import { auth as authApi } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const u = localStorage.getItem("wms_user");
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(!!localStorage.getItem("wms_token"));

  useEffect(() => {
    const token = localStorage.getItem("wms_token");
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((u) => {
        setUser(u);
        localStorage.setItem("wms_user", JSON.stringify(u));
      })
      .catch(() => {
        setUser(null);
        localStorage.removeItem("wms_token");
        localStorage.removeItem("wms_user");
      })
      .finally(() => setLoading(false));
  }, []);

  const login = (token, userData) => {
    localStorage.setItem("wms_token", token);
    localStorage.setItem("wms_user", JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("wms_token");
    localStorage.removeItem("wms_user");
    setUser(null);
  };

  const can = (moduleId) => {
    if (!user) return false;
    if (user.role === "admin") return true;
    return (user.allowed_modules || []).includes(moduleId);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
