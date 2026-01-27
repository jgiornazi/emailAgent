# Gmail API Setup Guide

This guide walks you through setting up Gmail API credentials for EmailAgent.

## Prerequisites

- Google account (Gmail)
- Access to Google Cloud Console

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** at the top
3. Click **New Project**
4. Enter project name: `EmailAgent` (or your choice)
5. Click **Create**
6. Wait for project creation to complete

## Step 2: Enable Gmail API

1. In your project, go to **APIs & Services** → **Library**
2. Search for **Gmail API**
3. Click on **Gmail API**
4. Click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Click **Create**
4. Fill in required fields:
   - **App name**: `EmailAgent`
   - **User support email**: Your email address
   - **Developer contact**: Your email address
5. Click **Save and Continue**
6. On **Scopes** page, click **Add or Remove Scopes**
7. Find and select:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
8. Click **Update**
9. Click **Save and Continue**
10. On **Test users** page, click **Add Users**
11. Add your Gmail address
12. Click **Save and Continue**
13. Review and click **Back to Dashboard**

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as application type
4. Enter name: `EmailAgent Desktop`
5. Click **Create**
6. A dialog shows your Client ID and Secret
7. Click **Download JSON** (or the download icon)
8. Save the file

## Step 5: Install Credentials

Move the downloaded file to EmailAgent's config directory:

```bash
# Create config directory
mkdir -p ~/.emailagent

# Move credentials file
mv ~/Downloads/client_secret_*.json ~/.emailagent/credentials.json
```

Verify the file:

```bash
cat ~/.emailagent/credentials.json | head -5
```

You should see JSON starting with:
```json
{
  "installed": {
    "client_id": "...",
    "project_id": "...",
```

## Step 6: First Authentication

Run EmailAgent to complete OAuth flow:

```bash
emailagent auth login
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Request permission to access Gmail
4. Save the authentication token

After successful authentication, you'll see:
```
✓ Successfully authenticated as your@gmail.com
```

## Troubleshooting

### "Access blocked: This app's request is invalid"

**Cause**: OAuth consent screen not configured correctly.

**Solution**:
1. Go to OAuth consent screen
2. Ensure your email is added as a test user
3. Check that all required fields are filled

### "Error 403: access_denied"

**Cause**: You denied the permission request.

**Solution**:
1. Run `emailagent auth login` again
2. Click "Allow" on the permission screen

### "credentials.json not found"

**Cause**: Credentials file is missing or in wrong location.

**Solution**:
1. Download credentials from Google Cloud Console
2. Save to `~/.emailagent/credentials.json`
3. Verify file exists: `ls -la ~/.emailagent/`

### "Token expired"

**Cause**: OAuth token has expired.

**Solution**:
```bash
# Force re-authentication
emailagent auth login
```

### "Insufficient Permission"

**Cause**: Missing API scopes.

**Solution**:
1. Delete token file: `rm ~/.emailagent/token.json`
2. Re-authenticate: `emailagent auth login`
3. Ensure you grant all requested permissions

## Security Notes

### Credential Files

- `credentials.json`: OAuth client configuration (safe to keep, don't share)
- `token.json`: Your access token (sensitive, don't share)

### File Permissions

Set secure permissions:
```bash
chmod 600 ~/.emailagent/credentials.json
chmod 600 ~/.emailagent/token.json
```

### Revoking Access

To revoke EmailAgent's access to your Gmail:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **Third-party apps with account access**
3. Find **EmailAgent**
4. Click **Remove Access**

Or use the CLI:
```bash
emailagent auth logout --revoke
```

## API Quotas

Gmail API free tier limits:

- **10,000 requests per day**
- **250 quota units per user per second**

Typical usage:
- Scanning 1000 emails: ~1,000 quota units
- Well within free tier limits

## Publishing (Optional)

For personal use, "Testing" mode is sufficient. To remove the "unverified app" warning:

1. Go to **OAuth consent screen**
2. Click **Publish App**
3. Complete Google verification (requires privacy policy, etc.)

For personal use, this is not necessary.

## Next Steps

After setup is complete:

```bash
# Verify authentication
emailagent auth status

# Run first scan (preview mode)
emailagent job scan --preview
```

See [README.md](README.md) for full usage instructions.
