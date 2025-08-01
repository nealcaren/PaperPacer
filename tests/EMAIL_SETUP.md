# 📧 Email Configuration Guide for PaperPacer

This guide explains how to configure email sending for password reset functionality.

## 🚀 Quick Setup Options

### Option 1: Gmail SMTP (Easiest for development)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. **Configure environment variables**:
   ```bash
   MAIL_ENABLED=true
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-character-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

### Option 2: SendGrid (Recommended for production)

1. **Sign up** at [SendGrid.com](https://sendgrid.com/)
2. **Create an API key** in your SendGrid dashboard
3. **Configure environment variables**:
   ```bash
   MAIL_ENABLED=true
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=your-sendgrid-api-key
   MAIL_DEFAULT_SENDER=your-verified-sender@yourdomain.com
   ```

### Option 3: AWS SES (Good for AWS-hosted apps)

1. **Set up AWS SES** in your AWS console
2. **Verify your sending domain/email**
3. **Create SMTP credentials**
4. **Configure environment variables**:
   ```bash
   MAIL_ENABLED=true
   MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-aws-smtp-username
   MAIL_PASSWORD=your-aws-smtp-password
   MAIL_DEFAULT_SENDER=noreply@yourdomain.com
   ```

## 🔧 Environment Setup

### Local Development

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** with your email credentials

3. **Install python-dotenv** (if not already installed):
   ```bash
   pip install python-dotenv
   ```

4. **Update app.py** to load environment variables:
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Add this at the top of app.py
   ```

### Production Deployment

Set environment variables directly on your hosting platform:

**Heroku:**
```bash
heroku config:set MAIL_ENABLED=true
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password
```

**Railway:**
- Add variables in the Railway dashboard under "Variables"

**AWS/DigitalOcean:**
- Set as system environment variables

## 🧪 Testing Email Configuration

1. **Disable email temporarily** for testing:
   ```bash
   MAIL_ENABLED=false
   ```
   This will show password reset links in flash messages instead of sending emails.

2. **Test email sending** with a simple test route:
   ```python
   @app.route('/test-email')
   def test_email():
       if send_email('test@example.com', 'Test', 'This is a test email'):
           return 'Email sent successfully!'
       return 'Email sending failed!'
   ```

## 📊 Email Provider Comparison

| Provider | Cost | Setup Difficulty | Reliability | Best For |
|----------|------|------------------|-------------|----------|
| Gmail SMTP | Free (limited) | Easy | Good | Development/Testing |
| SendGrid | Free tier + paid | Medium | Excellent | Production |
| AWS SES | Pay-per-email | Medium | Excellent | AWS deployments |
| Mailgun | Free tier + paid | Medium | Excellent | Production |

## 🛡️ Security Best Practices

1. **Never commit credentials** to version control
2. **Use app passwords** instead of regular passwords
3. **Rotate API keys** regularly
4. **Monitor email sending** for abuse
5. **Set up SPF/DKIM** records for your domain

## 🐛 Troubleshooting

### Common Issues:

**"Authentication failed":**
- Check username/password are correct
- Ensure 2FA is enabled for Gmail
- Use app password, not regular password

**"Connection refused":**
- Check MAIL_SERVER and MAIL_PORT
- Verify firewall isn't blocking SMTP

**"Emails not received":**
- Check spam folder
- Verify sender email is authentic
- Set up proper DNS records

**"SMTP timeout":**
- Try different port (25, 465, 587)
- Check if your hosting blocks SMTP

## 📝 Email Templates

The current implementation includes:
- **HTML email** with styled button
- **Plain text fallback** for accessibility
- **Responsive design** for mobile devices
- **Security messaging** about link expiration

You can customize the email templates in the `forgot_password` route in `app.py`.

## 🚀 Production Deployment Checklist

- [ ] Environment variables configured
- [ ] Email credentials tested
- [ ] Domain verification completed (if required)
- [ ] SPF/DKIM records configured
- [ ] Rate limiting implemented
- [ ] Email monitoring set up
- [ ] Backup email method configured

## 💡 Advanced Features

Consider implementing:
- **Email templates** stored in files
- **Background email sending** with Celery
- **Email delivery tracking**
- **Bounce handling**
- **Unsubscribe management**