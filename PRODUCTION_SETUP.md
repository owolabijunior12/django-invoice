# Production Setup Guide for Django Invoice on Render

## Why PostgreSQL is Essential for Production

**SQLite won't work in production** because:
- Render has an ephemeral filesystem
- Your `db.sqlite3` file gets deleted every ~15 minutes of inactivity
- All invoices, clients, and data are lost on restarts

**PostgreSQL** keeps data in a managed database that persists forever.

---

## STEP 1: Update to PostgreSQL Configuration

### 1.1 Update requirements.txt

Add PostgreSQL driver back:
```txt
Django==3.2.6
gunicorn==21.2.0
django-crispy-forms==2.0
crispy-bootstrap5==0.7
psycopg2-binary==2.9.9
python-decouple==3.8
dj-database-url==2.1.0
whitenoise==6.6.0
Pillow==10.1.0
requests==2.31.0
reportlab==4.0.7
```

### 1.2 Update render.yaml

```yaml
services:
  - type: web
    name: django-invoice
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
    startCommand: gunicorn invoicing.wsgi
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
      - key: DEBUG
        value: false
      - key: SECRET_KEY
        generateValue: true
      - fromGroup: render_postgres
        key: DATABASE_URL

databases:
  - name: postgres
    plan: free
    ipAllowList: []
    envVarKey: render_postgres
```

---

## STEP 2: Secure Your Production Settings

### 2.1 Verify settings.py has production settings

Your settings.py should have:

```python
# Load environment variables
from decouple import config, Csv

# Security settings
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Database with PostgreSQL support
import dj_database_url
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

### 2.2 Add Production Security Headers

Add to the end of `invoicing/settings.py`:

```python
# ===============================
# PRODUCTION SECURITY SETTINGS
# ===============================

# Only if DEBUG is False (production)
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_SECURITY_POLICY = {
        "default-src": ("'self'",),
        "script-src": ("'self'", "cdn.jsdelivr.net"),
        "style-src": ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net"),
    }
