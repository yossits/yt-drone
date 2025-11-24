// Theme Selector
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

  // Language Toggle (רק UI בשלב זה)
  const langToggle = document.getElementById("lang-toggle");
  langToggle.addEventListener("click", function () {
    // בעתיד: לוגיקה אמיתית לשינוי שפה
    console.log("Language toggle clicked");
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
      
      sidebar.classList.toggle("collapsed");
      document.body.classList.toggle("sidebar-collapsed");
      
      // שמירת מצב ב-localStorage
      const isCollapsed = sidebar.classList.contains("collapsed");
      localStorage.setItem("sidebarCollapsed", isCollapsed);
      
      // עדכון header
      const header = document.querySelector(".header");
      if (header) {
        if (isCollapsed) {
          header.classList.add("collapsed");
        } else {
          header.classList.remove("collapsed");
        }
      }
      
      console.log("Sidebar collapsed:", isCollapsed);
    }

    // טעינת מצב שמור
    const savedState = localStorage.getItem("sidebarCollapsed");
    if (savedState === "true") {
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
  } else {
    console.error("Failed to initialize sidebar toggle - missing elements");
  }
});
