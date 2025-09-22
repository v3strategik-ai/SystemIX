import requests
import sys
import json
from datetime import datetime, timedelta

class SystemIXAPITester:
    def __init__(self, base_url="https://deal-finder-76.preview.emergentagent.com"):
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