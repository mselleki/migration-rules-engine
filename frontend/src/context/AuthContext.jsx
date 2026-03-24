import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);
const STORAGE_KEY = "dgt_role";

export function AuthProvider({ children }) {
  const [role, setRole] = useState(() => localStorage.getItem(STORAGE_KEY));

  const login = (newRole) => {
    localStorage.setItem(STORAGE_KEY, newRole);
    setRole(newRole);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setRole(null);
  };

  return (
    <AuthContext.Provider value={{ role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
