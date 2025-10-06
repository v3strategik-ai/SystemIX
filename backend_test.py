import requests
import sys
import json
from datetime import datetime, timedelta

class SystemIXAPITester:
    def __init__(self, base_url="https://systemix-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })

            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            self.failed_tests.append({'name': name, 'error': 'Timeout'})
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({'name': name, 'error': str(e)})
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        return self.run_test("API Health Check", "GET", "", 200)

    def test_initialize_mock_data(self):
        """Initialize mock data"""
        return self.run_test("Initialize Mock Data", "POST", "initialize-mock-data", 200)

    def test_dashboard_metrics(self):
        """Test dashboard metrics endpoint"""
        return self.run_test("Dashboard Metrics", "GET", "dashboard/metrics", 200)

    def test_dashboard_insights(self):
        """Test AI insights endpoint"""
        return self.run_test("Dashboard AI Insights", "GET", "dashboard/insights", 200)

    def test_leads_endpoints(self):
        """Test lead management endpoints"""
        # Get all leads
        success, leads = self.run_test("Get All Leads", "GET", "leads", 200)
        
        # Create a new lead
        new_lead_data = {
            "name": "Test Lead",
            "email": "test@example.com",
            "company": "Test Company",
            "phone": "+1-555-0199",
            "source": "API Test",
            "notes": "Created during API testing"
        }
        
        create_success, created_lead = self.run_test(
            "Create New Lead", 
            "POST", 
            "leads", 
            200, 
            new_lead_data
        )
        
        # Get specific lead if creation was successful
        if create_success and 'id' in created_lead:
            self.run_test(
                "Get Specific Lead", 
                "GET", 
                f"leads/{created_lead['id']}", 
                200
            )
        
        return success and create_success

    def test_tasks_endpoints(self):
        """Test task management endpoints"""
        # Get all tasks
        success, tasks = self.run_test("Get All Tasks", "GET", "tasks", 200)
        
        # Create a new task
        new_task_data = {
            "title": "Test Task",
            "description": "Created during API testing",
            "priority": "medium",
            "created_by": "api_tester",
            "tags": ["test", "api"]
        }
        
        create_success, created_task = self.run_test(
            "Create New Task", 
            "POST", 
            "tasks", 
            200, 
            new_task_data
        )
        
        return success and create_success

    def test_workflows_endpoints(self):
        """Test workflow automation endpoints"""
        # Get all workflows
        success, workflows = self.run_test("Get All Workflows", "GET", "workflows", 200)
        
        # Create a new workflow
        new_workflow_data = {
            "name": "Test Workflow",
            "description": "Created during API testing",
            "steps": [
                {"name": "Step 1", "action": "test_action"},
                {"name": "Step 2", "action": "another_action"}
            ],
            "created_by": "api_tester"
        }
        
        create_success, created_workflow = self.run_test(
            "Create New Workflow", 
            "POST", 
            "workflows", 
            200, 
            new_workflow_data
        )
        
        # Test workflow execution if creation was successful
        if create_success and 'id' in created_workflow:
            self.run_test(
                "Execute Workflow", 
                "POST", 
                f"workflows/{created_workflow['id']}/execute", 
                200
            )
        
        return success and create_success

    def test_team_endpoints(self):
        """Test team management endpoints"""
        # Get all team members
        success, team = self.run_test("Get All Team Members", "GET", "team", 200)
        
        # Create a new team member
        new_member_data = {
            "name": "Test Member",
            "email": "testmember@systemix.ai",
            "role": "Test Role",
            "department": "Testing"
        }
        
        create_success, created_member = self.run_test(
            "Create New Team Member", 
            "POST", 
            "team", 
            200, 
            new_member_data
        )
        
        return success and create_success

    def test_calendar_endpoints(self):
        """Test calendar endpoints"""
        # Get all calendar events
        success, events = self.run_test("Get Calendar Events", "GET", "calendar/events", 200)
        
        # Create a new calendar event
        tomorrow = datetime.utcnow() + timedelta(days=1)
        new_event_data = {
            "title": "Test Event",
            "description": "Created during API testing",
            "start_time": tomorrow.replace(hour=10).isoformat(),
            "end_time": tomorrow.replace(hour=11).isoformat(),
            "created_by": "api_tester",
            "attendees": ["test@example.com"]
        }
        
        create_success, created_event = self.run_test(
            "Create Calendar Event", 
            "POST", 
            "calendar/events", 
            200, 
            new_event_data
        )
        
        return success and create_success

    def test_ai_chat(self):
        """Test AI chat functionality"""
        chat_data = {
            "message": "Hello SIXA, can you help me with lead management?",
            "session_id": "test_session_123",
            "user_id": "api_tester"
        }
        
        return self.run_test("AI Chat Message", "POST", "chat/message", 200, chat_data, timeout=60)

    def test_quoting_endpoints(self):
        """Test comprehensive quoting functionality"""
        print("\n💰 Running Quoting Tool Tests...")
        
        # 1. Initialize sample data
        init_success, _ = self.run_test(
            "Initialize Quote Sample Data", 
            "POST", 
            "quotes/initialize-sample-data", 
            200
        )
        
        # 2. Get products/services
        products_success, products = self.run_test(
            "Get Products/Services", 
            "GET", 
            "products-services", 
            200
        )
        
        # 3. Get quotes analytics summary
        analytics_success, analytics = self.run_test(
            "Get Quotes Analytics Summary", 
            "GET", 
            "quotes/analytics/summary", 
            200
        )
        
        # 4. Get all quotes
        quotes_success, quotes = self.run_test(
            "Get All Quotes", 
            "GET", 
            "quotes", 
            200
        )
        
        # 5. Create a new quote (if we have products)
        create_success = False
        created_quote = {}
        
        if products_success and products and len(products) > 0:
            # Use first product for line item
            first_product = products[0]
            
            new_quote_data = {
                "title": "Test Quote - API Testing",
                "customer_name": "Test Customer",
                "customer_email": "testcustomer@example.com",
                "customer_phone": "+1-555-0199",
                "customer_address": {
                    "street": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "zip": "12345"
                },
                "line_items": [
                    {
                        "product_service_id": first_product["id"],
                        "quantity": 2.0,
                        "discount_percentage": 10.0,
                        "pricing_tier": "standard"
                    }
                ],
                "tax_settings": {
                    "tax_rate": 8.5,
                    "tax_name": "Sales Tax"
                },
                "notes": "This is a test quote created via API",
                "terms_conditions": "Standard terms and conditions apply",
                "expires_in_days": 30,
                "e_signature_required": True,
                "created_by": "api_tester"
            }
            
            create_success, created_quote = self.run_test(
                "Create New Quote", 
                "POST", 
                "quotes", 
                200, 
                new_quote_data
            )
            
            # 6. Get specific quote if creation was successful
            if create_success and 'id' in created_quote:
                self.run_test(
                    "Get Specific Quote", 
                    "GET", 
                    f"quotes/{created_quote['id']}", 
                    200
                )
                
                # 7. Send the quote
                self.run_test(
                    "Send Quote", 
                    "POST", 
                    f"quotes/{created_quote['id']}/send", 
                    200
                )
                
                # 8. Get quote analytics
                self.run_test(
                    "Get Quote Analytics", 
                    "GET", 
                    f"quotes/{created_quote['id']}/analytics", 
                    200
                )
        
        return (init_success and products_success and analytics_success and 
                quotes_success and create_success)

    def test_document_center_endpoints(self):
        """Test comprehensive Document Center functionality"""
        print("\n📄 Running Document Center Tests...")
        
        # 1. Initialize sample document data
        init_success, _ = self.run_test(
            "Initialize Document Sample Data", 
            "POST", 
            "documents/initialize-sample-data", 
            200
        )
        
        # 2. Get document categories
        categories_success, categories = self.run_test(
            "Get Document Categories", 
            "GET", 
            "document-categories", 
            200
        )
        
        # 3. Get document templates
        templates_success, templates = self.run_test(
            "Get Document Templates", 
            "GET", 
            "document-templates", 
            200
        )
        
        # 4. Get documents
        documents_success, documents = self.run_test(
            "Get Documents", 
            "GET", 
            "documents", 
            200
        )
        
        # 5. Create a new document category
        new_category_data = {
            "name": "Test Category",
            "description": "Created during API testing",
            "color": "#FF5722",
            "icon": "🧪",
            "created_by": "api_tester"
        }
        
        create_category_success, created_category = self.run_test(
            "Create Document Category", 
            "POST", 
            "document-categories", 
            200, 
            new_category_data
        )
        
        # 6. Create a new document template
        template_success = False
        created_template = {}
        
        if create_category_success and 'id' in created_category:
            new_template_data = {
                "title": "Test Template",
                "description": "Created during API testing",
                "type": "custom",
                "category_id": created_category["id"],
                "content": "<h1>Test Template</h1><p>Hello {{customer_name}}, this is a test template created on {{date}}.</p>",
                "variables": ["customer_name", "date"],
                "file_format": "pdf",
                "access_level": "team",
                "created_by": "api_tester",
                "tags": ["test", "api", "template"]
            }
            
            template_success, created_template = self.run_test(
                "Create Document Template", 
                "POST", 
                "document-templates", 
                200, 
                new_template_data
            )
        
        # 7. Create a new document
        document_success = False
        created_document = {}
        
        if template_success and 'id' in created_template:
            new_document_data = {
                "title": "Test Document from Template",
                "description": "Created during API testing using template",
                "template_id": created_template["id"],
                "type": "custom",
                "category_id": created_category["id"],
                "content": "<h1>Test Document</h1><p>This is a test document created via API.</p>",
                "file_format": "pdf",
                "access_level": "private",
                "signature_required": True,
                "signers": [
                    {"name": "Test Signer", "email": "signer@example.com", "role": "signer"}
                ],
                "created_by": "api_tester",
                "tags": ["test", "api", "document"]
            }
            
            document_success, created_document = self.run_test(
                "Create Document from Template", 
                "POST", 
                "documents", 
                200, 
                new_document_data
            )
        
        # 8. Get specific template if creation was successful
        if template_success and 'id' in created_template:
            self.run_test(
                "Get Specific Template", 
                "GET", 
                f"document-templates/{created_template['id']}", 
                200
            )
        
        # 9. Get specific document if creation was successful
        if document_success and 'id' in created_document:
            self.run_test(
                "Get Specific Document", 
                "GET", 
                f"documents/{created_document['id']}", 
                200
            )
        
        # 10. Test file conversion
        import base64
        test_html_content = "<html><body><h1>Test HTML</h1><p>This is a test HTML document for conversion.</p></body></html>"
        encoded_content = base64.b64encode(test_html_content.encode()).decode()
        
        conversion_data = {
            "file_content": encoded_content,
            "source_format": "html",
            "target_format": "pdf",
            "document_title": "test_conversion"
        }
        
        conversion_success, conversion_result = self.run_test(
            "Convert HTML to PDF", 
            "POST", 
            "documents/convert", 
            200, 
            conversion_data
        )
        
        # 11. Test DocuSign integration (send for signature)
        docusign_success = False
        if document_success and 'id' in created_document:
            docusign_data = {
                "document_id": created_document["id"],
                "signers": [
                    {"name": "Test Signer", "email": "signer@example.com", "role": "signer"}
                ],
                "email_subject": "Please sign this test document",
                "email_message": "This is a test document sent via API for signature.",
                "send_reminders": True
            }
            
            docusign_success, docusign_result = self.run_test(
                "Send Document for Signature", 
                "POST", 
                f"documents/{created_document['id']}/send-for-signature", 
                200, 
                docusign_data
            )
            
            # 12. Check signature status
            if docusign_success:
                self.run_test(
                    "Get Document Signature Status", 
                    "GET", 
                    f"documents/{created_document['id']}/signature-status", 
                    200
                )
        
        # 13. Test filtered queries
        if categories_success and categories and len(categories) > 0:
            first_category = categories[0]
            self.run_test(
                "Get Templates by Category", 
                "GET", 
                f"document-templates?category_id={first_category['id']}", 
                200
            )
            
            self.run_test(
                "Get Documents by Category", 
                "GET", 
                f"documents?category_id={first_category['id']}", 
                200
            )
        
        return (init_success and categories_success and templates_success and 
                documents_success and create_category_success and template_success and 
                document_success and conversion_success and docusign_success)

    def test_monitoring_endpoints(self):
        """Test comprehensive Network Monitoring Bot functionality"""
        print("\n🔍 Running Network Monitoring Bot Tests...")
        
        # 1. Test System Status API
        status_success, status_data = self.run_test(
            "Get System Status", 
            "GET", 
            "monitoring/system-status", 
            200
        )
        
        # Validate system status response structure
        if status_success and status_data:
            required_fields = ['overall_health', 'cpu_usage', 'memory_usage', 'disk_usage', 
                             'network_latency', 'api_response_time', 'active_alerts', 
                             'total_alerts_24h', 'last_check', 'uptime']
            missing_fields = [field for field in required_fields if field not in status_data]
            if missing_fields:
                print(f"   ⚠️ Missing fields in system status: {missing_fields}")
            else:
                print(f"   ✅ System health: {status_data.get('overall_health')}")
                print(f"   📊 CPU: {status_data.get('cpu_usage'):.1f}%, Memory: {status_data.get('memory_usage'):.1f}%")
        
        # 2. Test Monitoring Metrics API - GET
        metrics_get_success, metrics_data = self.run_test(
            "Get Monitoring Metrics", 
            "GET", 
            "monitoring/metrics?limit=10", 
            200
        )
        
        # 3. Test Monitoring Metrics API - POST (Create new metric)
        new_metric_data = {
            "metric_name": "test_cpu_usage",
            "value": 75.5,
            "unit": "percentage",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "api_test",
            "metadata": {
                "test_run": True,
                "environment": "testing"
            }
        }
        
        metrics_post_success, metrics_post_result = self.run_test(
            "Create Monitoring Metric", 
            "POST", 
            "monitoring/metrics", 
            200, 
            new_metric_data
        )
        
        # 4. Test Alerts Management APIs - GET all alerts
        alerts_get_success, alerts_data = self.run_test(
            "Get All System Alerts", 
            "GET", 
            "monitoring/alerts?limit=20", 
            200
        )
        
        # 5. Test Alerts Management APIs - GET filtered alerts
        active_alerts_success, active_alerts_data = self.run_test(
            "Get Active Alerts", 
            "GET", 
            "monitoring/alerts?status=active&limit=10", 
            200
        )
        
        # 6. Test Alert Creation
        new_alert_data = {
            "title": "Test Alert - API Testing",
            "description": "This is a test alert created during API testing to verify alert management functionality",
            "severity": "medium",
            "status": "active",
            "source": "api_test",
            "metric_data": {
                "cpu_usage": 85.2,
                "memory_usage": 78.9,
                "trigger_threshold": 80.0
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "auto_healing_attempted": False,
            "healing_actions": []
        }
        
        alert_create_success, created_alert = self.run_test(
            "Create System Alert", 
            "POST", 
            "monitoring/alerts", 
            200, 
            new_alert_data
        )
        
        # 7. Test Alert Status Update (if alert was created successfully)
        alert_update_success = False
        if alert_create_success and created_alert and 'id' in created_alert:
            alert_update_success, update_result = self.run_test(
                "Update Alert Status to Acknowledged", 
                "PUT", 
                f"monitoring/alerts/{created_alert['id']}/status", 
                200, 
                "acknowledged"
            )
            
            # Test resolving the alert
            if alert_update_success:
                self.run_test(
                    "Update Alert Status to Resolved", 
                    "PUT", 
                    f"monitoring/alerts/{created_alert['id']}/status", 
                    200, 
                    "resolved"
                )
        
        # 8. Test AI Analysis API
        ai_analysis_success, ai_analysis_result = self.run_test(
            "Trigger AI System Analysis", 
            "POST", 
            "monitoring/analyze", 
            200,
            timeout=60  # AI analysis might take longer
        )
        
        # Validate AI analysis response
        if ai_analysis_success and ai_analysis_result:
            required_ai_fields = ['message', 'current_metrics', 'ai_analysis', 'timestamp']
            missing_ai_fields = [field for field in required_ai_fields if field not in ai_analysis_result]
            if missing_ai_fields:
                print(f"   ⚠️ Missing fields in AI analysis: {missing_ai_fields}")
            else:
                print(f"   🤖 AI Analysis completed successfully")
                if 'ai_analysis' in ai_analysis_result:
                    analysis_text = ai_analysis_result['ai_analysis'][:100] + "..." if len(ai_analysis_result['ai_analysis']) > 100 else ai_analysis_result['ai_analysis']
                    print(f"   📝 Analysis preview: {analysis_text}")
        
        # 9. Test Alert Simulation API - Different severity levels
        simulation_results = []
        severity_levels = ["low", "medium", "high", "critical"]
        
        for severity in severity_levels:
            simulate_success, simulate_result = self.run_test(
                f"Simulate {severity.title()} Alert", 
                "POST", 
                f"monitoring/simulate-alert?severity={severity}", 
                200
            )
            simulation_results.append(simulate_success)
            
            if simulate_success and simulate_result:
                print(f"   🚨 {severity.title()} alert simulated: {simulate_result.get('message', 'Success')}")
        
        # 10. Test Healing Actions API - Execute healing action
        healing_success = False
        if alert_create_success and created_alert and 'id' in created_alert:
            healing_actions = ["restart_service", "clear_cache", "scale_resources"]
            
            for action in healing_actions:
                action_success, action_result = self.run_test(
                    f"Execute Healing Action: {action}", 
                    "POST", 
                    f"monitoring/healing-action?action_type={action}&alert_id={created_alert['id']}&description=API test healing action for {action}", 
                    200
                )
                
                if action_success:
                    healing_success = True
                    print(f"   🔧 Healing action '{action}' executed successfully")
                    break
        
        # 11. Test Get Healing Actions
        healing_history_success, healing_history = self.run_test(
            "Get Healing Actions History", 
            "GET", 
            "monitoring/healing-actions?limit=10", 
            200
        )
        
        # 12. Test comprehensive monitoring workflow
        workflow_success = True
        if status_success and metrics_get_success and alerts_get_success and ai_analysis_success:
            print("   ✅ Core monitoring workflow functional")
        else:
            workflow_success = False
            print("   ❌ Core monitoring workflow has issues")
        
        # Calculate overall success rate for monitoring
        monitoring_tests = [
            status_success, metrics_get_success, metrics_post_success,
            alerts_get_success, active_alerts_success, alert_create_success,
            ai_analysis_success, healing_history_success
        ]
        
        # Add simulation results
        monitoring_tests.extend(simulation_results)
        
        if healing_success:
            monitoring_tests.append(healing_success)
        
        successful_tests = sum(monitoring_tests)
        total_tests = len(monitoring_tests)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"   📊 Monitoring Tests: {successful_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        return workflow_success and success_rate >= 70

    def test_integrations_hub_endpoints(self):
        """Test comprehensive Integrations Hub functionality"""
        print("\n🔗 Running Integrations Hub Tests...")
        
        # 1. Initialize sample integration data
        init_success, _ = self.run_test(
            "Initialize Integration Sample Data", 
            "POST", 
            "integrations/initialize-sample-data", 
            200
        )
        
        # 2. Get available platforms
        platforms_success, platforms = self.run_test(
            "Get Available Platforms", 
            "GET", 
            "integrations/platforms", 
            200
        )
        
        # 3. Get user connections
        connections_success, connections = self.run_test(
            "Get User Connections", 
            "GET", 
            "integrations/connections", 
            200
        )
        
        # 4. Get integration analytics
        analytics_success, analytics = self.run_test(
            "Get Integration Analytics", 
            "GET", 
            "integrations/analytics", 
            200
        )
        
        # 5. Test OAuth initiation (if we have platforms)
        oauth_init_success = False
        oauth_callback_success = False
        
        if platforms_success and platforms and len(platforms) > 0:
            # Find an OAuth2 platform
            oauth_platform = None
            for platform in platforms:
                if platform.get('auth_type') == 'oauth2':
                    oauth_platform = platform
                    break
            
            if oauth_platform:
                oauth_init_data = {
                    "platform_id": oauth_platform["id"],
                    "connection_name": "Test OAuth Connection",
                    "redirect_uri": "https://systemix-hub.preview.emergentagent.com/integrations/callback",
                    "user_id": "api_tester"
                }
                
                oauth_init_success, oauth_init_result = self.run_test(
                    "Initiate OAuth Flow", 
                    "POST", 
                    "integrations/oauth/initiate", 
                    200, 
                    oauth_init_data
                )
                
                # 6. Test OAuth callback (simulated)
                if oauth_init_success:
                    oauth_callback_data = {
                        "platform_id": oauth_platform["id"],
                        "code": "test_auth_code_12345",
                        "state": oauth_init_result.get("state", "test_state"),
                        "user_id": "api_tester"
                    }
                    
                    oauth_callback_success, oauth_callback_result = self.run_test(
                        "OAuth Callback Handling", 
                        "POST", 
                        "integrations/oauth/callback", 
                        200, 
                        oauth_callback_data
                    )
        
        # 7. Test API Key connection (if we have API key platforms)
        api_key_success = False
        created_connection = {}
        
        if platforms_success and platforms and len(platforms) > 0:
            # Find an API key platform
            api_key_platform = None
            for platform in platforms:
                if platform.get('auth_type') == 'api_key':
                    api_key_platform = platform
                    break
            
            if api_key_platform:
                api_key_data = {
                    "platform_id": api_key_platform["id"],
                    "connection_name": "Test API Key Connection",
                    "api_key": "test_api_key_12345",
                    "user_id": "api_tester",
                    "additional_config": {
                        "endpoint": "https://api.example.com",
                        "version": "v1"
                    }
                }
                
                api_key_success, created_connection = self.run_test(
                    "Create API Key Connection", 
                    "POST", 
                    "integrations/api-key-connection", 
                    200, 
                    api_key_data
                )
        
        # 8. Test sync job creation (if we have a connection)
        sync_job_success = False
        created_sync_job = {}
        
        if api_key_success and 'id' in created_connection:
            sync_job_data = {
                "connection_id": created_connection["id"],
                "job_type": "manual",
                "direction": "bidirectional",
                "data_type": "contacts"
            }
            
            sync_job_success, created_sync_job = self.run_test(
                "Create Manual Sync Job", 
                "POST", 
                "integrations/sync-jobs", 
                200, 
                sync_job_data
            )
        
        # 9. Test connection disconnect (if we have a connection)
        disconnect_success = False
        if api_key_success and 'id' in created_connection:
            disconnect_success, disconnect_result = self.run_test(
                "Disconnect Integration", 
                "DELETE", 
                f"integrations/connections/{created_connection['id']}", 
                200
            )
        
        # 10. Test filtered platform queries
        if platforms_success:
            # Test filtering by type
            self.run_test(
                "Get CRM Platforms", 
                "GET", 
                "integrations/platforms?type=crm", 
                200
            )
            
            self.run_test(
                "Get Payment Platforms", 
                "GET", 
                "integrations/platforms?type=payment", 
                200
            )
            
            self.run_test(
                "Get Marketing Platforms", 
                "GET", 
                "integrations/platforms?type=marketing", 
                200
            )
        
        # 11. Test connection filtering
        if connections_success:
            self.run_test(
                "Get Active Connections", 
                "GET", 
                "integrations/connections?status=connected", 
                200
            )
        
        # 12. Test analytics with date range
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        self.run_test(
            "Get Analytics with Date Range", 
            "GET", 
            f"integrations/analytics?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}", 
            200
        )
        
        return (init_success and platforms_success and connections_success and 
                analytics_success and (oauth_init_success or api_key_success) and 
                sync_job_success)

def main():
    print("🚀 Starting SystemIX AI Platinum Suite API Tests")
    print("=" * 60)
    
    tester = SystemIXAPITester()
    
    # Run all tests
    print("\n📋 Running Basic API Tests...")
    tester.test_health_check()
    tester.test_initialize_mock_data()
    
    print("\n📊 Running Dashboard Tests...")
    tester.test_dashboard_metrics()
    tester.test_dashboard_insights()
    
    print("\n👥 Running Lead Management Tests...")
    tester.test_leads_endpoints()
    
    print("\n📝 Running Task Management Tests...")
    tester.test_tasks_endpoints()
    
    print("\n⚙️ Running Workflow Tests...")
    tester.test_workflows_endpoints()
    
    print("\n👨‍💼 Running Team Management Tests...")
    tester.test_team_endpoints()
    
    print("\n📅 Running Calendar Tests...")
    tester.test_calendar_endpoints()
    
    print("\n🤖 Running AI Chat Tests...")
    tester.test_ai_chat()
    
    print("\n💰 Running Quoting Tool Tests...")
    tester.test_quoting_endpoints()
    
    print("\n📄 Running Document Center Tests...")
    tester.test_document_center_endpoints()
    
    print("\n🔍 Running Network Monitoring Bot Tests...")
    tester.test_monitoring_endpoints()
    
    print("\n🔗 Running Integrations Hub Tests...")
    tester.test_integrations_hub_endpoints()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests failed: {len(tester.failed_tests)}")
    
    if tester.failed_tests:
        print("\n🔍 FAILED TESTS DETAILS:")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"\n{i}. {failure['name']}")
            if 'expected' in failure:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
                print(f"   Response: {failure['response']}")
            else:
                print(f"   Error: {failure['error']}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 API testing completed successfully!")
        return 0
    else:
        print("⚠️ API testing completed with significant failures!")
        return 1

if __name__ == "__main__":
    sys.exit(main())