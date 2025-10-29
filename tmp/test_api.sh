#!/bin/bash

# Test Script für MindBridge API
# Testet verschiedene Endpoints

echo "🧪 MindBridge API Test Suite"
echo "=============================="
echo ""

# 1. Registrierung
echo "1️⃣  Testing Patient Registration..."
REGISTER_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/users/register/patient' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }')

TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ]; then
    echo "✅ Registration successful!"
    echo "Token: ${TOKEN:0:20}..."
else
    echo "❌ Registration failed"
    echo "$REGISTER_RESPONSE" | jq '.'
    exit 1
fi

echo ""
echo "2️⃣  Testing Login..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/users/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123!"
  }')

LOGIN_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$LOGIN_TOKEN" != "null" ]; then
    echo "✅ Login successful!"
else
    echo "❌ Login failed"
    echo "$LOGIN_RESPONSE" | jq '.'
fi

echo ""
echo "3️⃣  Testing Mood Entry Creation..."
MOOD_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/mood/' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "mood_score": 7.5,
    "energy_level": 6.0,
    "stress_level": 4.0,
    "sleep_hours": 7.5,
    "sleep_quality": 8.0,
    "activities": ["exercise", "meditation"],
    "notes": "Guter Tag heute!"
  }')

MOOD_ID=$(echo $MOOD_RESPONSE | jq -r '.id')

if [ "$MOOD_ID" != "null" ]; then
    echo "✅ Mood entry created!"
    echo "$MOOD_RESPONSE" | jq '{id, mood_score, energy_level, activities}'
else
    echo "❌ Mood entry creation failed"
    echo "$MOOD_RESPONSE" | jq '.'
fi

echo ""
echo "4️⃣  Testing Dream Entry Creation..."
DREAM_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/dreams/' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Flug über die Stadt",
    "content": "Ich bin über die Stadt geflogen und konnte alles von oben sehen.",
    "emotion": "excited",
    "lucidity_level": 5,
    "tags": ["flying", "city", "adventure"]
  }')

DREAM_ID=$(echo $DREAM_RESPONSE | jq -r '.id')

if [ "$DREAM_ID" != "null" ]; then
    echo "✅ Dream entry created!"
    echo "$DREAM_RESPONSE" | jq '{id, title, emotion, lucidity_level}'
else
    echo "❌ Dream entry creation failed"
    echo "$DREAM_RESPONSE" | jq '.'
fi

echo ""
echo "5️⃣  Testing Mood Analytics..."
ANALYTICS_RESPONSE=$(curl -s -X GET 'http://localhost:8000/api/v1/analytics/mood/trends?days=7' \
  -H "Authorization: Bearer $TOKEN")

echo "$ANALYTICS_RESPONSE" | jq '.'

echo ""
echo "6️⃣  Testing AI Mood Analysis..."
AI_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/ai/analyze-mood' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "mood_score": 7.5,
    "energy_level": 6.0,
    "stress_level": 4.0,
    "activities": ["exercise", "meditation"],
    "notes": "Guter Tag heute!"
  }')

echo "$AI_RESPONSE" | jq '.'

echo ""
echo "7️⃣  Testing Health Check..."
curl -s http://localhost:8000/api/health | jq '.'

echo ""
echo "✨ Tests completed!"
