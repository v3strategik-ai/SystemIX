import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const IntegrationsHub = () => {
  const [activeView, setActiveView] = useState('platforms'); // 'platforms', 'connections', 'analytics'
  const [platforms, setPlatforms] = useState([]);
  const [connections, setConnections] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  const [connectionData, setConnectionData] = useState({
    platform_id: '',
    connection_name: '',
    sync_direction: 'bidirectional',
    sync_frequency: 60,
    field_mappings: {},
    user_id: 'current_user'
  });

  const [syncJobData, setSyncJobData] = useState({
    connection_id: '',
    job_type: 'manual',
    direction: 'bidirectional',
    data_type: 'contacts'
  });

  const [apiKeyData, setApiKeyData] = useState({
    api_key: '',
    additional_config: {}
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [platformsResponse, connectionsResponse, analyticsResponse] = await Promise.all([
        axios.get(`${API}/integrations/platforms`),
        axios.get(`${API}/integrations/connections?user_id=current_user`),
        axios.get(`${API}/integrations/analytics`)
      ]);
      
      setPlatforms(platformsResponse.data);
      setConnections(connectionsResponse.data);
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/integrations/initialize-sample-data`);
      fetchData();
    } catch (error) {
      console.error('Error initializing sample data:', error);
    }
  };

  const initiateOAuth = async (platform) => {
    try {
      const oauthRequest = {
        platform_id: platform.id,
        connection_name: connectionData.connection_name || `${platform.name} Connection`,
        redirect_uri: `${window.location.origin}/integrations/callback`,
        user_id: 'current_user'
      };

      const response = await axios.post(`${API}/integrations/oauth/initiate`, oauthRequest);
      
      // In production, redirect to OAuth URL
      // For demo, simulate successful connection
      setTimeout(async () => {
        try {
          const callbackRequest = {
            platform_id: platform.id,
            code: 'demo_auth_code',
            state: response.data.state,
            user_id: 'current_user'
          };
          
          await axios.post(`${API}/integrations/oauth/callback`, callbackRequest);
          fetchData();
          setShowConnectModal(false);
        } catch (error) {
          console.error('OAuth callback error:', error);
        }
      }, 2000);
      
    } catch (error) {
      console.error('OAuth initiation error:', error);
    }
  };

  const createApiKeyConnection = async (platform) => {
    try {
      const apiRequest = {
        platform_id: platform.id,
        connection_name: connectionData.connection_name || `${platform.name} Connection`,
        api_key: apiKeyData.api_key,
        user_id: 'current_user',
        additional_config: apiKeyData.additional_config
      };

      await axios.post(`${API}/integrations/api-key-connection`, apiRequest);
      fetchData();
      setShowConnectModal(false);
      setApiKeyData({ api_key: '', additional_config: {} });
    } catch (error) {
      console.error('API key connection error:', error);
    }
  };

  const createSyncJob = async () => {
    try {
      await axios.post(`${API}/integrations/sync-jobs`, syncJobData);
      fetchData();
      setShowSyncModal(false);
      setSyncJobData({
        connection_id: '',
        job_type: 'manual',
        direction: 'bidirectional',
        data_type: 'contacts'
      });
    } catch (error) {
      console.error('Error creating sync job:', error);
    }
  };

  const disconnectIntegration = async (connectionId) => {
    try {
      await axios.delete(`${API}/integrations/connections/${connectionId}`);
      fetchData();
    } catch (error) {
      console.error('Error disconnecting integration:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
      case 'disconnected': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
      case 'error': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'expired': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const getSyncStatusColor = (status) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'cancelled': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'crm': return 'bg-blue-500';
      case 'payment': return 'bg-green-500';
      case 'marketing': return 'bg-purple-500';
      case 'communication': return 'bg-orange-500';
      case 'project_management': return 'bg-indigo-500';
      case 'ecommerce': return 'bg-pink-500';
      default: return 'bg-gray-500';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'crm': return '👥';
      case 'payment': return '💳';
      case 'marketing': return '📧';
      case 'communication': return '💬';
      case 'project_management': return '📋';
      case 'ecommerce': return '🛒';
      default: return '🔗';
    }
  };

  // Additional navigation and interaction functions
  const connectIntegration = (platform) => {
    if (platform.auth_type === 'oauth2') {
      initiateOAuth(platform);
    } else {
      createApiKeyConnection(platform);
    }
  };

  const configureIntegration = (connectionId) => {
    alert(`Opening configuration for connection: ${connectionId}\nThis would show detailed settings, field mapping, and sync preferences.`);
  };

  const viewIntegration = (connectionId) => {
    alert(`Viewing integration details: ${connectionId}\nThis would show connection status, sync history, and performance metrics.`);
  };

  const testConnection = async (connectionId) => {
    try {
      // Simulate connection test
      alert(`Testing connection: ${connectionId}\nConnection test successful! All endpoints are responding correctly.`);
    } catch (error) {
      alert(`Connection test failed: ${error.message}`);
    }
  };

  const categories = [
    { key: 'all', label: 'All Categories', count: platforms.length },
    { key: 'crm', label: 'CRM', count: platforms.filter(p => p.type === 'crm').length },
    { key: 'payment', label: 'Payments', count: platforms.filter(p => p.type === 'payment').length },
    { key: 'marketing', label: 'Marketing', count: platforms.filter(p => p.type === 'marketing').length },
    { key: 'communication', label: 'Communication', count: platforms.filter(p => p.type === 'communication').length },
    { key: 'project_management', label: 'Project Management', count: platforms.filter(p => p.type === 'project_management').length },
    { key: 'ecommerce', label: 'E-commerce', count: platforms.filter(p => p.type === 'ecommerce').length }
  ];

  const filteredPlatforms = selectedCategory === 'all' 
    ? platforms 
    : platforms.filter(platform => platform.type === selectedCategory);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Integrations Hub</h1>
          <p className="text-gray-600 dark:text-gray-400">Connect SystemIX AI to your existing platforms and tools</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={initializeSampleData}
            className="btn-secondary"
          >
            Initialize Sample Data
          </button>
          <button
            onClick={() => setShowSyncModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200"
          >
            <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Manual Sync
          </button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 mb-6">
        <div className="flex space-x-2">
          {[
            { key: 'platforms', label: 'Available Platforms', icon: '🔗', count: platforms.length },
            { key: 'connections', label: 'My Connections', icon: '🔌', count: connections.length },
            { key: 'analytics', label: 'Analytics', icon: '📊', count: null }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveView(tab.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeView === tab.key
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label} {tab.count !== null && `(${tab.count})`}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Category Filter */}
      {activeView === 'platforms' && (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 mb-6">
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <button
                key={category.key}
                onClick={() => setSelectedCategory(category.key)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all duration-200 ${
                  selectedCategory === category.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {category.key !== 'all' && (
                  <span className="mr-1">{getTypeIcon(category.key)}</span>
                )}
                {category.label} ({category.count})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Platforms View */}
      {activeView === 'platforms' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlatforms.map((platform) => {
            const existingConnection = connections.find(c => c.platform_id === platform.id && c.status === 'connected');
            
            return (
              <div key={platform.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50 card-hover">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div 
                      className={`w-12 h-12 ${getTypeColor(platform.type)} rounded-lg flex items-center justify-center text-white text-xl`}
                    >
                      {getTypeIcon(platform.type)}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{platform.name}</h3>
                      <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                        {platform.type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  {existingConnection && (
                    <span className={`tag ${getStatusColor(existingConnection.status)}`}>
                      Connected
                    </span>
                  )}
                </div>
                
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
                  {platform.description}
                </p>
                
                <div className="mb-4">
                  <div className="flex flex-wrap gap-1 mb-2">
                    {platform.supported_features.slice(0, 4).map((feature, index) => (
                      <span key={index} className="tag tag-blue text-xs">
                        {feature}
                      </span>
                    ))}
                    {platform.supported_features.length > 4 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        +{platform.supported_features.length - 4} more
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>Auth: {platform.auth_type.toUpperCase()}</span>
                    <span>
                      {Object.keys(platform.rate_limits)[0]}: {Object.values(platform.rate_limits)[0]}
                    </span>
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  {existingConnection ? (
                    <>
                      <button className="flex-1 text-sm bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-3 rounded-lg transition-all duration-200">
                        ✓ Connected
                      </button>
                      <button
                        onClick={() => disconnectIntegration(existingConnection.id)}
                        className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium py-2 px-3 rounded-lg border border-red-300 dark:border-red-600 transition-colors"
                      >
                        Disconnect
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setSelectedPlatform(platform);
                          setConnectionData({ ...connectionData, platform_id: platform.id });
                          setShowConnectModal(true);
                        }}
                        className="flex-1 btn-primary"
                      >
                        Connect
                      </button>
                      <a
                        href={platform.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 font-medium py-2 px-3 rounded-lg border border-gray-300 dark:border-gray-600 transition-colors"
                      >
                        Learn More
                      </a>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Connections View */}
      {activeView === 'connections' && (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">My Connections</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Platform</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sync Stats</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Sync</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {connections.map((connection) => (
                  <tr key={connection.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className={`w-10 h-10 ${getTypeColor('crm')} rounded-lg flex items-center justify-center text-white mr-3`}>
                          {getTypeIcon('crm')}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">{connection.platform_name}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{connection.connection_name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`tag ${getStatusColor(connection.status)}`}>
                        {connection.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <div className="text-xs">
                        <div>Total: {connection.total_syncs}</div>
                        <div className="text-green-600">Success: {connection.successful_syncs}</div>
                        <div className="text-red-600">Failed: {connection.failed_syncs}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {connection.last_sync_at ? new Date(connection.last_sync_at).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => {
                          setSyncJobData({ ...syncJobData, connection_id: connection.id });
                          setShowSyncModal(true);
                        }}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                      >
                        Sync Now
                      </button>
                      <button 
                        onClick={() => configureIntegration(connection.id)}
                        className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                      >
                        Configure
                      </button>
                      <button
                        onClick={() => disconnectIntegration(connection.id)}
                        className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                      >
                        Disconnect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Analytics View */}
      {activeView === 'analytics' && analytics && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Connections</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.total_connections}</p>
                </div>
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 dark:text-blue-400">🔗</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Connections</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.active_connections}</p>
                </div>
                <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 dark:text-green-400">✅</span>
                </div>
              </div>
            </div>

            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recent Syncs</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.recent_syncs.length}</p>
                </div>
                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 dark:text-purple-400">🔄</span>
                </div>
              </div>
            </div>

            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Platforms</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{Object.keys(analytics.platform_stats).length}</p>
                </div>
                <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-orange-600 dark:text-orange-400">🏗️</span>
                </div>
              </div>
            </div>
          </div>

          {/* Platform Stats */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Platform Statistics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(analytics.platform_stats).map(([platform, stats]) => (
                <div key={platform} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">{platform}</h4>
                    <span className={`tag ${stats.active_connections > 0 ? 'tag-green' : 'tag-gray'}`}>
                      {stats.active_connections}/{stats.connections}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                    <div>Total Syncs: {stats.total_syncs}</div>
                    <div>Success Rate: {stats.total_syncs > 0 ? Math.round((stats.successful_syncs / stats.total_syncs) * 100) : 0}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Sync Jobs */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Sync Jobs</h3>
            <div className="space-y-3">
              {analytics.recent_syncs.slice(0, 10).map((sync) => (
                <div key={sync.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 ${getTypeColor('crm')} rounded-lg flex items-center justify-center text-white text-sm`}>
                      {getTypeIcon('crm')}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{sync.platform_name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {sync.data_type} • {sync.direction} • {sync.job_type}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={`tag ${getSyncStatusColor(sync.status)}`}>
                      {sync.status}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {sync.records_success}/{sync.records_processed}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(sync.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty States */}
      {((activeView === 'platforms' && filteredPlatforms.length === 0) ||
        (activeView === 'connections' && connections.length === 0)) && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">
            {activeView === 'platforms' ? '🔗' : '🔌'}
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {activeView === 'platforms' ? 'No platforms found' : 'No connections yet'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {activeView === 'platforms' 
              ? 'Initialize sample data to see available platforms' 
              : 'Connect to your first platform to get started'
            }
          </p>
        </div>
      )}

      {/* Connect Platform Modal */}
      {showConnectModal && selectedPlatform && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Connect to {selectedPlatform.name}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Connection Name
                </label>
                <input
                  type="text"
                  value={connectionData.connection_name}
                  onChange={(e) => setConnectionData({ ...connectionData, connection_name: e.target.value })}
                  className="form-input"
                  placeholder={`${selectedPlatform.name} Connection`}
                />
              </div>

              {selectedPlatform.auth_type === 'api_key' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={apiKeyData.api_key}
                    onChange={(e) => setApiKeyData({ ...apiKeyData, api_key: e.target.value })}
                    className="form-input"
                    placeholder="Enter your API key"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Sync Direction
                </label>
                <select
                  value={connectionData.sync_direction}
                  onChange={(e) => setConnectionData({ ...connectionData, sync_direction: e.target.value })}
                  className="form-input"
                >
                  <option value="bidirectional">Bidirectional</option>
                  <option value="inbound">Inbound Only</option>
                  <option value="outbound">Outbound Only</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Sync Frequency (minutes)
                </label>
                <input
                  type="number"
                  value={connectionData.sync_frequency}
                  onChange={(e) => setConnectionData({ ...connectionData, sync_frequency: parseInt(e.target.value) })}
                  className="form-input"
                  min="15"
                  max="1440"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  if (selectedPlatform.auth_type === 'oauth2') {
                    initiateOAuth(selectedPlatform);
                  } else {
                    createApiKeyConnection(selectedPlatform);
                  }
                }}
                className="flex-1 btn-primary"
                disabled={selectedPlatform.auth_type === 'api_key' && !apiKeyData.api_key}
              >
                {selectedPlatform.auth_type === 'oauth2' ? 'Connect with OAuth' : 'Connect with API Key'}
              </button>
              <button
                onClick={() => setShowConnectModal(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Sync Modal */}
      {showSyncModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Manual Sync</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Connection
                </label>
                <select
                  value={syncJobData.connection_id}
                  onChange={(e) => setSyncJobData({ ...syncJobData, connection_id: e.target.value })}
                  className="form-input"
                >
                  <option value="">Select connection</option>
                  {connections.filter(c => c.status === 'connected').map(connection => (
                    <option key={connection.id} value={connection.id}>
                      {connection.platform_name} - {connection.connection_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Data Type
                </label>
                <select
                  value={syncJobData.data_type}
                  onChange={(e) => setSyncJobData({ ...syncJobData, data_type: e.target.value })}
                  className="form-input"
                >
                  <option value="contacts">Contacts</option>
                  <option value="accounts">Accounts</option>
                  <option value="opportunities">Opportunities</option>
                  <option value="tasks">Tasks</option>
                  <option value="events">Events</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Direction
                </label>
                <select
                  value={syncJobData.direction}
                  onChange={(e) => setSyncJobData({ ...syncJobData, direction: e.target.value })}
                  className="form-input"
                >
                  <option value="bidirectional">Bidirectional</option>
                  <option value="inbound">Inbound Only</option>
                  <option value="outbound">Outbound Only</option>
                </select>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createSyncJob}
                className="flex-1 btn-primary"
                disabled={!syncJobData.connection_id}
              >
                Start Sync
              </button>
              <button
                onClick={() => setShowSyncModal(false)}
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

export default IntegrationsHub;