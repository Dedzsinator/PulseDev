#!/bin/bash

# Test script for PulseDev+ plugin integration
# This script simulates the plugin making API calls to the backend

echo "🧪 Testing PulseDev+ Plugin Integration"
echo "=============================================="

BASE_URL="http://localhost:8000"
SESSION_ID="plugin-test-$(date +%s)"

echo ""
echo "📊 Testing Backend Health..."
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health")
if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null; then
    echo "✅ Backend is healthy"
    echo "$HEALTH_RESPONSE" | jq .
else
    echo "❌ Backend health check failed"
    echo "$HEALTH_RESPONSE"
    exit 1
fi

echo ""
echo "📝 Creating test context events (simulating Neovim plugin)..."

# Simulate file opening
echo "  → File opened: main.py"
EVENT_1=$(curl -s -X POST "${BASE_URL}/api/v1/context/events" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"${SESSION_ID}\",
    \"agent\": \"editor\",
    \"type\": \"editor_focus\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"payload\": {
      \"file_path\": \"/home/user/project/main.py\",
      \"language\": \"python\"
    }
  }")

if echo "$EVENT_1" | jq -e '.status == "success"' > /dev/null; then
    echo "    ✅ File focus event created"
    echo "$EVENT_1" | jq .
else
    echo "    ❌ Failed to create file focus event"
    echo "$EVENT_1"
    exit 1
fi

# Simulate file editing
sleep 1
echo "  → File edited: main.py"
EVENT_2=$(curl -s -X POST "${BASE_URL}/api/v1/context/events" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"${SESSION_ID}\",
    \"agent\": \"editor\",
    \"type\": \"file_modified\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"payload\": {
      \"file_path\": \"/home/user/project/main.py\",
      \"function_name\": \"calculate_score\",
      \"language\": \"python\",
      \"lines_changed\": 15,
      \"change_type\": \"modification\"
    }
  }")

if echo "$EVENT_2" | jq -e '.status == "success"' > /dev/null; then
    echo "    ✅ File modification event created"
    echo "$EVENT_2" | jq .
else
    echo "    ❌ Failed to create file modification event"
    echo "$EVENT_2"
    exit 1
fi

# Simulate command execution
sleep 1
echo "  → Command executed: python main.py"
EVENT_3=$(curl -s -X POST "${BASE_URL}/api/v1/context/events" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"${SESSION_ID}\",
    \"agent\": \"terminal\",
    \"type\": \"command_executed\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"payload\": {
      \"command\": \"python main.py\",
      \"exit_code\": 0,
      \"output\": \"Hello, World!\",
      \"working_directory\": \"/home/user/project\"
    }
  }")

if echo "$EVENT_3" | jq -e '.status == "success"' > /dev/null; then
    echo "    ✅ Command execution event created"
    echo "$EVENT_3" | jq .
else
    echo "    ❌ Failed to create command execution event"
    echo "$EVENT_3"
    exit 1
fi

echo ""
echo "🤖 Testing AI Prompt Generation..."
AI_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/ai/prompt" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"${SESSION_ID}\",
    \"context_window_minutes\": 30
  }")

if echo "$AI_RESPONSE" | jq -e '.prompt' > /dev/null; then
    echo "✅ AI prompt generated successfully"
    echo "Event count: $(echo "$AI_RESPONSE" | jq -r '.event_count')"
    echo ""
    echo "Generated Prompt:"
    echo "=================="
    echo "$AI_RESPONSE" | jq -r '.prompt'
else
    echo "❌ Failed to generate AI prompt"
    echo "$AI_RESPONSE"
    exit 1
fi

echo ""
echo "📊 Testing Gamification Features..."
ACTIVITY_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/gamification/activity/track" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"${SESSION_ID}\",
    \"activity_type\": \"code_edit\",
    \"points\": 10,
    \"metadata\": {
      \"file_type\": \"python\",
      \"lines_changed\": 15
    }
  }")

if echo "$ACTIVITY_RESPONSE" | jq -e '.status == "success"' > /dev/null; then
    echo "✅ Activity tracking successful"
    echo "$ACTIVITY_RESPONSE" | jq .
else
    echo "❌ Activity tracking failed"
    echo "$ACTIVITY_RESPONSE"
fi

echo ""
echo "🎯 All tests completed!"
echo "=============================================="
echo "✅ Backend health: OK"
echo "✅ Context events: OK"
echo "✅ AI prompt generation: OK"
echo "✅ Plugin integration: READY"
echo ""
echo "🔧 To use with Neovim:"
echo "1. Add the plugin configuration to your init.lua"
echo "2. Set api.endpoint = 'http://localhost:8000'"
echo "3. Start coding and watch the magic happen!"
