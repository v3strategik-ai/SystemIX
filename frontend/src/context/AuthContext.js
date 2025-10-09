import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Setup axios interceptor for token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = localStorage.getItem('systemix_token');
      const savedUser = localStorage.getItem('systemix_user');

      if (savedToken && savedUser) {
        try {
          // Verify token is still valid
          axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
          const response = await axios.get(`${API}/auth/me`);
          
          setToken(savedToken);
          setUser(response.data);
        } catch (error) {
          // Token is invalid, clear stored data
          localStorage.removeItem('systemix_token');
          localStorage.removeItem('systemix_user');
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = (userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    localStorage.setItem('systemix_token', accessToken);
    localStorage.setItem('systemix_user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('systemix_token');
    localStorage.removeItem('systemix_user');
    delete axios.defaults.headers.common['Authorization'];
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const isEmployee = () => {
    return user?.role === 'employee';
  };

  const hasAccess = (requiredRole) => {
    if (!user) return false;
    if (requiredRole === 'admin') return user.role === 'admin';
    if (requiredRole === 'employee') return ['admin', 'employee'].includes(user.role);
    return true;
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAdmin,
    isEmployee,
    hasAccess,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};