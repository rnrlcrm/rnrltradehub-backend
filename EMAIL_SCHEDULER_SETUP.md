# Email and Scheduler Setup Guide

This guide covers setting up Gmail SMTP for email notifications and Cloud Scheduler for automated KYC reminders.

---

## Phase 4: Email Integration (SMTP)

### 1. Gmail SMTP Setup

#### Step 1: Create App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Select **Security** > **2-Step Verification** (enable if not already)
3. Scroll to **App passwords** and click
4. Select **Mail** and **Other (Custom name)**
5. Enter "RNRL TradeHub Backend"
6. Click **Generate**
7. Copy the 16-character app password

#### Step 2: Store in Secret Manager

```bash
# Create SMTP password secret
echo -n "YOUR_16_CHAR_APP_PASSWORD" | gcloud secrets create smtp-password \
  --data-file=- \
  --project=google-mpf-cas7ishusxmu \
  --replication-policy=automatic

# Create SMTP user secret (optional, can use env var)
echo -n "your-email@gmail.com" | gcloud secrets create smtp-user \
  --data-file=- \
  --project=google-mpf-cas7ishusxmu \
  --replication-policy=automatic

# Grant Cloud Run service account access
gcloud secrets add-iam-policy-binding smtp-password \
  --member="serviceAccount:502095789065-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=google-mpf-cas7ishusxmu

gcloud secrets add-iam-policy-binding smtp-user \
  --member="serviceAccount:502095789065-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=google-mpf-cas7ishusxmu
```

#### Step 3: Update Cloud Build Configuration

The `cloudbuild.yaml` has been updated to include:
```yaml
--update-secrets=...,SMTP_PASSWORD=smtp-password:latest
--set-env-vars=...,SMTP_ENABLED=false,SMTP_HOST=smtp.gmail.com,SMTP_PORT=587
```

To enable SMTP after setup, change `SMTP_ENABLED=true` in cloudbuild.yaml.

#### Step 4: Test SMTP Connection

After deployment, test the connection:

```bash
curl -X GET "https://erp-nonprod-backend-502095789065.us-central1.run.app/api/test/smtp" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Email Templates

The following email templates are automatically created:

1. **sub_user_invitation** - Invitation to sub-users with credentials
2. **password_reset** - Password reset link
3. **welcome_partner** - Welcome email for new business partners
4. **kyc_reminder** - KYC verification reminder

Templates are stored in the `email_templates` table and can be customized via API.

### 3. Email Queue Processing

Emails are queued in the `email_logs` table. To enable automatic sending:

**Option A: Process Queue via Endpoint**
```bash
curl -X POST "https://erp-nonprod-backend-502095789065.us-central1.run.app/api/scheduler/process-email-queue" \
  -H "X-Cron-Secret: YOUR_CRON_SECRET"
```

**Option B: Create Cloud Scheduler Job**
```bash
gcloud scheduler jobs create http email-queue-processor \
  --schedule="*/5 * * * *" \
  --uri="https://erp-nonprod-backend-502095789065.us-central1.run.app/api/scheduler/process-email-queue" \
  --http-method=POST \
  --headers="X-Cron-Secret=YOUR_CRON_SECRET" \
  --location=us-central1 \
  --description="Process email queue every 5 minutes"
```

---

## Phase 3: Cloud Scheduler Setup

### 1. Create Cron Secret

```bash
# Generate a secure random secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output

# Store in Secret Manager
echo -n "YOUR_GENERATED_SECRET" | gcloud secrets create cron-secret \
  --data-file=- \
  --project=google-mpf-cas7ishusxmu \
  --replication-policy=automatic

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding cron-secret \
  --member="serviceAccount:502095789065-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=google-mpf-cas7ishusxmu
```

### 2. Create KYC Reminder Scheduler Job

```bash
gcloud scheduler jobs create http kyc-daily-reminders \
  --schedule="0 9 * * *" \
  --uri="https://erp-nonprod-backend-502095789065.us-central1.run.app/api/scheduler/kyc-reminders" \
  --http-method=POST \
  --headers="X-Cron-Secret=YOUR_CRON_SECRET" \
  --location=us-central1 \
  --description="Send daily KYC reminders at 9 AM" \
  --time-zone="Asia/Kolkata"
```

### 3. Verify Scheduler Job

```bash
# List scheduler jobs
gcloud scheduler jobs list --location=us-central1

