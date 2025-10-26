# Production Deployment Checklist

## Static Files & CSS Issues Fix

### 1. Collect Static Files
```bash
python manage.py collectstatic --noinput --clear
```

### 2. Verify Static Files
```bash
python manage.py collect_static_production
```

### 3. Check Static File Serving
- Ensure `STATIC_URL` and `STATIC_ROOT` are properly configured
- Verify static files are accessible via web server (nginx/apache)
- Check that CSS files are loading in browser developer tools

### 4. Test All Pages
- [ ] Home page (`/`) - Hero section, services, floating images
- [ ] Documentation page (`/docs/`) - Should show content with sidebar
- [ ] Privacy page (`/privacy-policy/`) - Should show styled content
- [ ] Cookies page (`/cookie-policy/`) - Should show styled content
- [ ] Navigation links should have proper spacing

### 5. Browser Testing
- [ ] Test at 100% zoom (no image truncation)
- [ ] Test responsive design on mobile
- [ ] Verify all animations work
- [ ] Check that hero text is jet black and visible

### 6. Production Environment Variables
```bash
# Ensure these are set in production
DEBUG=False
STATIC_URL=/static/
STATIC_ROOT=/path/to/static/files
```

### 7. Web Server Configuration
Ensure your web server (nginx/apache) is configured to serve static files:
```nginx
location /static/ {
    alias /path/to/static/files/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Critical CSS Fallback
All critical styles are now embedded in `base.html` to ensure they work even if external CSS files fail to load.

## Troubleshooting
- If styles still don't load, check browser developer tools for 404 errors on CSS files
- Verify file permissions on static files directory
- Check web server logs for static file serving errors
