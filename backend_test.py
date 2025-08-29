#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for QuickLiqi
Tests all endpoints including settings, deals, health check, financial calculations, and SERPAPI integration.
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://dom-finder.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class QuickLiqiAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_deal_ids = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_health_check(self):
        """Test the health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['status', 'timestamp', 'serpapi_enabled', 'database']
                
                if all(field in data for field in expected_fields):
                    if data['status'] == 'healthy' and data['database'] == 'connected':
                        self.log_test("Health Check", True, f"Status: {data['status']}, SERPAPI: {data['serpapi_enabled']}")
                        return True
                    else:
                        self.log_test("Health Check", False, f"Unhealthy status or database issue: {data}")
                        return False
                else:
                    self.log_test("Health Check", False, f"Missing expected fields in response: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_settings_get(self):
        """Test GET settings endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/settings", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = [
                    'min_coc_pct', 'min_dscr', 'min_monthly_cf', 'max_rehab',
                    'max_down_payment_pct', 'max_interest_rate', 'term_years',
                    'arv_discount_pct', 'refi_ltv_pct', 'vacancy_pct',
                    'mgmt_pct', 'maintenance_pct', 'other_expense_pct', 'rent_input_mode'
                ]
                
                if all(field in data for field in expected_fields):
                    self.log_test("Settings GET", True, f"Retrieved settings with {len(data)} fields")
                    return data
                else:
                    missing = [f for f in expected_fields if f not in data]
                    self.log_test("Settings GET", False, f"Missing fields: {missing}")
                    return None
            else:
                self.log_test("Settings GET", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Settings GET", False, f"Exception: {str(e)}")
            return None
    
    def test_settings_update(self):
        """Test PUT settings endpoint"""
        try:
            # First get current settings
            current_settings = self.test_settings_get()
            if not current_settings:
                return False
            
            # Update some settings
            update_data = {
                "min_coc_pct": 15.0,
                "min_dscr": 1.30,
                "min_monthly_cf": 300.0
            }
            
            response = self.session.put(
                f"{API_BASE}/settings",
                json=update_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify updates were applied
                if (data['min_coc_pct'] == 15.0 and 
                    data['min_dscr'] == 1.30 and 
                    data['min_monthly_cf'] == 300.0):
                    self.log_test("Settings PUT", True, "Settings updated successfully")
                    
                    # Restore original settings
                    restore_response = self.session.put(
                        f"{API_BASE}/settings",
                        json=current_settings,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    return True
                else:
                    self.log_test("Settings PUT", False, f"Settings not updated correctly: {data}")
                    return False
            else:
                self.log_test("Settings PUT", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Settings PUT", False, f"Exception: {str(e)}")
            return False
    
    def test_deals_get_empty(self):
        """Test GET deals endpoint (should handle empty state)"""
        try:
            response = self.session.get(f"{API_BASE}/deals", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Deals GET (empty)", True, f"Retrieved {len(data)} deals")
                    return data
                else:
                    self.log_test("Deals GET (empty)", False, f"Expected list, got: {type(data)}")
                    return None
            else:
                self.log_test("Deals GET (empty)", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Deals GET (empty)", False, f"Exception: {str(e)}")
            return None
    
    def test_deal_create(self):
        """Test POST deals endpoint with realistic data"""
        try:
            deal_data = {
                "address": "1234 Investment Ave",
                "city": "Atlanta",
                "state": "GA",
                "zip": "30309",
                "list_price": 185000,
                "days_on_market": 145,
                "property_type": "SFR",
                "beds": 3,
                "baths": 2.0,
                "sqft": 1250,
                "year_built": 1985,
                "listing_agent_name": "Sarah Johnson",
                "listing_agent_phone": "(404) 555-0123",
                "arv_estimate": 240000,
                "repair_estimate": 25000,
                "monthly_rent": 1800,
                "taxes_insurance_monthly": 350,
                "assignment_fee": 5000,
                "financing_pref": "any",
                "notes": "Test property for API validation"
            }
            
            response = self.session.post(
                f"{API_BASE}/deals",
                json=deal_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields are present
                required_fields = ['id', 'address', 'city', 'state', 'list_price', 'status', 'created_at']
                calculated_fields = ['mao_cash', 'mao_creative', 'noi_monthly', 'cash_flow_monthly', 'coc_pct', 'dscr', 'deal_signal']
                
                if all(field in data for field in required_fields + calculated_fields):
                    self.created_deal_ids.append(data['id'])
                    
                    # Verify financial calculations
                    calculations_valid = (
                        isinstance(data['mao_cash'], (int, float)) and
                        isinstance(data['coc_pct'], (int, float)) and
                        isinstance(data['dscr'], (int, float)) and
                        data['deal_signal'] in ['Green', 'Red']
                    )
                    
                    if calculations_valid:
                        self.log_test("Deal CREATE", True, 
                                    f"Created deal {data['id'][:8]}... with signal: {data['deal_signal']}, CoC: {data['coc_pct']}%")
                        return data
                    else:
                        self.log_test("Deal CREATE", False, "Financial calculations invalid")
                        return None
                else:
                    missing = [f for f in required_fields + calculated_fields if f not in data]
                    self.log_test("Deal CREATE", False, f"Missing fields: {missing}")
                    return None
            else:
                self.log_test("Deal CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Deal CREATE", False, f"Exception: {str(e)}")
            return None
    
    def test_deal_get_by_id(self, deal_id: str):
        """Test GET specific deal by ID"""
        try:
            response = self.session.get(f"{API_BASE}/deals/{deal_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['id'] == deal_id:
                    self.log_test("Deal GET by ID", True, f"Retrieved deal {deal_id[:8]}...")
                    return data
                else:
                    self.log_test("Deal GET by ID", False, f"ID mismatch: expected {deal_id}, got {data.get('id')}")
                    return None
            elif response.status_code == 404:
                self.log_test("Deal GET by ID", False, f"Deal not found: {deal_id}")
                return None
            else:
                self.log_test("Deal GET by ID", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Deal GET by ID", False, f"Exception: {str(e)}")
            return None
    
    def test_deal_update(self, deal_id: str):
        """Test PUT deal update endpoint"""
        try:
            update_data = {
                "arv_estimate": 260000,
                "repair_estimate": 30000,
                "monthly_rent": 1950,
                "notes": "Updated test property with new estimates"
            }
            
            response = self.session.put(
                f"{API_BASE}/deals/{deal_id}",
                json=update_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify updates were applied and metrics recalculated
                if (data['arv_estimate'] == 260000 and 
                    data['repair_estimate'] == 30000 and
                    data['monthly_rent'] == 1950):
                    self.log_test("Deal UPDATE", True, 
                                f"Updated deal {deal_id[:8]}... - new CoC: {data['coc_pct']}%")
                    return data
                else:
                    self.log_test("Deal UPDATE", False, "Updates not applied correctly")
                    return None
            elif response.status_code == 404:
                self.log_test("Deal UPDATE", False, f"Deal not found: {deal_id}")
                return None
            else:
                self.log_test("Deal UPDATE", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Deal UPDATE", False, f"Exception: {str(e)}")
            return None
    
    def test_deal_status_update(self, deal_id: str):
        """Test PATCH deal status endpoint"""
        try:
            status_data = {"status": "Analyzing"}
            
            response = self.session.patch(
                f"{API_BASE}/deals/{deal_id}/status",
                json=status_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == "Analyzing":
                    self.log_test("Deal STATUS Update", True, f"Status updated to: {data['status']}")
                    return data
                else:
                    self.log_test("Deal STATUS Update", False, f"Status not updated: {data['status']}")
                    return None
            elif response.status_code == 404:
                self.log_test("Deal STATUS Update", False, f"Deal not found: {deal_id}")
                return None
            else:
                self.log_test("Deal STATUS Update", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Deal STATUS Update", False, f"Exception: {str(e)}")
            return None
    
    def test_financial_calculations(self):
        """Test financial calculation accuracy with known inputs"""
        try:
            # Create a deal with specific inputs for calculation verification
            test_deal = {
                "address": "999 Calculation Test St",
                "city": "Test City",
                "state": "TX",
                "list_price": 100000,
                "days_on_market": 120,
                "property_type": "SFR",
                "beds": 3,
                "baths": 2.0,
                "sqft": 1000,
                "arv_estimate": 130000,  # 30% above list
                "repair_estimate": 20000,
                "monthly_rent": 1200,
                "taxes_insurance_monthly": 200,
                "assignment_fee": 5000,
                "financing_pref": "cash"
            }
            
            response = self.session.post(
                f"{API_BASE}/deals",
                json=test_deal,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.created_deal_ids.append(data['id'])
                
                # Verify calculations with expected values
                # MAO Cash = ARV * 0.70 - repairs - fee = 130000 * 0.70 - 20000 - 5000 = 66000
                expected_mao_cash = 130000 * 0.70 - 20000 - 5000  # 66000
                
                # NOI = Rent - Operating Expenses
                # OpEx = taxes_insurance + (rent * (vacancy + mgmt + maintenance) / 100)
                # Using default settings: vacancy=5%, mgmt=8%, maintenance=5% = 18%
                expected_opex = 200 + (1200 * 0.18)  # 200 + 216 = 416
                expected_noi = 1200 - expected_opex  # 784
                
                # For cash deal: Cash Flow = NOI, CoC = (NOI * 12) / total_cash_in * 100
                total_cash_in = 100000 + 20000 + 5000  # 125000
                expected_coc = (expected_noi * 12) / total_cash_in * 100
                
                # Allow for rounding differences
                mao_diff = abs(data['mao_cash'] - expected_mao_cash)
                noi_diff = abs(data['noi_monthly'] - expected_noi)
                coc_diff = abs(data['coc_pct'] - expected_coc)
                
                if mao_diff <= 1 and noi_diff <= 1 and coc_diff <= 0.1:
                    self.log_test("Financial Calculations", True, 
                                f"MAO: ${data['mao_cash']:,}, NOI: ${data['noi_monthly']:,}/mo, CoC: {data['coc_pct']:.1f}%")
                    return True
                else:
                    self.log_test("Financial Calculations", False, 
                                f"Calculation errors - MAO diff: {mao_diff}, NOI diff: {noi_diff}, CoC diff: {coc_diff}")
                    return False
            else:
                self.log_test("Financial Calculations", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Financial Calculations", False, f"Exception: {str(e)}")
            return False
    
    def test_serpapi_integration(self):
        """Test SERPAPI market scanning functionality"""
        try:
            # Test with form data as expected by the endpoint
            scan_data = {
                'city': 'Atlanta',
                'state': 'GA',
                'filters': json.dumps({
                    'dom_min': 100,
                    'price_max': 500000,
                    'beds_min': 2
                })
            }
            
            response = self.session.post(
                f"{API_BASE}/candidates/scan",
                data=scan_data,
                timeout=30  # Longer timeout for external API
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0:
                        # Verify candidate structure
                        candidate = data[0]
                        required_fields = ['id', 'address', 'city', 'state', 'list_price', 'days_on_market', 'opportunity_score', 'deal_signal']
                        
                        if all(field in candidate for field in required_fields):
                            self.log_test("SERPAPI Integration", True, 
                                        f"Found {len(data)} candidates, top score: {candidate['opportunity_score']}")
                            return True
                        else:
                            missing = [f for f in required_fields if f not in candidate]
                            self.log_test("SERPAPI Integration", False, f"Missing candidate fields: {missing}")
                            return False
                    else:
                        self.log_test("SERPAPI Integration", True, "No candidates found (valid response)")
                        return True
                else:
                    self.log_test("SERPAPI Integration", False, f"Expected list, got: {type(data)}")
                    return False
            elif response.status_code == 400:
                # Check if it's due to missing SERPAPI key
                error_text = response.text
                if "SERPAPI_KEY not configured" in error_text:
                    self.log_test("SERPAPI Integration", False, "SERPAPI_KEY not configured")
                    return False
                else:
                    self.log_test("SERPAPI Integration", False, f"Bad request: {error_text}")
                    return False
            else:
                self.log_test("SERPAPI Integration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SERPAPI Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_deal_delete(self, deal_id: str):
        """Test DELETE deal endpoint"""
        try:
            response = self.session.delete(f"{API_BASE}/deals/{deal_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "deleted successfully" in data.get('message', ''):
                    self.log_test("Deal DELETE", True, f"Deleted deal {deal_id[:8]}...")
                    return True
                else:
                    self.log_test("Deal DELETE", False, f"Unexpected response: {data}")
                    return False
            elif response.status_code == 404:
                self.log_test("Deal DELETE", False, f"Deal not found: {deal_id}")
                return False
            else:
                self.log_test("Deal DELETE", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Deal DELETE", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test API error handling with invalid inputs"""
        try:
            # Test invalid deal creation
            invalid_deal = {
                "address": "",  # Empty address
                "city": "Test",
                "state": "INVALID",  # Invalid state code
                "list_price": -1000,  # Negative price
                "days_on_market": "not_a_number"  # Invalid type
            }
            
            response = self.session.post(
                f"{API_BASE}/deals",
                json=invalid_deal,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Should return 422 (validation error) or 400 (bad request)
            if response.status_code in [400, 422]:
                self.log_test("Error Handling", True, f"Properly rejected invalid input: HTTP {response.status_code}")
                return True
            else:
                self.log_test("Error Handling", False, f"Should have rejected invalid input: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_deals(self):
        """Clean up any deals created during testing"""
        for deal_id in self.created_deal_ids:
            try:
                self.session.delete(f"{API_BASE}/deals/{deal_id}", timeout=5)
            except:
                pass  # Ignore cleanup errors
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"\n🚀 Starting QuickLiqi Backend API Tests")
        print(f"📍 Testing against: {API_BASE}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Core API Tests
        print("\n📋 Core API Tests:")
        self.test_health_check()
        
        print("\n⚙️ Settings Management Tests:")
        self.test_settings_get()
        self.test_settings_update()
        
        print("\n🏠 Deal Management Tests:")
        self.test_deals_get_empty()
        
        # Create a test deal for subsequent tests
        created_deal = self.test_deal_create()
        if created_deal:
            deal_id = created_deal['id']
            self.test_deal_get_by_id(deal_id)
            self.test_deal_update(deal_id)
            self.test_deal_status_update(deal_id)
        
        print("\n🧮 Financial Calculation Tests:")
        self.test_financial_calculations()
        
        print("\n🔍 SERPAPI Integration Tests:")
        self.test_serpapi_integration()
        
        print("\n❌ Error Handling Tests:")
        self.test_error_handling()
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        self.cleanup_test_deals()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return passed_tests, failed_tests

def main():
    """Main test execution"""
    tester = QuickLiqiAPITester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()