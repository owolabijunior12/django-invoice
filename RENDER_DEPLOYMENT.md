# Django Invoice - Render Deployment Guide

## Prerequisites
- Git repository (GitHub, GitLab, or Bitbucket)
- Render account (https://render.com)
- PostgreSQL database (provided by Render)

## Step 1: Prepare Your Application ✓

The following files have been created/updated:
- ✓ `requirements.txt` - Python dependencies
- ✓ `Procfile` - Specifies how to run the app
- ✓ `.env.example` - Environment variables template
- ✓ `render.yaml` - Render deployment configuration
- ✓ `invoicing/settings.py` - Updated for production

## Step 2: Update Your .gitignore

Add the following to your `.gitignore` if not already present:
```
.env
*.pyc
__pycache__/
.venv/
venv/
db.sqlite3
staticfiles/
uploads/
```

## Step 3: Commit Changes to Git

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

## Step 4: Deploy on Render

### Option A: Using Blueprint (render.yaml) - RECOMMENDED

1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub/GitLab account
4. Select your repository
5. Click "Apply"
6. Configure environment variables (see Step 5)

### Option B: Manual Setup

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Fill in the details:
   - **Name**: django-invoice
   - **Environment**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command**: 
     ```bash
     gunicorn invoicing.wsgi
     ```

## Step 5: Configure Environment Variables

In your Render service settings, add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | Generate a secure key | Use: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'` |
| `DEBUG` | `False` | MUST be False in production |
| `ALLOWED_HOSTS` | `yourdomain.onrender.com` | Replace with your actual domain |
| `DATABASE_URL` | Auto-linked from PostgreSQL | Render will populate this |
| `EMAIL_HOST` | `smtp.gmail.com` | Your email service |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_USE_TLS` | `True` | |
| `EMAIL_HOST_USER` | Your email address | |
| `EMAIL_HOST_PASSWORD` | Your app password | For Gmail: Generate at https://myaccount.google.com/apppasswords |
| `DEFAULT_FROM_EMAIL` | Your email address | |

## Step 6: Set Up PostgreSQL Database

### Using Render's Managed PostgreSQL (Recommended):

1. In Render Dashboard, click "New +" → "PostgreSQL"
2. Set instance name: `django-invoice-db`
3. Choose Free tier (or paid if needed)
4. Click "Create Database"
5. Render will automatically populate `DATABASE_URL` in your web service

### Linking to Your Web Service:

1. Go to your Web Service settings
2. Go to "Environment"
3. The `DATABASE_URL` should already be there from the database you created

## Step 7: Run Migrations

After deployment:
1. Go to your Web Service in Render Dashboard
2. Click "Logs" or "Shell" tab
3. Run: `python manage.py migrate`
4. Create a superuser: `python manage.py createsuperuser`

Or do this before pushing by creating a management command.

## Step 8: Collect Static Files

Your build command automatically runs:
```bash
python manage.py collectstatic --noinput
```

This should handle CSS, JavaScript, and admin assets.

## Step 9: Upload Settings

Before going live, you may want to:
1. Create a superuser account
2. Configure company settings via admin panel
3. Test the application

## Troubleshooting

### Check Logs
- Go to your Service in Render Dashboard
- Click "Logs" tab to see deployment/runtime errors

### Database Connection Issues
- Verify `DATABASE_URL` is set in environment variables
- Check PostgreSQL instance is running
- In logs, look for "DATABASES" configuration errors

### Static Files Not Loading
- Ensure `STATIC_ROOT` is set correctly
- Run `collectstatic` in Render Shell
- Check WhiteNoise middleware is installed

### Email Not Sending
- Verify `EMAIL_HOST_PASSWORD` (use app-specific password for Gmail)
- Check email configuration in settings
- Test with a simple print statement in views

### Secret Key Issues
- Ensure `SECRET_KEY` is long and random
- Don't commit `.env` file to git
- Use environment variables only

## Important Notes

⚠️ **SECURITY WARNINGS:**
- Never commit `.env` file to git
- Always set `DEBUG = False` in production
- Keep `SECRET_KEY` secret and long
- Use strong `EMAIL_HOST_PASSWORD`
- Update `ALLOWED_HOSTS` with your actual domain

## Production Checklist

Before going live:
- [ ] DEBUG is False
- [ ] SECRET_KEY is set and secure
- [ ] ALLOWED_HOSTS includes your domain
- [ ] Database is PostgreSQL (not SQLite)
- [ ] Email configuration is working
- [ ] HTTPS is enabled (automatic on Render)
- [ ] Superuser account created
- [ ] Tested all main features
- [ ] Backed up any data
- [ ] Static files are loading correctly

## Support & Resources

- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/3.2/howto/deployment/
- WhiteNoise: http://whitenoise.evans.io/
- PostgreSQL: https://www.postgresql.org/docs/

---

Once deployed, your app will be available at: `https://your-service-name.onrender.com`
