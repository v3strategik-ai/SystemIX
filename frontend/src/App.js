import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Authentication
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';

// Components
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import LeadManagement from './components/LeadManagement';
import TaskManagement from './components/TaskManagement';
import WorkflowAutomation from './components/WorkflowAutomation';
import TeamManagement from './components/TeamManagement';
import Calendar from './components/Calendar';
import QuotingTool from './components/QuotingTool';
import DocumentCenter from './components/DocumentCenter';
import IntegrationsHub from './components/IntegrationsHub';
import Settings from './components/Settings';
import NetworkMonitoring from './components/NetworkMonitoring';
import AIChat from './components/AIChat';
import LoadingSpinner from './components/LoadingSpinner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { hasAccess } = useAuth();
  
  if (!hasAccess(requiredRole)) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Access Denied</h2>
          <p className="text-gray-600 dark:text-gray-400">You don't have permission to access this feature.</p>
        </div>
      </div>
    );
  }
  
  return children;
};

// Main Authenticated App Component
function AuthenticatedApp() {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
    name: 'Admin User',
    email: 'admin@systemix.ai',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facepad&facepad=2&w=256&h=256&q=80'
  });

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Test API connection
        const response = await axios.get(`${API}/`);
        console.log('API Connected:', response.data);
        
        // Initialize mock data
        await axios.post(`${API}/initialize-mock-data`);
        console.log('Mock data initialized');
        
        setLoading(false);
      } catch (error) {
        console.error('App initialization error:', error);
        setLoading(false);
      }
    };

    initializeApp();
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900 ${darkMode ? 'dark' : ''}`}>
      <BrowserRouter>
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar */}
          <Sidebar 
            open={sidebarOpen} 
            setOpen={setSidebarOpen}
            darkMode={darkMode}
            toggleDarkMode={toggleDarkMode}
            currentUser={user}
          />

          {/* Main Content */}
          <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
            {/* Header */}
            <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200/50 dark:border-gray-700/50 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    SystemIX AI Platinum Suite
                  </h1>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-3 py-1 rounded-full">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium">AI Active</span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-systemix-electric to-systemix-purple flex items-center justify-center border-2 border-blue-200 dark:border-blue-600">
                      <span className="text-white text-sm font-bold">{user.name.charAt(0)}</span>
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      {user.name}
                    </span>
                    <button
                      onClick={logout}
                      className="ml-2 text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 overflow-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/leads" element={<LeadManagement />} />
                <Route path="/tasks" element={<TaskManagement />} />
                <Route path="/workflows" element={<WorkflowAutomation />} />
                <Route path="/team" element={<TeamManagement />} />
                <Route path="/calendar" element={<Calendar />} />
                <Route path="/quotes" element={<QuotingTool />} />
                <Route path="/documents" element={<DocumentCenter />} />
                <Route path="/integrations" element={<IntegrationsHub />} />
                <Route path="/monitoring" element={<NetworkMonitoring />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>

          {/* AI Chat Assistant */}
          <AIChat />
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;