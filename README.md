# YT-Drone

אפליקציה מודולרית לניהול רחפן ומערכות סביבו.

## גרסה V1 - System Monitoring & Real-time Updates

גרסה זו כוללת:
- **System Monitoring אמיתי** - איסוף נתוני מערכת בזמן אמת (CPU, RAM, Storage, Temperature)
- **WebSocket Integration** - עדכונים בזמן אמת דרך WebSocket
- **Real-time Dashboard** - תצוגת נתוני מערכת מעודכנים אוטומטית
- **UI מתקדם** - עיצוב responsive עם תמיכה בערכות נושא

## תכונות

### System Monitoring
- **System Information**: מערכת הפעלה, חומרה, זמן פעילות
- **CPU Monitoring**: טמפרטורה, שימוש, progress bars עם אינדיקטורים ויזואליים
- **RAM Monitoring**: שימוש בזיכרון בזמן אמת
- **Storage Monitoring**: מעקב אחר Boot partition (MB) ו-Root partition (GB) עם progress bars

### Real-time Updates
- **WebSocket Integration**: עדכונים אוטומטיים כל 5 שניות (CPU, RAM, Temperature) וכל 60 שניות (Storage, Uptime)
- **Monitor Manager**: ניהול מרכזי של כל ה-monitors עם עדכונים תקופתיים
- **Live Dashboard**: עדכון אוטומטי של כל השדות ללא רענון עמוד

### UI/UX
- **Theme Support**: 3 ערכות נושא (Light, Medium, Dark)
- **Responsive Design**: תמיכה מלאה במסכים שונים (desktop, tablet, mobile)
- **Modern UI**: עיצוב נקי ומודרני עם cards, progress bars, ואייקונים
- **Sidebar Navigation**: תפריט צד נפתח/נסגר עם אייקונים לכל מודול

## התקנה

```bash
# יצירת סביבה וירטואלית
python -m venv .venv

# הפעלת הסביבה (Windows)
venv\Scripts\activate

# הפעלת הסביבה (Linux/Mac)
source .venv/bin/activate

# התקנת תלויות
pip install -r requirements.txt
```

## הרצה

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

האפליקציה תהיה זמינה בכתובת: http://0.0.0.0:8001 או http://localhost:8001

## מבנה הפרויקט

הפרויקט בנוי בצורה מודולרית, כאשר כל מודול מכיל:

- `router.py` - Routes של המודול
- `services.py` - לוגיקה ונתוני דמו/אמיתיים
- `templates/` - תבניות HTML של המודול

### תיקיות עיקריות

- `app/core/` - שירותים משותפים:
  - `system.py` - איסוף נתוני מערכת (CPU, RAM, Storage, Temperature)
  - `websocket.py` - WebSocket Manager לניהול connections
  - `websocket_router.py` - WebSocket endpoints
  - `monitor_manager.py` - ניהול monitors עם עדכונים תקופתיים
  - `templates.py` - תמיכה ב-Jinja2 templates
  - `static.py` - ניהול קבצים סטטיים

- `app/modules/` - מודולי האפליקציה
- `app/shared/` - תבניות ומשאבים משותפים
- `app/static/` - קבצים סטטיים (CSS, JS, Images)

## מודולים

- **Dashboard** - תצוגת נתוני מערכת בזמן אמת עם system monitoring
- **Flight Controller** - ניהול בקר טיסה (UI בלבד)
- **Flight Map** - מפה למעקב אחר טיסה (UI בלבד)
- **Ground Control Station** - תחנת בקרה קרקעית (UI בלבד)
- **Modem** - ניהול מודם (UI בלבד)
- **VPN** - ניהול VPN (UI בלבד)
- **Dynamic DNS** - ניהול Dynamic DNS (UI בלבד)
- **Camera** - ניהול מצלמה (UI בלבד)
- **Networks** - ניהול רשתות (UI בלבד)
- **Users** - ניהול משתמשים (UI בלבד)
- **Application** - הגדרות אפליקציה (UI בלבד)

## טכנולוגיות

- **Backend**:
  - FastAPI - Web framework
  - WebSocket - Real-time communication
  - psutil - System information gathering
  - Jinja2 - Template engine

- **Frontend**:
  - HTML5, CSS3 - Responsive design
  - JavaScript (ES6+) - WebSocket client, DOM manipulation
  - SVG Icons - Vector graphics

- **Infrastructure**:
  - Uvicorn - ASGI server
  - Monitor Manager - Periodic task scheduling

## תלויות

התלויות העיקריות:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `psutil` - System information
- `python-multipart` - Form handling

ראה `requirements.txt` לרשימה מלאה.