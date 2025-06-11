# Security Action Plan for Firebase Credentials

## Immediate Actions

1. **Revoke Exposed Firebase Credentials**
   - Log in to the Firebase console (https://console.firebase.google.com/)
   - Navigate to Project settings > Service accounts
   - Click "Manage service account permissions"
   - Find the exposed service account (firebase-adminsdk-fbsvc@nutri-app-ed269.iam.gserviceaccount.com)
   - Click the three dots menu and select "Delete service account" or "Disable"
   - Generate a new service account key if needed

2. **Check for Unauthorized Access**
   - Review Firebase project logs for any unusual activity
   - Check Database usage for unexpected reads/writes
   - Monitor your Google Cloud billing for unexpected charges

## Secure Implementation

1. **Set Up Environment Variables**
   - Copy the newly created credentials to your local .env file
   - Format the private key correctly with proper newline escaping (`\n`)
   - Example: `FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nABC123...\n-----END PRIVATE KEY-----\n"`
   - For Vercel deployment, add these environment variables in the Vercel dashboard

2. **For Development**
   - Use the same environment variables approach for both development and production
   - Never store actual credentials in files that might be committed

3. **Testing**
   - Run your app using environment variables to ensure everything works
   - Test Firebase authentication flows

## Best Practices Going Forward

1. **Use `.gitignore` properly**
   - Keep it updated with all secret files and directories
   - Periodically audit your repo for sensitive information

2. **Consider using a secrets manager**
   - For more advanced setups, use AWS Secrets Manager, GCP Secret Manager, or Hashicorp Vault

3. **Regular security audits**
   - Use tools like `git-secrets` or `trufflehog` to scan repositories
   - Set up pre-commit hooks to prevent credential leaks

4. **Educate your team**
   - Share security best practices
   - Document secure credential handling
