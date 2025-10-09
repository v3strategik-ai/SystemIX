import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showDefaultCredentials, setShowDefaultCredentials] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/login`, formData);
      const { access_token, user } = response.data;
      
      // Store token and user info in localStorage
      localStorage.setItem('systemix_token', access_token);
      localStorage.setItem('systemix_user', JSON.stringify(user));
      
      onLogin(user, access_token);
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (email, password) => {
    setFormData({ email, password });
    setShowDefaultCredentials(false);
  };

  const initializeDefaultUsers = async () => {
    try {
      await axios.post(`${API}/auth/initialize-default-users`);
      setShowDefaultCredentials(true);
    } catch (error) {
      console.error('Error initializing users:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-systemix-dark via-systemix-metallic to-systemix-dark flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="mx-auto w-20 h-20 bg-gradient-to-r from-systemix-electric via-systemix-bright-blue to-systemix-purple rounded-2xl flex items-center justify-center shadow-2xl shadow-systemix-electric/30 mb-4">
            <img 
              src="https://customer-assets.emergentagent.com/job_systemix-workspace/artifacts/0zxfh74m_slogo.PNG" 
              alt="SystemIX Logo" 
              className="h-12 w-auto object-contain filter drop-shadow-lg"
            />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">SystemIX AI</h1>
          <p className="text-gray-300">Platinum Suite</p>
        </div>

        {/* Login Form */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-200 mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-systemix-electric focus:border-transparent transition-all"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-200 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-systemix-electric focus:border-transparent transition-all"
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-systemix-electric via-systemix-bright-blue to-systemix-purple text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing In...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Demo Credentials */}
          <div className="mt-6 pt-6 border-t border-white/10">
            <p className="text-center text-gray-300 text-sm mb-4">Demo Access</p>
            
            {!showDefaultCredentials ? (
              <button
                onClick={initializeDefaultUsers}
                className="w-full py-2 px-4 bg-white/5 border border-white/20 rounded-xl text-gray-300 text-sm hover:bg-white/10 transition-all"
              >
                Initialize Demo Users
              </button>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={() => handleQuickLogin('admin@systemix.com', 'admin123')}
                  className="w-full py-2 px-4 bg-blue-500/20 border border-blue-500/30 rounded-xl text-blue-200 text-sm hover:bg-blue-500/30 transition-all"
                >
                  Login as Admin (Full Access)
                </button>
                <button
                  onClick={() => handleQuickLogin('employee@systemix.com', 'employee123')}
                  className="w-full py-2 px-4 bg-green-500/20 border border-green-500/30 rounded-xl text-green-200 text-sm hover:bg-green-500/30 transition-all"
                >
                  Login as Employee (Limited Access)
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;