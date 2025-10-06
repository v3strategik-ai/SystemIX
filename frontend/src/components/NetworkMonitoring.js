import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Network, 
  Server, 
  Zap,
  Clock,
  TrendingUp,
  Settings,
  RefreshCw,
  Bot
} from 'lucide-react';

const NetworkMonitoring = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [healingActions, setHealingActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

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

  // Fetch metrics
  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/metrics?limit=20`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  // Fetch healing actions
  const fetchHealingActions = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/monitoring/healing-actions?limit=10`);
      const data = await response.json();
      setHealingActions(data);
    } catch (error) {
      console.error('Error fetching healing actions:', error);
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

  // Update alert status
  const updateAlertStatus = async (alertId, status) => {
    try {
      await fetch(`${backendUrl}/api/monitoring/alerts/${alertId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(status)
      });
      await fetchAlerts(); // Refresh alerts
    } catch (error) {
      console.error('Error updating alert status:', error);
    }
  };

  // Execute healing action
  const executeHealingAction = async (alertId, actionType, description) => {
    try {
      await fetch(`${backendUrl}/api/monitoring/healing-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_type: actionType, alert_id: alertId, description })
      });
      await fetchHealingActions(); // Refresh healing actions
      await fetchAlerts(); // Refresh alerts
    } catch (error) {
      console.error('Error executing healing action:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchSystemStatus(),
        fetchAlerts(),
        fetchMetrics(),
        fetchHealingActions()
      ]);
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
            <Bot className="h-8 w-8 text-blue-600" />
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
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Bot className="h-4 w-4" />
            )}
            AI Analysis
          </button>
          <button 
            onClick={() => window.location.reload()}
            className="border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
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
              <Server className={`h-8 w-8 ${getHealthColor(systemStatus.overall_health)}`} />
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
              <Cpu className="h-8 w-8 text-blue-600" />
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
              <MemoryStick className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{systemStatus.active_alerts}</p>
                <p className="text-sm text-gray-500">{systemStatus.total_alerts_24h} in 24h</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-600" />
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
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('alerts')}
            className={`px-4 py-2 font-medium ${activeTab === 'alerts' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Alerts
          </button>
          <button 
            onClick={() => setActiveTab('metrics')}
            className={`px-4 py-2 font-medium ${activeTab === 'metrics' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Metrics
          </button>
          <button 
            onClick={() => setActiveTab('healing')}
            className={`px-4 py-2 font-medium ${activeTab === 'healing' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Self-Healing
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
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-gray-600" />
                      <span>Disk Usage</span>
                    </div>
                    <span className="font-medium">{systemStatus.disk_usage.toFixed(1)}%</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Network className="h-4 w-4 text-gray-600" />
                      <span>Network Latency</span>
                    </div>
                    <span className="font-medium">{systemStatus.network_latency.toFixed(1)}ms</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-gray-600" />
                      <span>API Response Time</span>
                    </div>
                    <span className="font-medium">{systemStatus.api_response_time.toFixed(1)}ms</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-gray-600" />
                      <span>Uptime</span>
                    </div>
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
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
                    <Bot className="h-4 w-4 text-blue-600 mt-1" />
                    <div className="text-sm">{lastAnalysis.ai_analysis}</div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <Bot className="h-8 w-8 text-gray-400 mx-auto mb-2" />
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

          {/* Testing Actions */}
          <div className="bg-white p-6 rounded-lg shadow border">
            <h3 className="text-lg font-semibold mb-4">Testing & Simulation</h3>
            <div className="flex gap-2 flex-wrap">
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
          </div>
        </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">System Alerts</h3>
            <Button onClick={fetchAlerts} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="space-y-4">
            {alerts.length === 0 ? (
              <Card className="p-6 text-center">
                <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="text-gray-500">No active alerts</p>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Card key={alert.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getSeverityColor(alert.severity)}>
                          {alert.severity.toUpperCase()}
                        </Badge>
                        <Badge variant="outline">{alert.status}</Badge>
                      </div>
                      <h4 className="font-semibold">{alert.title}</h4>
                      <p className="text-gray-600 text-sm">{alert.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-2 ml-4">
                      {alert.status === 'active' && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => updateAlertStatus(alert.id, 'acknowledged')}
                          >
                            Acknowledge
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => updateAlertStatus(alert.id, 'resolved')}
                          >
                            Resolve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => executeHealingAction(alert.id, 'restart_service', 'Auto-healing attempt')}
                          >
                            <Zap className="h-4 w-4 mr-1" />
                            Heal
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                  {alert.ai_analysis && (
                    <Alert className="mt-3">
                      <Bot className="h-4 w-4" />
                      <div className="text-sm">{alert.ai_analysis}</div>
                    </Alert>
                  )}
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          <h3 className="text-lg font-semibold">System Metrics History</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {metrics.slice(0, 10).map((metric) => (
              <Card key={metric.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{metric.metric_name}</h4>
                    <p className="text-2xl font-bold text-blue-600">
                      {metric.value} {metric.unit}
                    </p>
                    <p className="text-sm text-gray-500">
                      Source: {metric.source}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {new Date(metric.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Self-Healing Tab */}
        <TabsContent value="healing" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Self-Healing Actions</h3>
            <Button onClick={fetchHealingActions} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="space-y-4">
            {healingActions.length === 0 ? (
              <Card className="p-6 text-center">
                <Zap className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">No healing actions executed yet</p>
              </Card>
            ) : (
              healingActions.map((action) => (
                <Card key={action.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant={action.success ? "default" : "destructive"}>
                          {action.success ? "SUCCESS" : "FAILED"}
                        </Badge>
                        {action.ai_recommended && (
                          <Badge variant="outline">AI Recommended</Badge>
                        )}
                      </div>
                      <h4 className="font-semibold">{action.action_type.replace('_', ' ').toUpperCase()}</h4>
                      <p className="text-gray-600 text-sm">{action.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Executed: {new Date(action.executed_at).toLocaleString()}
                      </p>
                      {action.output && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                          {action.output}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NetworkMonitoring;