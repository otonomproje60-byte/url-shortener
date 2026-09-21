#!/bin/bash
# Simple test for URL shortener service

SERVICE_URL="http://localhost:5000"
TEST_URL="https://example.com"

echo "Testing URL shortener service at $SERVICE_URL"
echo "Test URL: $TEST_URL"

# Test shortening
echo -n "Shortening... "
RESPONSE=$(curl -s -X POST "$SERVICE_URL/" -d "url=$TEST_URL" -H "Content-Type: application/x-www-form-urlencoded")
if [ $? -ne 0 ]; then
  echo "FAILED - curl error"
  exit 1
fi

SHORT_CODE=$(echo "$RESPONSE" | grep -o '"short_code":"[^"]*"' | cut -d'"' -f4)
if [ -z "$SHORT_CODE" ]; then
  echo "FAILED - no short code in response"
  echo "Response: $RESPONSE"
  exit 1
fi

SHORT_URL="$SERVICE_URL/$SHORT_CODE"
echo "SUCCESS - $SHORT_URL"

# Test redirect
echo -n "Testing redirect... "
REDIRECT_RESPONSE=$(curl -s -I "$SHORT_URL" | grep -i "location:")
if [ $? -ne 0 ]; then
  echo "FAILED - curl error"
  exit 1
fi

REDIRECT_URL=$(echo "$REDIRECT_RESPONSE" | cut -d' ' -f2 | tr -d '\r')
if [ "$REDIRECT_URL" = "$TEST_URL" ]; then
  echo "SUCCESS - redirects to $TEST_URL"
else
  echo "FAILED - expected $TEST_URL, got $REDIRECT_URL"
  exit 1
fi

echo "All tests passed!"