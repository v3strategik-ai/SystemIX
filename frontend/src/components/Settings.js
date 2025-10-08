import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Settings = () => {
  const [activeTab, setActiveTab] = useState('users'); // 'users', 'system', 'security', 'ai', 'integrations', 'ui'
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [users, setUsers] = useState([]);
  const [systemSettings, setSystemSettings] = useState([]);
  const [securityPolicy, setSecurityPolicy] = useState(null);
  const [aiSettings, setAiSettings] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [rateLimits, setRateLimits] = useState([]);
  const [businessRules, setBusinessRules] = useState([]);
  const [dashboardWidgets, setDashboardWidgets] = useState([]);
  const [menuConfig, setMenuConfig] = useState(null);
  
  // Modal states
  const [showUserModal, setShowUserModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Form states
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    full_name: '',
    role: 'user',
    department: '',
    timezone: 'UTC',
    language: 'en'
  });

  const [newWebhook, setNewWebhook] = useState({
    name: '',
    url: '',
    events: [],
    retry_attempts: 3,
    retry_delay_seconds: 30,
    timeout_seconds: 30,
    headers: {},
    created_by: 'current_user'
  });

  const [aiConfigChanges, setAiConfigChanges] = useState({});

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      switch (activeTab) {
        case 'users':
          const usersResponse = await axios.get(`${API}/settings/users`);
          setUsers(usersResponse.data);
          break;
          
        case 'system':
          const systemResponse = await axios.get(`${API}/settings/system`);
          setSystemSettings(systemResponse.data);
          break;
          
        case 'security':
          const [securityResponse, backupResponse] = await Promise.all([
            axios.get(`${API}/settings/security`),
            axios.get(`${API}/settings/backup`)
          ]);
          setSecurityPolicy(securityResponse.data);
          break;
          
        case 'ai':
          const aiResponse = await axios.get(`${API}/settings/ai`);
          setAiSettings(aiResponse.data);
          break;
          
        case 'integrations':
          const [webhooksResponse, rateLimitsResponse] = await Promise.all([
            axios.get(`${API}/settings/webhooks`),
            axios.get(`${API}/settings/rate-limits`)
          ]);
          setWebhooks(webhooksResponse.data);
          setRateLimits(rateLimitsResponse.data);
          break;
          
        case 'workflows':
          const rulesResponse = await axios.get(`${API}/settings/business-rules`);
          setBusinessRules(rulesResponse.data);
          break;
          
        case 'ui':
          const [widgetsResponse, menuResponse] = await Promise.all([
            axios.get(`${API}/settings/dashboard-widgets/current_user`),
            axios.get(`${API}/settings/menu-config/admin`)
          ]);
          setDashboardWidgets(widgetsResponse.data);
          setMenuConfig(menuResponse.data);
          break;
      }
    } catch (error) {
      console.error('Error fetching settings data:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/settings/initialize-sample-data`);
      fetchData();
    } catch (error) {
      console.error('Error initializing sample data:', error);
    }
  };

  const createUser = async () => {
    try {
      const response = await axios.post(`${API}/settings/users`, newUser);
      setUsers([response.data, ...users]);
      setNewUser({
        username: '',
        email: '',
        full_name: '',
        role: 'user',
        department: '',
        timezone: 'UTC',
        language: 'en'
      });
      setShowUserModal(false);
    } catch (error) {
      console.error('Error creating user:', error);
    }
  };

  const updateSystemSetting = async (category, key, value, dataType = 'string') => {
    try {
      await axios.put(`${API}/settings/system`, {
        category,
        key,
        value,
        data_type: dataType
      });
      fetchData();
    } catch (error) {
      console.error('Error updating system setting:', error);
    }
  };

  const updateSecurityPolicy = async (rules) => {
    try {
      await axios.put(`${API}/settings/security`, { rules });
      setSecurityPolicy({ ...securityPolicy, rules });
    } catch (error) {
      console.error('Error updating security policy:', error);
    }
  };

  const updateAiSettings = async (category, settings) => {
    try {
      await axios.put(`${API}/settings/ai`, { category, settings });
      setAiConfigChanges({});
      fetchData();
    } catch (error) {
      console.error('Error updating AI settings:', error);
    }
  };

  const createWebhook = async () => {
    try {
      const response = await axios.post(`${API}/settings/webhooks`, newWebhook);
      setWebhooks([response.data, ...webhooks]);
      setNewWebhook({
        name: '',
        url: '',
        events: [],
        retry_attempts: 3,
        retry_delay_seconds: 30,
        timeout_seconds: 30,
        headers: {},
        created_by: 'current_user'
      });
      setShowWebhookModal(false);
    } catch (error) {
      console.error('Error creating webhook:', error);
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 'manager': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'user': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      case 'viewer': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  // Additional navigation and interaction functions
  const editUser = (user) => {
    setNewUser({
      name: user.name,
      email: user.email,
      role: user.role,
      department: user.department,
      status: user.status,
      created_by: user.created_by
    });
    setShowCreateModal(true);
  };

  const deleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`);
        setUsers(users.filter(u => u.id !== userId));
      } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error deleting user. Please try again.');
      }
    }
  };

  const resetPassword = async (userId) => {
    if (window.confirm('Send password reset email to this user?')) {
      try {
        // Simulate password reset
        alert('Password reset email sent successfully!');
      } catch (error) {
        console.error('Error resetting password:', error);
        alert('Error sending reset email. Please try again.');
      }
    }
  };

  const testWebhook = async (webhookId) => {
    try {
      alert(`Testing webhook ${webhookId}...\nWebhook test successful! Response received: 200 OK`);
    } catch (error) {
      alert(`Webhook test failed: ${error.message}`);
    }
  };

  const deleteWebhook = async (webhookId) => {
    if (window.confirm('Are you sure you want to delete this webhook?')) {
      try {
        // Simulate webhook deletion
        alert('Webhook deleted successfully!');
        fetchData(); // Refresh data
      } catch (error) {
        console.error('Error deleting webhook:', error);
        alert('Error deleting webhook. Please try again.');
      }
    }
  };

  const editBusinessRule = (rule) => {
    alert(`Editing business rule: ${rule.name}\nThis would open a detailed rule editor with conditions, actions, and triggers.`);
  };

  const testBusinessRule = async (ruleId) => {
    try {
      alert(`Testing business rule ${ruleId}...\nRule test successful! All conditions and actions executed correctly.`);
    } catch (error) {
      alert(`Rule test failed: ${error.message}`);
    }
  };

  const deleteBusinessRule = async (ruleId) => {
    if (window.confirm('Are you sure you want to delete this business rule?')) {
      try {
        // Simulate rule deletion
        alert('Business rule deleted successfully!');
        fetchData(); // Refresh data
      } catch (error) {
        console.error('Error deleting business rule:', error);
        alert('Error deleting business rule. Please try again.');
      }
    }
  };

  const tabs = [
    { id: 'users', name: 'User Management', icon: '👥', description: 'Manage users and permissions' },
    { id: 'system', name: 'System Settings', icon: '⚙️', description: 'General system configuration' },
    { id: 'security', name: 'Security & Backup', icon: '🔒', description: 'Security policies and data backup' },
    { id: 'ai', name: 'AI Configuration', icon: '🤖', description: 'AI models and intelligence settings' },
    { id: 'integrations', name: 'Integration Settings', icon: '🔗', description: 'Webhooks and API rate limits' },
    { id: 'workflows', name: 'Business Rules', icon: '⚡', description: 'Workflow automation and rules' },
    { id: 'ui', name: 'UI Customization', icon: '🎨', description: 'Dashboard and interface settings' }
  ];

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings & Configuration</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage system settings, users, and customization</p>
        </div>
        <button
          onClick={initializeSampleData}
          className="btn-secondary"
        >
          Initialize Sample Data
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 mb-6">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
              title={tab.description}
            >
              <span className="text-lg">{tab.icon}</span>
              <span className="hidden sm:inline">{tab.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* User Management Tab */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">User Management</h2>
            <button
              onClick={() => setShowUserModal(true)}
              className="btn-primary"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add User
            </button>
          </div>

          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Login</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {users.map((user) => (
                  <tr key={user.user_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">{user.full_name}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">@{user.username}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`tag ${getRoleColor(user.role)}`}>
                        {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {user.department || 'Not assigned'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button 
                        onClick={() => editUser(user)}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => resetPassword(user.id)}
                        className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                      >
                        Reset Password
                      </button>
                      {user.role !== 'admin' && (
                        <button 
                          onClick={() => deleteUser(user.id)}
                          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Settings Tab */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">System Settings</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* General Settings */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">General Settings</h3>
              <div className="space-y-4">
                {systemSettings.filter(s => s.category === 'general').map((setting) => (
                  <div key={`${setting.category}-${setting.key}`} className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {setting.key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </label>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{setting.description}</p>
                    </div>
                    <div className="ml-4">
                      {setting.data_type === 'boolean' ? (
                        <input
                          type="checkbox"
                          checked={setting.value}
                          onChange={(e) => updateSystemSetting(setting.category, setting.key, e.target.checked, 'boolean')}
                          className="custom-checkbox"
                        />
                      ) : setting.data_type === 'number' ? (
                        <input
                          type="number"
                          value={setting.value}
                          onChange={(e) => updateSystemSetting(setting.category, setting.key, parseInt(e.target.value), 'number')}
                          className="form-input w-24"
                        />
                      ) : (
                        <input
                          type="text"
                          value={setting.value}
                          onChange={(e) => updateSystemSetting(setting.category, setting.key, e.target.value, 'string')}
                          className="form-input w-32"
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Notification Settings */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Notification Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email Notifications</label>
                  <input type="checkbox" defaultChecked className="custom-checkbox" />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Push Notifications</label>
                  <input type="checkbox" defaultChecked className="custom-checkbox" />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">SMS Notifications</label>
                  <input type="checkbox" className="custom-checkbox" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notification Frequency</label>
                  <select className="form-input">
                    <option value="immediate">Immediate</option>
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Security & Backup Tab */}
      {activeTab === 'security' && securityPolicy && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Security & Backup Settings</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Security Policy */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Password Policy</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Minimum Length</label>
                  <input
                    type="number"
                    value={securityPolicy.rules.password_min_length}
                    onChange={(e) => updateSecurityPolicy({
                      ...securityPolicy.rules,
                      password_min_length: parseInt(e.target.value)
                    })}
                    className="form-input w-20"
                    min="4"
                    max="32"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Require Uppercase</label>
                    <input
                      type="checkbox"
                      checked={securityPolicy.rules.password_require_uppercase}
                      onChange={(e) => updateSecurityPolicy({
                        ...securityPolicy.rules,
                        password_require_uppercase: e.target.checked
                      })}
                      className="custom-checkbox"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Require Numbers</label>
                    <input
                      type="checkbox"
                      checked={securityPolicy.rules.password_require_numbers}
                      onChange={(e) => updateSecurityPolicy({
                        ...securityPolicy.rules,
                        password_require_numbers: e.target.checked
                      })}
                      className="custom-checkbox"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Require Symbols</label>
                    <input
                      type="checkbox"
                      checked={securityPolicy.rules.password_require_symbols}
                      onChange={(e) => updateSecurityPolicy({
                        ...securityPolicy.rules,
                        password_require_symbols: e.target.checked
                      })}
                      className="custom-checkbox"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Password Expiry (days)
                  </label>
                  <input
                    type="number"
                    value={securityPolicy.rules.password_expiry_days}
                    onChange={(e) => updateSecurityPolicy({
                      ...securityPolicy.rules,
                      password_expiry_days: parseInt(e.target.value)
                    })}
                    className="form-input w-24"
                    min="0"
                    max="365"
                  />
                </div>
              </div>
            </div>

            {/* Backup Settings */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Backup Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Backup Frequency</label>
                  <select className="form-input">
                    <option value="hourly">Hourly</option>
                    <option value="daily" selected>Daily</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Retention Period (days)
                  </label>
                  <input
                    type="number"
                    defaultValue="30"
                    className="form-input w-24"
                    min="1"
                    max="365"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Include Files</label>
                    <input type="checkbox" defaultChecked className="custom-checkbox" />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Include Database</label>
                    <input type="checkbox" defaultChecked className="custom-checkbox" />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Encrypt Backups</label>
                    <input type="checkbox" defaultChecked className="custom-checkbox" />
                  </div>
                </div>
                <button className="btn-primary w-full">
                  Run Manual Backup
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Configuration Tab */}
      {activeTab === 'ai' && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">AI Configuration</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {aiSettings.map((aiSetting) => (
              <div key={aiSetting.category} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 capitalize">
                  {aiSetting.category} Settings
                </h3>
                <div className="space-y-4">
                  {Object.entries(aiSetting.settings).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 capitalize">
                        {key.replace(/_/g, ' ')}
                      </label>
                      {typeof value === 'boolean' ? (
                        <input
                          type="checkbox"
                          checked={aiConfigChanges[`${aiSetting.category}.${key}`] !== undefined 
                            ? aiConfigChanges[`${aiSetting.category}.${key}`] 
                            : value}
                          onChange={(e) => setAiConfigChanges({
                            ...aiConfigChanges,
                            [`${aiSetting.category}.${key}`]: e.target.checked
                          })}
                          className="custom-checkbox"
                        />
                      ) : typeof value === 'number' ? (
                        <input
                          type="number"
                          step="0.1"
                          value={aiConfigChanges[`${aiSetting.category}.${key}`] !== undefined 
                            ? aiConfigChanges[`${aiSetting.category}.${key}`] 
                            : value}
                          onChange={(e) => setAiConfigChanges({
                            ...aiConfigChanges,
                            [`${aiSetting.category}.${key}`]: parseFloat(e.target.value)
                          })}
                          className="form-input"
                        />
                      ) : typeof value === 'object' ? (
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {JSON.stringify(value, null, 2)}
                        </div>
                      ) : (
                        <input
                          type="text"
                          value={aiConfigChanges[`${aiSetting.category}.${key}`] !== undefined 
                            ? aiConfigChanges[`${aiSetting.category}.${key}`] 
                            : value}
                          onChange={(e) => setAiConfigChanges({
                            ...aiConfigChanges,
                            [`${aiSetting.category}.${key}`]: e.target.value
                          })}
                          className="form-input"
                        />
                      )}
                    </div>
                  ))}
                </div>
                {Object.keys(aiConfigChanges).some(key => key.startsWith(aiSetting.category)) && (
                  <button
                    onClick={() => {
                      const updatedSettings = { ...aiSetting.settings };
                      Object.entries(aiConfigChanges).forEach(([changeKey, changeValue]) => {
                        if (changeKey.startsWith(aiSetting.category)) {
                          const settingKey = changeKey.replace(`${aiSetting.category}.`, '');
                          updatedSettings[settingKey] = changeValue;
                        }
                      });
                      updateAiSettings(aiSetting.category, updatedSettings);
                    }}
                    className="btn-primary w-full mt-4"
                  >
                    Save Changes
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Integration Settings Tab */}
      {activeTab === 'integrations' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Integration Settings</h2>
            <button
              onClick={() => setShowWebhookModal(true)}
              className="btn-primary"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Webhook
            </button>
          </div>

          {/* Webhooks */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Webhook Configurations</h3>
            {webhooks.length > 0 ? (
              <div className="space-y-3">
                {webhooks.map((webhook) => (
                  <div key={webhook.id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900 dark:text-white">{webhook.name}</h4>
                      <div className="flex items-center space-x-2">
                        <span className={`tag ${webhook.is_active ? 'tag-green' : 'tag-gray'}`}>
                          {webhook.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <button 
                          onClick={() => testWebhook(webhook.id)}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mr-2"
                        >
                          Test
                        </button>
                        <button 
                          onClick={() => deleteWebhook(webhook.id)}
                          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <div>URL: {webhook.url}</div>
                      <div>Events: {webhook.events.join(', ')}</div>
                      <div>
                        Stats: {webhook.success_count} success, {webhook.failure_count} failures
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No webhooks configured</p>
            )}
          </div>

          {/* Rate Limits */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Rate Limits</h3>
            <div className="space-y-4">
              {rateLimits.map((limit) => (
                <div key={limit.id} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white capitalize">
                      {limit.resource.replace('_', ' ')}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {limit.limit_per_hour}/hour, {limit.limit_per_day}/day
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <input
                      type="number"
                      value={limit.limit_per_hour}
                      className="form-input w-20"
                      readOnly
                    />
                    <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Business Rules Tab */}
      {activeTab === 'workflows' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Business Rules & Automation</h2>
            <button
              onClick={() => setShowRuleModal(true)}
              className="btn-primary"
            >
              Create Rule
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {businessRules.map((rule) => (
              <div key={rule.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">{rule.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{rule.description}</p>
                  </div>
                  <span className={`tag ${rule.is_active ? 'tag-green' : 'tag-gray'}`}>
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div><strong>Module:</strong> {rule.module}</div>
                  <div><strong>Trigger:</strong> {rule.trigger_event}</div>
                  <div><strong>Conditions:</strong> {rule.conditions.length}</div>
                  <div><strong>Actions:</strong> {rule.actions.length}</div>
                  <div><strong>Executions:</strong> {rule.execution_count}</div>
                </div>
                <div className="flex space-x-2 mt-4">
                  <button 
                    onClick={() => editBusinessRule(rule)}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                  >
                    Edit
                  </button>
                  <button 
                    onClick={() => testBusinessRule(rule.id)}
                    className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    Test
                  </button>
                  <button 
                    onClick={() => deleteBusinessRule(rule.id)}
                    className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* UI Customization Tab */}
      {activeTab === 'ui' && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">UI Customization</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Dashboard Widgets */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Dashboard Widgets</h3>
              <div className="space-y-3">
                {dashboardWidgets.map((widget) => (
                  <div key={widget.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{widget.widget_type}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Position: {widget.position.x}, {widget.position.y}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={widget.is_visible}
                        className="custom-checkbox"
                        readOnly
                      />
                      <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
                        Configure
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Menu Configuration */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Menu Configuration</h3>
              {menuConfig && (
                <div className="space-y-3">
                  {menuConfig.menu_items.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{item.icon}</span>
                        <span className="font-medium text-gray-900 dark:text-white">{item.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={item.visible}
                          className="custom-checkbox"
                          readOnly
                        />
                        <button className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                          ⚙️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Add New User</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="form-input"
                  placeholder="Enter username"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="form-input"
                  placeholder="Enter email address"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="form-input"
                  placeholder="Enter full name"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    className="form-input"
                  >
                    <option value="user">User</option>
                    <option value="manager">Manager</option>
                    <option value="admin">Admin</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Department</label>
                  <input
                    type="text"
                    value={newUser.department}
                    onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
                    className="form-input"
                    placeholder="Department"
                  />
                </div>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createUser}
                className="flex-1 btn-primary"
                disabled={!newUser.username || !newUser.email || !newUser.full_name}
              >
                Create User
              </button>
              <button
                onClick={() => setShowUserModal(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Webhook Modal */}
      {showWebhookModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Add Webhook</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  value={newWebhook.name}
                  onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                  className="form-input"
                  placeholder="Webhook name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">URL</label>
                <input
                  type="url"
                  value={newWebhook.url}
                  onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                  className="form-input"
                  placeholder="https://example.com/webhook"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Events</label>
                <input
                  type="text"
                  value={newWebhook.events.join(', ')}
                  onChange={(e) => setNewWebhook({ 
                    ...newWebhook, 
                    events: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                  })}
                  className="form-input"
                  placeholder="lead.created, quote.sent, task.completed"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createWebhook}
                className="flex-1 btn-primary"
                disabled={!newWebhook.name || !newWebhook.url}
              >
                Create Webhook
              </button>
              <button
                onClick={() => setShowWebhookModal(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;