# Google OAuth Setup Guide - Fix invalid_grant Error

## The Problem

The `invalid_grant` error occurs when:
1. **Redirect URI mismatch**: The redirect URI in your code doesn't match what's configured in Google Cloud Console
2. **Authorization code already used**: The code can only be used once (if page refreshes, it fails)
3. **Authorization code expired**: Codes expire after ~10 minutes

## How to Fix

### Step 1: Verify Redirect URI in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your **OAuth 2.0 Client ID** (the one used for sign-in)
5. Under **Authorized redirect URIs**, ensure this EXACT URI is listed:
   ```
   http://localhost:3000/onboarding/google/callback
   ```
6. **Important**: The URI must match EXACTLY (including `http://` not `https://`, and the port `3000`)
7. Click **Save**

### Step 2: Verify Your credentials.json File

1. Check that `credentials.json` exists in your `backend/` directory
2. Verify it contains the correct Client ID and Client Secret
3. The Client ID should match the one in Google Cloud Console

### Step 3: Test Again

1. **Clear browser cache/cookies** for localhost
2. Try signing in with Google again
3. **Do NOT refresh the page** during the callback
4. If it still fails, check the debug logs at `.cursor/debug.log`

## Common Issues

### Issue 1: Redirect URI Not Added
- **Symptom**: `invalid_grant` error immediately
- **Fix**: Add `http://localhost:3000/onboarding/google/callback` to Google Cloud Console

### Issue 2: Wrong Redirect URI Format
- **Symptom**: `invalid_grant` error
- **Fix**: Ensure it's exactly `http://localhost:3000/onboarding/google/callback` (not `https://`, not different port)

### Issue 3: Page Refresh
- **Symptom**: `invalid_grant` error on refresh
- **Fix**: Don't refresh the page. The code can only be used once. If you refresh, you need to start over.

### Issue 4: Code Expired
- **Symptom**: `invalid_grant` error after waiting too long
- **Fix**: Authorization codes expire after ~10 minutes. Start the sign-in process again.

## Verification

After adding the redirect URI, you should see:
- No `invalid_grant` error
- Successful token exchange
- User info retrieved from Google
- Company name collection form appears

## Debug Logs

Check `.cursor/debug.log` for detailed information about:
- Redirect URI used
- Scopes requested
- Error type and message
- Whether it's an `invalid_grant` error