# Manually trigger a job for testing
gcloud scheduler jobs run kyc-daily-reminders --location=us-central1

# View job logs
gcloud logging read "resource.type=cloud_scheduler_job" --limit=50
```

### 4. Monitor Job Execution

```bash
# Check if job ran successfully
curl -X GET "https://erp-nonprod-backend-502095789065.us-central1.run.app/api/scheduler/kyc-status" \
  -H "X-Cron-Secret: YOUR_CRON_SECRET"
```

---

## Email Templates Customization

### Update Email Template

```bash
curl -X PUT "https://erp-nonprod-backend-502095789065.us-central1.run.app/api/email-templates/welcome_partner" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Welcome to RNRL TradeHub!",
    "body_html": "<h1>Custom HTML Content</h1>",
    "body_text": "Custom text content"
  }'
```

---

## Troubleshooting

### SMTP Issues

**Error: Authentication failed**
- Verify app password is correct
- Ensure 2-Step Verification is enabled
- Check SMTP_USER matches Google account

**Error: Connection timeout**
- Verify SMTP_PORT=587 (TLS)
- Check network/firewall rules
- Try SMTP_PORT=465 (SSL) if 587 fails

**Error: Emails not sending**
- Check `SMTP_ENABLED=true` in environment
- Verify secrets are accessible
- Check email logs: `SELECT * FROM email_logs WHERE status='failed'`

### Scheduler Issues

**Job not triggering**
- Verify schedule cron expression
- Check service account permissions
- Review Cloud Scheduler logs

**Authentication errors**
- Verify CRON_SECRET matches in both places
- Check secret is properly mounted
- Test with manual curl request

---

## Email Sending Limits

### Gmail Limits
- **Free Gmail**: 500 emails/day
- **Google Workspace**: 2,000 emails/day
- **Recommendation**: Use SendGrid/AWS SES for production

### Alternative Email Services

**SendGrid (Recommended for Production):**
```bash
# Update environment variables
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=YOUR_SENDGRID_API_KEY
```

**AWS SES:**
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=YOUR_SES_SMTP_USERNAME
SMTP_PASSWORD=YOUR_SES_SMTP_PASSWORD
```

---

## Security Best Practices

1. **Never commit secrets** to git
2. **Use Secret Manager** for all sensitive data
3. **Rotate secrets** every 90 days
4. **Monitor email logs** for suspicious activity
5. **Implement rate limiting** on email endpoints
6. **Use strong CRON_SECRET** (32+ characters)
7. **Enable SMTP only when ready** (SMTP_ENABLED=false by default)

---

## Monitoring & Alerts

### Set up Cloud Monitoring Alerts

```bash
# Alert if scheduler job fails
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="KYC Scheduler Failed" \
  --condition-display-name="Job execution failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_scheduler_job" AND metric.type="scheduler.googleapis.com/job/num_attempts_failed"'
```

### Check Email Statistics

```sql
-- Email sending statistics
SELECT 
  status,
  COUNT(*) as count,
  DATE(created_at) as date
FROM email_logs
GROUP BY status, DATE(created_at)
ORDER BY date DESC;

-- Failed emails
SELECT 
  recipient,
  subject,
  error_message,
  created_at
FROM email_logs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

---

## Testing

### Test Email Sending

```python
import requests

response = requests.post(
    "https://erp-nonprod-backend-502095789065.us-central1.run.app/api/test/send-test-email",
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"},
    json={"to_email": "test@example.com"}
)
print(response.json())
```

### Test KYC Reminders

```bash
# Manually trigger KYC check
curl -X POST "https://erp-nonprod-backend-502095789065.us-central1.run.app/api/scheduler/kyc-reminders" \
  -H "X-Cron-Secret: YOUR_CRON_SECRET"
```

---

## Next Steps

After email setup:

1. ✅ Test SMTP connection
2. ✅ Send test emails
3. ✅ Create scheduler jobs
4. ✅ Test cron endpoints
5. ✅ Monitor first scheduled run
6. ✅ Set up monitoring alerts
7. ✅ Document any custom templates
8. ✅ Plan migration to production email service (SendGrid/SES)

---

**For Support:**
- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- Cloud Scheduler: https://cloud.google.com/scheduler/docs
- Secret Manager: https://cloud.google.com/secret-manager/docs
