import React, { useState, useEffect } from 'react';

const NetworkMonitoring = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/system-status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/alerts?limit=10`);
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  // Trigger AI analysis
  const triggerAIAnalysis = async () => {
    setAnalysisLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/analyze`, {
        method: 'POST'
      });
      const data = await response.json();
      setLastAnalysis(data);
      await fetchSystemStatus(); // Refresh status after analysis
    } catch (error) {
      console.error('Error triggering AI analysis:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Simulate alert for testing
  const simulateAlert = async (severity = 'medium') => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/simulate-alert?severity=${severity}`, {
        method: 'POST'
      });
      await response.json();
      await fetchAlerts(); // Refresh alerts
    } catch (error) {
      console.error('Error simulating alert:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchSystemStatus(), fetchAlerts()]);
      setLoading(false);
    };

    loadData();

    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchAlerts();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Helper function to get health status color
  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Helper function to get alert severity color
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'low': return 'bg-blue-100 text-blue-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <svg className="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
            Autonomous Network Monitoring Bot
          </h1>
          <p className="text-gray-600">AI-powered system monitoring and self-healing</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={triggerAIAnalysis} 
            disabled={analysisLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
          >
            {analysisLoading ? (
              <svg className="h-4 w-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            )}
            AI Analysis
          </button>
          <button 
            onClick={() => window.location.reload()}
            className="border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* System Status Overview */}
      {systemStatus && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">System Health</p>
                <p className={`text-2xl font-bold ${getHealthColor(systemStatus.overall_health)}`}>
                  {systemStatus.overall_health.charAt(0).toUpperCase() + systemStatus.overall_health.slice(1)}
                </p>
              </div>
              <svg className={`h-8 w-8 ${getHealthColor(systemStatus.overall_health)}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h6a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h6a2 2 0 002-2v-4a2 2 0 00-2-2m8-2V6a2 2 0 012-2h2a2 2 0 012 2v8a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">CPU Usage</p>
                <p className="text-2xl font-bold text-gray-900">{systemStatus.cpu_usage.toFixed(1)}%</p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${systemStatus.cpu_usage}%` }}></div>
                </div>
              </div>
              <svg className="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Memory Usage</p>
                <p className="text-2xl font-bold text-gray-900">{systemStatus.memory_usage.toFixed(1)}%</p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: `${systemStatus.memory_usage}%` }}></div>
                </div>
              </div>
              <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{systemStatus.active_alerts}</p>
                <p className="text-sm text-gray-500">{systemStatus.total_alerts_24h} in 24h</p>
              </div>
              <svg className="h-8 w-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
        </div>
      )}

      {/* Main Tabs */}
      <div className="w-full">
        <div className="grid grid-cols-3 border-b">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 font-medium ${activeTab === 'dashboard' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('alerts')}
            className={`px-4 py-2 font-medium ${activeTab === 'alerts' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Alerts ({alerts.length})
          </button>
          <button 
            onClick={() => setActiveTab('testing')}
            className={`px-4 py-2 font-medium ${activeTab === 'testing' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Testing & Simulation
          </button>
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-4 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* System Metrics */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4">System Metrics</h3>
                {systemStatus && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Disk Usage</span>
                      <span className="font-medium">{systemStatus.disk_usage.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Network Latency</span>
                      <span className="font-medium">{systemStatus.network_latency.toFixed(1)}ms</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>API Response Time</span>
                      <span className="font-medium">{systemStatus.api_response_time.toFixed(1)}ms</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Uptime</span>
                      <span className="font-medium">{(systemStatus.uptime / 24).toFixed(1)} days</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Recent AI Analysis */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4">AI Analysis</h3>
                {lastAnalysis ? (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600">
                      Last Analysis: {new Date(lastAnalysis.timestamp).toLocaleString()}
                    </p>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="text-sm">{lastAnalysis.ai_analysis}</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-gray-500">No recent AI analysis</p>
                    <button 
                      onClick={triggerAIAnalysis} 
                      disabled={analysisLoading}
                      className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                    >
                      Run Analysis
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="space-y-4 mt-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">System Alerts</h3>
              <button onClick={fetchAlerts} className="border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg">
                Refresh
              </button>
            </div>

            <div className="space-y-4">
              {alerts.length === 0 ? (
                <div className="bg-white p-6 rounded-lg shadow border text-center">
                  <svg className="h-8 w-8 text-green-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-gray-500">No active alerts</p>
                </div>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="bg-white p-4 rounded-lg shadow border">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                            {alert.severity.toUpperCase()}
                          </span>
                          <span className="px-2 py-1 text-xs border rounded">
                            {alert.status}
                          </span>
                        </div>
                        <h4 className="font-semibold">{alert.title}</h4>
                        <p className="text-gray-600 text-sm">{alert.description}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(alert.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    {alert.ai_analysis && (
                      <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <div className="text-sm">{alert.ai_analysis}</div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Testing Tab */}
        {activeTab === 'testing' && (
          <div className="space-y-4 mt-6">
            <div className="bg-white p-6 rounded-lg shadow border">
              <h3 className="text-lg font-semibold mb-4">Testing & Simulation</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <button 
                  onClick={() => simulateAlert('low')}
                  className="text-blue-600 border border-blue-600 hover:bg-blue-50 px-4 py-2 rounded-lg"
                >
                  Simulate Low Alert
                </button>
                <button 
                  onClick={() => simulateAlert('medium')}
                  className="text-yellow-600 border border-yellow-600 hover:bg-yellow-50 px-4 py-2 rounded-lg"
                >
                  Simulate Medium Alert
                </button>
                <button 
                  onClick={() => simulateAlert('high')}
                  className="text-orange-600 border border-orange-600 hover:bg-orange-50 px-4 py-2 rounded-lg"
                >
                  Simulate High Alert
                </button>
                <button 
                  onClick={() => simulateAlert('critical')}
                  className="text-red-600 border border-red-600 hover:bg-red-50 px-4 py-2 rounded-lg"
                >
                  Simulate Critical Alert
                </button>
              </div>
              <div className="mt-4 text-sm text-gray-600">
                <p>Use these buttons to simulate different types of alerts for testing the monitoring system.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NetworkMonitoring;