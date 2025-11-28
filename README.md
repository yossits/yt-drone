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

## התקנה על Raspberry Pi

### דרישות מוקדמות

לפני התחלת ההתקנה, ודא שיש לך:

- **Raspberry Pi** עם **Raspberry Pi OS** מותקן (גרסה אחרונה מומלצת)
- **חיבור לאינטרנט** פעיל
- **הרשאות root** (גישה ל-`sudo`)
- **מערכת הפעלה נקייה** או מערכת קיימת שברצונך להתקין עליה

### התקנה אוטומטית (מומלץ)

הדרך הקלה והמהירה ביותר להתקין את האפליקציה היא באמצעות סקריפט ההתקנה האוטומטי:

```bash
curl -fsSL https://raw.githubusercontent.com/yossits/yt-drone/main/install.sh | sudo bash
```

**מה הסקריפט עושה:**

1. **התקנת חבילות מערכת** - Python 3, Git, pip, venv, net-tools
2. **שכפול/עדכון Repository** - הורדת הקוד מהמאגר ב-GitHub
3. **יצירת סביבה וירטואלית** - Python virtualenv והתקנת כל התלויות
4. **הגדרת UART** - הגדרת UART לחומרה (enable_uart=1, disable-bt)
5. **בדיקת פורט** - וידוא שהפורט 8001 פנוי
6. **יצירת קובץ הרצה** - יצירת `run_app.sh` להרצת האפליקציה
7. **יצירת שירות Systemd** - הגדרת השירות להרצה אוטומטית
8. **הפעלת השירות** - הפעלה אוטומטית של האפליקציה

**לאחר ההתקנה:**

- אם ה-UART שונה, **תידרש אתחול** של המערכת
- האפליקציה תרוץ אוטומטית כשירות systemd
- תוכל לגשת לאפליקציה בכתובת: `http://[IP-של-הרספברי-פאי]:8001`

**פקודות שימושיות:**

```bash
# בדיקת סטטוס השירות
sudo systemctl status drone-hub.service

# צפייה בלוגים
sudo journalctl -u drone-hub.service -f

# הפעלה מחדש של השירות
sudo systemctl restart drone-hub.service

# עצירת השירות
sudo systemctl stop drone-hub.service
```

### התקנה ידנית

אם אתה מעדיף להתקין ידנית, בצע את השלבים הבאים:

#### 1. עדכון המערכת והתקנת חבילות בסיסיות

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip net-tools
```

#### 2. שכפול המאגר

```bash
cd /home/pi
git clone https://github.com/yossits/yt-drone.git
cd yt-drone
```

#### 3. יצירת סביבה וירטואלית והתקנת תלויות

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. הגדרת UART

ערוך את קובץ `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

הוסף או ודא שיש את השורות הבאות:

```
enable_uart=1
dtoverlay=disable-bt
```

שמור את הקובץ (Ctrl+O, Enter, Ctrl+X).

ערוך את קובץ `/boot/cmdline.txt` והסר כל אזכור ל-`console=serial0` או `console=ttyAMA0`:

```bash
sudo nano /boot/cmdline.txt
```

**חשוב:** לאחר שינוי קבצי UART, **אתחל את המערכת**:

```bash
sudo reboot
```

#### 5. יצירת קובץ הרצה

צור קובץ `run_app.sh`:

```bash
nano /home/pi/yt-drone/run_app.sh
```

הוסף את התוכן הבא:

```bash
#!/bin/bash
set -e
cd /home/pi/yt-drone
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

שמור את הקובץ והפוך אותו לביצועי:

```bash
chmod +x /home/pi/yt-drone/run_app.sh
```

#### 6. יצירת שירות Systemd

צור קובץ שירות:

```bash
sudo nano /etc/systemd/system/drone-hub.service
```

הוסף את התוכן הבא:

```ini
[Unit]
Description=Drone Hub Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/yt-drone
ExecStart=/home/pi/yt-drone/run_app.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

שמור את הקובץ.

#### 7. הפעלת השירות

```bash
sudo systemctl daemon-reload
sudo systemctl enable drone-hub.service
sudo systemctl start drone-hub.service
```

בדוק שהשירות רץ:

```bash
sudo systemctl status drone-hub.service
```

### פתרון בעיות

#### השירות לא מתחיל

1. בדוק את הלוגים:
   ```bash
   sudo journalctl -u drone-hub.service -n 50
   ```

2. בדוק שהפורט פנוי:
   ```bash
   sudo netstat -tulpn | grep 8001
   ```

3. בדוק שהקובץ `run_app.sh` קיים ובעל הרשאות ביצוע:
   ```bash
   ls -l /home/pi/yt-drone/run_app.sh
   ```

#### שגיאות בהתקנת תלויות

1. ודא שיש חיבור לאינטרנט
2. נסה לעדכן את pip:
   ```bash
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

#### UART לא עובד

1. ודא שביצעת אתחול לאחר שינוי קבצי UART
2. בדוק את קובץ `/boot/config.txt`:
   ```bash
   cat /boot/config.txt | grep uart
   ```
3. בדוק את קובץ `/boot/cmdline.txt` שאין בו console=serial0:
   ```bash
   cat /boot/cmdline.txt
   ```

#### לא ניתן לגשת לאפליקציה מהרשת

1. בדוק את כתובת ה-IP של הרספברי פאי:
   ```bash
   hostname -I
   ```

2. בדוק שהשירות רץ:
   ```bash
   sudo systemctl status drone-hub.service
   ```

3. בדוק את חומת האש (אם יש):
   ```bash
   sudo ufw status
   ```

## התקנה (פלטפורמות אחרות)

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

### על Raspberry Pi (כשירות)

אם התקנת את האפליקציה עם `install.sh`, היא תרוץ אוטומטית כשירות systemd. השירות יתחיל אוטומטית בכל אתחול.

**ניהול השירות:**

```bash
# בדיקת סטטוס
sudo systemctl status drone-hub.service

# הפעלה
sudo systemctl start drone-hub.service

# עצירה
sudo systemctl stop drone-hub.service

# הפעלה מחדש
sudo systemctl restart drone-hub.service

# צפייה בלוגים בזמן אמת
sudo journalctl -u drone-hub.service -f
```

### הרצה ידנית

להרצה ידנית (לפיתוח או בדיקה):

```bash
cd /home/pi/yt-drone
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**הערה:** אם השירות systemd רץ, עצור אותו קודם:

```bash
sudo systemctl stop drone-hub.service
```

האפליקציה תהיה זמינה בכתובת: `http://[IP-של-הרספברי-פאי]:8001` או `http://localhost:8001`

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