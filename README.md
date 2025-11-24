# AI Drone Control Center

אפליקציה מודולרית לניהול רחפן ומערכות סביבו.

## גרסה V1 - UI בלבד

גרסה זו מכילה רק מעטפת UI עם נתוני דמו/placeholder, ללא חיבור אמיתי לרחפן.

## התקנה

```bash
# יצירת סביבה וירטואלית
python -m venv venv

# הפעלת הסביבה (Windows)
venv\Scripts\activate

# הפעלת הסביבה (Linux/Mac)
source venv/bin/activate

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
- `services.py` - לוגיקה ונתוני דמו
- `templates/` - תבניות HTML של המודול

## מודולים

- Dashboard
- Flight Controller
- Flight Map
- Ground Control Station
- Modem
- VPN
- Dynamic DNS
- Camera
- Networks
- Users
- Application
