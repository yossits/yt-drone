// Theme Selector + Global UI logic
document.addEventListener("DOMContentLoaded", function () {
  const themeToggle = document.getElementById("theme-toggle");
  const themeDropdown = document.getElementById("theme-dropdown");
  const themeOptions = document.querySelectorAll(".theme-option");
  const body = document.body;

  // פונקציה לעדכון ערכת הנושא
  function setTheme(theme) {
    // הסרת כל ערכות הנושא
    body.classList.remove("theme-light", "theme-medium", "theme-dark");
    
    // הוספת ערכת הנושא הנבחרת
    body.classList.add(`theme-${theme}`);
    
    // עדכון localStorage
    localStorage.setItem("theme", theme);
    
    // עדכון אייקון בכפתור
    const icons = {
      light: "☀️",
      medium: "🌓",
      dark: "🌙"
    };
    themeToggle.querySelector("span").textContent = icons[theme];
    
    // עדכון סימון בחלונית
    themeOptions.forEach(option => {
      option.classList.remove("active");
      if (option.dataset.theme === theme) {
        option.classList.add("active");
      }
    });
    
    // סגירת החלונית
    themeDropdown.classList.remove("show");
  }

  // טעינת ערכת נושא שמורה
  const savedTheme = localStorage.getItem("theme") || "light";
  setTheme(savedTheme);

  // פתיחה/סגירה של חלונית בחירה
  themeToggle.addEventListener("click", function (e) {
    e.stopPropagation();
    themeDropdown.classList.toggle("show");
  });

  // בחירת ערכת נושא מהרשימה
  themeOptions.forEach(option => {
    option.addEventListener("click", function () {
      const selectedTheme = this.dataset.theme;
      setTheme(selectedTheme);
    });
  });

  // סגירת החלונית בלחיצה מחוץ לה
  document.addEventListener("click", function (e) {
    if (!themeToggle.contains(e.target) && !themeDropdown.contains(e.target)) {
      themeDropdown.classList.remove("show");
    }
  });

  // Sidebar Toggle
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");

  // בדיקה שהאלמנטים קיימים
  if (!sidebarToggle) {
    console.error("sidebar-toggle button not found");
  }
  if (!sidebar) {
    console.error("sidebar element not found");
  }

  if (sidebarToggle && sidebar) {
    console.log("Sidebar toggle initialized successfully");
    
    // פונקציה לכיווץ/הרחבת התפריט
    function toggleSidebar(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log("Toggle button clicked");
      
      // בדיקה אם זה מובייל
      const isMobile = window.innerWidth <= 768;
      
      if (isMobile) {
        // במובייל - פתיחה/סגירה עם class "open"
        sidebar.classList.toggle("open");
    } else {
        // בדסקטופ - כיווץ/הרחבה
        sidebar.classList.toggle("collapsed");
        document.body.classList.toggle("sidebar-collapsed");
        
        // עדכון header
        const header = document.querySelector(".header");
        if (header) {
          const isCollapsed = sidebar.classList.contains("collapsed");
          if (isCollapsed) {
            header.classList.add("collapsed");
          } else {
            header.classList.remove("collapsed");
          }
        }
        
        // שמירת מצב ב-localStorage
        const isCollapsed = sidebar.classList.contains("collapsed");
        localStorage.setItem("sidebarCollapsed", isCollapsed);
    }
      
      console.log("Sidebar toggled, mobile:", isMobile);
    }

    // טעינת מצב שמור (רק בדסקטופ)
    const savedState = localStorage.getItem("sidebarCollapsed");
    if (savedState === "true" && window.innerWidth > 768) {
      sidebar.classList.add("collapsed");
      document.body.classList.add("sidebar-collapsed");
      const header = document.querySelector(".header");
      if (header) {
        header.classList.add("collapsed");
      }
      console.log("Loaded saved collapsed state");
    }

    // הוספת event listener לכפתור
    sidebarToggle.addEventListener("click", toggleSidebar);
    console.log("Event listener added to sidebar toggle");
    
    // במובייל - סגירת sidebar בלחיצה מחוץ לו
  if (window.innerWidth <= 768) {
      document.addEventListener("click", function(e) {
        if (sidebar && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
          sidebar.classList.remove("open");
        }
      });
    }
  } else {
    console.error("Failed to initialize sidebar toggle - missing elements");
  }

  // Mobile Menu Toggle
  const mobileMenuToggle = document.getElementById("mobile-menu-toggle");
  if (mobileMenuToggle && sidebar) {
    mobileMenuToggle.addEventListener("click", function(e) {
      e.preventDefault();
      e.stopPropagation();
      sidebar.classList.toggle("open");
    });
  }

  // ---------------------------------------------------------------------------
  // Flight Controller CONNECT/DISCONNECT
  // ---------------------------------------------------------------------------
  const connectBtn = document.getElementById("fc-connect-restart-btn");
  const disconnectBtn = document.getElementById("fc-disconnect-btn");
  const typeSelect = document.getElementById("fc-connection-type");
  const baudSelect = document.getElementById("fc-baud-select");

  // Initialize connect button text based on backend status
  async function initFcConnectButton() {
    if (!connectBtn) {
      return;
    }

    try {
      const response = await fetch("/flight-controller/api/flight-controller/status");
      if (!response.ok) {
        console.error("Failed to fetch FC status for connect button init");
        return;
      }
      const data = await response.json();

      // אם יש חיבור פעיל – הכפתור צריך להיות Restart, אחרת Connect
      if (data.connected) {
        connectBtn.textContent = "Restart";
      } else {
        connectBtn.textContent = "Connect";
      }
    } catch (err) {
      console.error("Error while initializing FC connect button:", err);
    }
  }

  // Initialize disconnect button state based on backend status
  async function initFcDisconnectButton() {
    if (!disconnectBtn) {
      return;
    }

    try {
      const response = await fetch("/flight-controller/api/flight-controller/status");
      if (!response.ok) {
        console.error("Failed to fetch FC status for disconnect button init");
        return;
      }
      const data = await response.json();

      // If the system is not connected, make the Disconnect button disabled and semi-transparent
      if (!data.connected) {
        disconnectBtn.disabled = true;
        disconnectBtn.style.opacity = "0.5";
        disconnectBtn.style.cursor = "not-allowed";
      } else {
        disconnectBtn.disabled = false;
        disconnectBtn.style.opacity = "";
        disconnectBtn.style.cursor = "";
      }
    } catch (err) {
      console.error("Error while initializing FC disconnect button:", err);
    }
  }

  async function fcConnect() {
    if (!connectBtn || !typeSelect || !baudSelect) {
      console.error("Flight Controller elements not found in DOM");
      return;
    }

    const connectionTypeValue = typeSelect.value; // "serial" or "usb"
    const baudrate = parseInt(baudSelect.value, 10);

    let device;
    if (connectionTypeValue === "serial") {
      device = "/dev/serial0";
    } else if (connectionTypeValue === "usb") {
      device = "/dev/ttyACM0";
    } else {
      console.error("Unknown connection type:", connectionTypeValue);
      return;
    }

    const payload = {
      connection_type: "serial", // backend always uses serial in this setup
      baudrate: baudrate,
      params: {
        device: device
      }
    };

    try {
      connectBtn.disabled = true;
      connectBtn.textContent = "Connecting...";

      const response = await fetch("/flight-controller/api/flight-controller/connect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        console.error("FC connect failed:", data);
        alert("Failed to connect to Flight Controller: " + (data.detail || "Unknown error"));
        // חיבור נכשל – נשאיר את הכפתור כ-Connect
        connectBtn.textContent = "Connect";
      } else {
        console.log("FC connected:", data);
        alert("Flight Controller connected successfully");
        // חיבור הצליח – מיד לשנות ל-Restart ולאפשר Disconnect
        connectBtn.textContent = "Restart";
        if (disconnectBtn) {
          disconnectBtn.disabled = false;
          disconnectBtn.style.opacity = "";
          disconnectBtn.style.cursor = "";
        }
      }
    } catch (err) {
      console.error("Error while connecting to Flight Controller:", err);
      alert("Error while connecting to Flight Controller: " + err);
      connectBtn.textContent = "Connect";
    } finally {
      connectBtn.disabled = false;
    }
  }

  async function fcDisconnect() {
    if (!disconnectBtn) {
      return;
    }

    try {
      disconnectBtn.disabled = true;
      disconnectBtn.textContent = "Disconnecting...";

      const response = await fetch("/flight-controller/api/flight-controller/disconnect", {
        method: "POST"
      });

      const data = await response.json();
      console.log("FC disconnected status:", data);
      alert("Flight Controller disconnected");

      // After successful disconnect, keep the button disabled and semi-transparent
      disconnectBtn.disabled = true;
      disconnectBtn.textContent = "Disconnect";
      disconnectBtn.style.opacity = "0.5";
      disconnectBtn.style.cursor = "not-allowed";

      // After disconnect, the connect button should go back to 'Connect'
      if (connectBtn) {
        connectBtn.textContent = "Connect";
      }
    } catch (err) {
      console.error("Error while disconnecting from Flight Controller:", err);
      alert("Error while disconnecting from Flight Controller: " + err);
      // On error, restore normal state so user can try again
      disconnectBtn.disabled = false;
      disconnectBtn.textContent = "Disconnect";
      disconnectBtn.style.opacity = "";
      disconnectBtn.style.cursor = "";
    }
  }

  if (connectBtn) {
    connectBtn.addEventListener("click", function (event) {
      event.preventDefault();
      fcConnect();
    });

    // Set initial label on page load (Connect / Restart)
    initFcConnectButton();
  }

  if (disconnectBtn) {
    disconnectBtn.addEventListener("click", function (event) {
      event.preventDefault();
      fcDisconnect();
    });

    // Set initial state on page load
    initFcDisconnectButton();
  }
});