```

---

## STEP 3: Deploy on Render (Complete Flow)

### 3.1 Commit and Push Changes

```bash
cd c:\Users\IBOYTECH\Desktop\CodesFile\django-invoice
git add .
git commit -m "Setup production with PostgreSQL and security headers"
git push origin main
```

### 3.2 Deploy via Render Blueprint

1. Go to **https://dashboard.render.com**
2. Click **"New +"** → **"Blueprint"**
3. **Connect GitHub** (if not already connected)
4. Select your **django-invoice** repository
5. Click **"Connect"**
6. Review the blueprint
7. Click **"Create New Resources"**

Render will automatically:
- ✓ Create web service (Django app)
- ✓ Create PostgreSQL database
- ✓ Link them together
- ✓ Run migrations
- ✓ Collect static files

### 3.3 Manual Deployment (Alternative)

**If Blueprint fails, do manual setup:**

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub account and select `django-invoice` repo
3. Fill in details:
   - **Name:** django-invoice
   - **Environment:** Python 3
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command:** 
     ```bash
     gunicorn invoicing.wsgi
     ```
   - **Plan:** Free tier

4. Click **"Create Web Service"**

5. Go to **"Environment"** tab → Add variables (see Step 4)

6. Then create PostgreSQL:
   - Click **"New +"** → **"PostgreSQL"**
   - **Name:** postgres (or any name)
   - **Database:** invoicedb
   - **User:** (auto-generated)
   - **Plan:** Free
   - Click **"Create Database"**

7. Render auto-populates `DATABASE_URL` in web service

---

## STEP 4: Configure Environment Variables

Go to your Web Service → **"Environment"** tab

Add these variables:

| Key | Value | How to Get |
|-----|-------|-----------|
| `DEBUG` | `false` | Hardcoded |
| `ALLOWED_HOSTS` | `yourapp.onrender.com` | Replace with your Render domain |
| `SECRET_KEY` | **(auto-generated)** | Let Render generate it |
| `DATABASE_URL` | **(auto-linked)** | Automatically set from PostgreSQL |
| `EMAIL_HOST` | `smtp.gmail.com` | Your email service |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_USE_TLS` | `true` | Enable TLS |
| `EMAIL_HOST_USER` | `your-email@gmail.com` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | `xxxx xxxx xxxx xxxx` | [Generate app password](#generate-gmail-app-password) |
| `DEFAULT_FROM_EMAIL` | `your-email@gmail.com` | Your email |

### Generate Gmail App Password

1. Go to **https://myaccount.google.com/apppasswords**
2. Select **Mail** and **Windows Computer**
3. Copy the 16-character password
4. Paste in `EMAIL_HOST_PASSWORD`

**⚠️ Important:** This is NOT your Gmail password, it's a special app password.

---

## STEP 5: Test Your Deployment

### 5.1 Check Build Logs

1. Go to your service in Render Dashboard
2. Click **"Logs"** tab
3. Wait for build to complete (green checkmark)
4. Look for: `"Migrations applied successfully"` and `"Collectstatic completed"`

### 5.2 Visit Your App

1. Find your service URL in Render Dashboard (looks like: `https://django-invoice-xxxxx.onrender.com`)
2. Click the link to visit your app
3. You should see the login page

### 5.3 Create Superuser

1. In Render Dashboard, go to your web service
2. Click **"Shell"** tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter username, email, password
5. Done!

### 5.4 Access Admin Panel

1. Go to `https://your-app-name.onrender.com/admin`
2. Login with superuser credentials
3. Configure company settings, email, etc.

---

## STEP 6: Verify Everything Works

### Checklist:

- [ ] App loads without errors
- [ ] Login page appears
- [ ] Can login with superuser
- [ ] Can access admin panel
- [ ] Can create/view invoices
- [ ] Can create/view clients
- [ ] Static files load (CSS, JS work)
- [ ] Database persists data (create invoice → refresh → still there)

### If Something Fails:

1. **Check Logs:** Render Dashboard → Service → **Logs**
2. **Check Error Messages:** Look for Python tracebacks
3. **Common Issues:**
   - `ModuleNotFoundError` → Check requirements.txt
   - `DATABASE` error → Check DATABASE_URL in environment variables
   - `SECRET_KEY` error → Ensure it's set in environment
   - Static files missing → Run: `python manage.py collectstatic`

---

## STEP 7: Post-Launch Configuration

### 7.1 Configure Company Settings

1. Login to admin: `/admin/`
2. Go to **Settings**
3. Set:
   - Company name
   - Company logo
   - Tax rate
   - Currency
   - Invoice prefix

### 7.2 Test Email (Optional)

If you configured email:
1. In admin, try sending a test email
2. Check inbox for confirmation

### 7.3 Set Up Custom Domain (Optional)

1. Register a domain (GoDaddy, Namecheap, etc.)
2. In Render Dashboard → Service → **Settings** → **Custom Domains**
3. Add your domain
4. Update DNS records (Render provides instructions)

---

## STEP 8: Monitoring & Maintenance

### Monitor Your App

1. **Check Logs Regularly:**
   - Render Dashboard → Service → **Logs**
   - Look for errors or warnings

2. **Monitor Database Usage:**
   - Render Dashboard → Database → **Info**
   - Free tier: 256 MB storage (usually enough for thousands of invoices)

3. **Check Performance:**
   - Response times in logs
   - Page load speed in browser

### Regular Maintenance

- **Weekly:** Check logs for errors
- **Monthly:** Backup important data
- **As Needed:** Update Django/packages for security patches

### Backup Your Database

```bash
# In Render Shell:
pg_dump $DATABASE_URL > backup.sql
```

---

## STEP 9: Production Best Practices

### Security Checklist

- ✓ `DEBUG = False` (never True in production)
- ✓ `SECRET_KEY` is secure and unique
- ✓ `ALLOWED_HOSTS` only includes your domain
- ✓ Database uses strong password
- ✓ HTTPS enabled (automatic on Render)
- ✓ Email credentials use app-specific password
- ✓ `.env` file is in `.gitignore`
- ✓ Admin URL is obscured (not `/admin/` if possible)

### Performance

- WhiteNoise handles static files efficiently
- Gunicorn runs 4 workers by default
- PostgreSQL is optimized for production

### Scaling

- Free tier is good for development/small usage
- If you get 1000+ invoices, consider upgrading:
  - Web service: Standard tier ($12/month)
  - Database: Standard tier ($15/month)

---

## Quick Reference: Key Commands

```bash
# Run locally before pushing
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Make migrations
python manage.py makemigrations
python manage.py migrate

# Check for security issues
python manage.py check --deploy

# Export database
pg_dump $DATABASE_URL > backup.sql
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **App won't load** | Check Logs tab for errors |
| **Database error** | Verify DATABASE_URL in Environment |
| **Static files missing** | Run collectstatic in Shell tab |
| **Can't login** | Create superuser in Shell tab |
| **Email not working** | Check EMAIL_HOST_PASSWORD is app-specific |
| **Data lost after restart** | You're using SQLite! Switch to PostgreSQL |
| **ALLOWED_HOSTS error** | Update ALLOWED_HOSTS with your domain |

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **Django Deployment:** https://docs.djangoproject.com/en/3.2/howto/deployment/
- **WhiteNoise:** http://whitenoise.evans.io/
- **PostgreSQL:** https://www.postgresql.org/docs/

---

## Summary: 3 Simple Steps to Production

1. **Update files:** Use PostgreSQL in `requirements.txt` and `render.yaml`
2. **Deploy:** Push to GitHub → Create Blueprint on Render
3. **Configure:** Set environment variables → Create superuser → Done!

Your app will be live at: `https://your-service-name.onrender.com`
