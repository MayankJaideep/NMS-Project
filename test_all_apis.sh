#!/bin/bash

echo "========================================"
echo "   SCNMS COMPREHENSIVE API TEST SUITE"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    response=$(curl -s -w "%{http_code}" -o /tmp/api_response.json "$url")
    http_code="${response: -3}"
    
    if [ "$http_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        ((passed++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_code)"
        cat /tmp/api_response.json
        echo ""
        ((failed++))
        return 1
    fi
}

echo "=== 1. HEALTH CHECKS ==="
test_endpoint "API Gateway Health" "http://localhost:8000/health"
test_endpoint "Services Health" "http://localhost:8000/api/v1/health/services"
echo ""

echo "=== 2. DEVICE MANAGEMENT ===" 
test_endpoint "List All Devices" "http://localhost:8000/api/v1/devices"
test_endpoint "Get Device by ID" "http://localhost:8000/api/v1/devices/1"
test_endpoint "Get Device Statistics" "http://localhost:8000/api/v1/devices/stats"
echo ""

echo "=== 3. METRICS ===" 
test_endpoint "Query All Metrics (limit 10)" "http://localhost:8000/api/v1/metrics?limit=10"
test_endpoint "Query CPU Metrics" "http://localhost:8000/api/v1/metrics?metric_names=cpu_utilization&limit=5"
test_endpoint "Query Metrics for Device 1" "http://localhost:8000/api/v1/metrics?device_ids=1&limit=5"
test_endpoint "Query Multiple Metrics" "http://localhost:8000/api/v1/metrics?metric_names=cpu_utilization&metric_names=memory_utilization&limit=10"
echo ""

echo "=== 4. ALARMS ===" 
test_endpoint "List All Alarms" "http://localhost:8000/api/v1/alarms"
test_endpoint "Get Active Alarms" "http://localhost:8000/api/v1/alarms?status=raised"
test_endpoint "Get Critical Alarms" "http://localhost:8000/api/v1/alarms?severity=critical"
test_endpoint "Alarm Stats Summary" "http://localhost:8000/api/v1/alarms/stats/summary"
echo ""

echo "=== 5. ALARM RULES ===" 
test_endpoint "List Alarm Rules" "http://localhost:8000/api/v1/alarm-rules"
test_endpoint "Get Alarm Rule by ID" "http://localhost:8000/api/v1/alarm-rules/1"
echo ""

echo "=== 6. DASHBOARD ===" 
test_endpoint "Dashboard Summary" "http://localhost:8000/api/v1/dashboard/summary"
echo ""

echo "=== 7. DIRECT SERVICE HEALTH ===" 
test_endpoint "Device Discovery Health" "http://localhost:8001/health"
test_endpoint "Poller Health" "http://localhost:8002/health"
test_endpoint "Data Ingestion Health" "http://localhost:8003/health"
test_endpoint "Alarm Manager Health" "http://localhost:8004/health"
echo ""

echo "========================================"
echo -e "   TEST RESULTS"
echo "========================================"
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo "Total:  $((passed + failed))"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
