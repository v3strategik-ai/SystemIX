import React, { useState, useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const NetworkMonitoringEnhanced = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState(null);
  const [chartData, setChartData] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const wsUrl = backendUrl.replace('http', 'ws') + '/ws/monitoring';
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
        };

        wsRef.current.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          if (message.type === 'system_status') {
            setSystemStatus(message.data);
          } else if (message.type === 'new_alert') {
            setAlerts(prevAlerts => [message.data, ...prevAlerts.slice(0, 9)]);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          setIsConnected(false);
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
        };
      } catch (error) {
        console.error('Error connecting WebSocket:', error);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [backendUrl]);

  // Fetch initial data and chart data
  const fetchInitialData = async () => {
    try {
      await Promise.all([
        fetchSystemStatus(),
        fetchAlerts(),
        fetchChartData()
      ]);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch system status (fallback if WebSocket not connected)
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/system-status`);
      const data = await response.json();
      if (!isConnected) {
        setSystemStatus(data);
      }
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

  // Fetch chart data for real-time charts
  const fetchChartData = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/metrics/chart-data?hours=6`);
      const data = await response.json();
      setChartData(data.chart_data || {});
    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
  };

  // Trigger enhanced AI analysis
  const triggerAIAnalysis = async () => {
    setAnalysisLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/analyze`, {
        method: 'POST'
      });
      const data = await response.json();
      setLastAnalysis(data);
    } catch (error) {
      console.error('Error triggering AI analysis:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Simulate alert for testing
  const simulateAlert = async (severity = 'medium') => {
    try {
      await fetch(`${backendUrl}/api/monitoring/simulate-alert?severity=${severity}`, {
        method: 'POST'
      });
      if (!isConnected) {
        await fetchAlerts(); // Refresh alerts if not using WebSocket
      }
    } catch (error) {
      console.error('Error simulating alert:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchInitialData();

    // Refresh chart data every 30 seconds
    const chartInterval = setInterval(fetchChartData, 30000);

    return () => clearInterval(chartInterval);
  }, []);

  // Chart configuration
  const createChartConfig = (metricName, data, color) => {
    if (!data || !data.labels || !data.data) {
      return null;
    }

    return {
      labels: data.labels,
      datasets: [
        {
          label: metricName,
          data: data.data,
          borderColor: color,
          backgroundColor: color + '20',
          fill: true,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 4,
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#f3f4f6' },
      },
      x: {
        grid: { color: '#f3f4f6' },
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1f2937',
        titleColor: '#f9fafb',
        bodyColor: '#f9fafb',
        borderColor: '#374151',
        borderWidth: 1,
      }
    },
    elements: {
      point: {
        hoverBackgroundColor: '#3b82f6'
      }
    }
  };

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
            {/* Connection status indicator */}
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} title={isConnected ? 'Connected' : 'Disconnected'}></div>
          </h1>
          <p className="text-gray-600">AI-powered real-time system monitoring with predictive analytics</p>
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
            Enhanced AI Analysis
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
        <div className="grid grid-cols-4 border-b">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 font-medium ${activeTab === 'dashboard' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Dashboard & Charts
          </button>
          <button 
            onClick={() => setActiveTab('alerts')}
            className={`px-4 py-2 font-medium ${activeTab === 'alerts' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Alerts ({alerts.length})
          </button>
          <button 
            onClick={() => setActiveTab('ai-insights')}
            className={`px-4 py-2 font-medium ${activeTab === 'ai-insights' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            AI Insights
          </button>
          <button 
            onClick={() => setActiveTab('testing')}
            className={`px-4 py-2 font-medium ${activeTab === 'testing' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Testing & Simulation
          </button>
        </div>

        {/* Dashboard Tab with Real-Time Charts */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6 mt-6">
            {/* Real-Time Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* CPU Usage Chart */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4 text-blue-600">CPU Usage Trend</h3>
                <div style={{ height: '300px' }}>
                  {chartData.cpu_usage && (
                    <Line 
                      data={createChartConfig('CPU Usage (%)', chartData.cpu_usage, '#3b82f6')}
                      options={chartOptions}
                    />
                  )}
                </div>
              </div>

              {/* Memory Usage Chart */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4 text-green-600">Memory Usage Trend</h3>
                <div style={{ height: '300px' }}>
                  {chartData.memory_usage && (
                    <Line 
                      data={createChartConfig('Memory Usage (%)', chartData.memory_usage, '#10b981')}
                      options={chartOptions}
                    />
                  )}
                </div>
              </div>

              {/* Network Latency Chart */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4 text-purple-600">Network Latency</h3>
                <div style={{ height: '300px' }}>
                  {chartData.network_latency && (
                    <Line 
                      data={createChartConfig('Network Latency (ms)', chartData.network_latency, '#8b5cf6')}
                      options={chartOptions}
                    />
                  )}
                </div>
              </div>

              {/* API Response Time Chart */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4 text-orange-600">API Response Time</h3>
                <div style={{ height: '300px' }}>
                  {chartData.api_response_time && (
                    <Line 
                      data={createChartConfig('API Response Time (ms)', chartData.api_response_time, '#f59e0b')}
                      options={chartOptions}
                    />
                  )}
                </div>
              </div>
            </div>

            {/* System Metrics Summary */}
            <div className="bg-white p-6 rounded-lg shadow border">
              <h3 className="text-lg font-semibold mb-4">Current System Metrics</h3>
              {systemStatus && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{systemStatus.disk_usage.toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">Disk Usage</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{systemStatus.network_latency.toFixed(1)}ms</p>
                    <p className="text-sm text-gray-600">Network Latency</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{systemStatus.api_response_time.toFixed(1)}ms</p>
                    <p className="text-sm text-gray-600">API Response</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{(systemStatus.uptime / 24).toFixed(1)}</p>
                    <p className="text-sm text-gray-600">Days Uptime</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{isConnected ? 'Live' : 'Offline'}</p>
                    <p className="text-sm text-gray-600">Data Stream</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Insights Tab */}
        {activeTab === 'ai-insights' && (
          <div className="space-y-6 mt-6">
            <div className="bg-white p-6 rounded-lg shadow border">
              <h3 className="text-lg font-semibold mb-4">Enhanced AI Analysis</h3>
              {lastAnalysis ? (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Last Analysis: {new Date(lastAnalysis.timestamp).toLocaleString()}
                  </p>
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                        {typeof lastAnalysis.ai_analysis === 'string' 
                          ? lastAnalysis.ai_analysis 
                          : JSON.stringify(lastAnalysis.ai_analysis, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No Recent Analysis</h4>
                  <p className="text-gray-600 mb-4">Run an enhanced AI analysis to get predictive insights, pattern recognition, and trend forecasting.</p>
                  <button 
                    onClick={triggerAIAnalysis} 
                    disabled={analysisLoading}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg disabled:opacity-50"
                  >
                    {analysisLoading ? 'Analyzing...' : 'Run Enhanced AI Analysis'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="space-y-4 mt-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">System Alerts</h3>
              <button onClick={fetchAlerts} className="border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg">
                Refresh Alerts
              </button>
            </div>

            <div className="space-y-4">
              {alerts.length === 0 ? (
                <div className="bg-white p-8 rounded-lg shadow border text-center">
                  <svg className="h-12 w-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h4>
                  <p className="text-gray-600">No active alerts. Your system is running smoothly.</p>
                </div>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="bg-white p-6 rounded-lg shadow border">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <span className={`px-3 py-1 text-sm font-medium rounded-full ${getSeverityColor(alert.severity)}`}>
                            {alert.severity.toUpperCase()}
                          </span>
                          <span className="px-3 py-1 text-sm border rounded-full">
                            {alert.status}
                          </span>
                        </div>
                        <h4 className="text-lg font-semibold text-gray-900">{alert.title}</h4>
                        <p className="text-gray-600 mt-1">{alert.description}</p>
                        <p className="text-sm text-gray-500 mt-2">
                          {new Date(alert.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    {alert.ai_analysis && (
                      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h5 className="font-medium text-blue-900 mb-2">AI Analysis</h5>
                        <div className="text-sm text-blue-800">{alert.ai_analysis}</div>
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
              <h3 className="text-lg font-semibold mb-4">Alert Testing & Simulation</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button 
                  onClick={() => simulateAlert('low')}
                  className="text-blue-600 border-2 border-blue-600 hover:bg-blue-50 px-4 py-3 rounded-lg font-medium transition-colors"
                >
                  Simulate Low Alert
                </button>
                <button 
                  onClick={() => simulateAlert('medium')}
                  className="text-yellow-600 border-2 border-yellow-600 hover:bg-yellow-50 px-4 py-3 rounded-lg font-medium transition-colors"
                >
                  Simulate Medium Alert
                </button>
                <button 
                  onClick={() => simulateAlert('high')}
                  className="text-orange-600 border-2 border-orange-600 hover:bg-orange-50 px-4 py-3 rounded-lg font-medium transition-colors"
                >
                  Simulate High Alert
                </button>
                <button 
                  onClick={() => simulateAlert('critical')}
                  className="text-red-600 border-2 border-red-600 hover:bg-red-50 px-4 py-3 rounded-lg font-medium transition-colors"
                >
                  Simulate Critical Alert
                </button>
              </div>
              <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Real-Time Testing Features</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Alerts created instantly appear in the Alerts tab {isConnected && <span className="text-green-600">(Live updates enabled)</span>}</li>
                  <li>• System metrics update automatically every 10 seconds</li>
                  <li>• Charts refresh with new data points continuously</li>
                  <li>• WebSocket connection provides real-time notifications</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NetworkMonitoringEnhanced;