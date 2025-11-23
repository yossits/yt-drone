// Theme Toggle
document.addEventListener("DOMContentLoaded", function () {
  const themeToggle = document.getElementById("theme-toggle");
  const body = document.body;

  // בדיקה אם יש theme שמור ב-localStorage
  const savedTheme = localStorage.getItem("theme") || "light";
  if (savedTheme === "dark") {
    body.classList.remove("theme-light");
    body.classList.add("theme-dark");
    themeToggle.querySelector("span").textContent = "☀️";
  }

  // טוגל נושא
  themeToggle.addEventListener("click", function () {
    const isDark = body.classList.contains("theme-dark");

    if (isDark) {
      body.classList.remove("theme-dark");
      body.classList.add("theme-light");
      themeToggle.querySelector("span").textContent = "🌙";
      localStorage.setItem("theme", "light");
    } else {
      body.classList.remove("theme-light");
      body.classList.add("theme-dark");
      themeToggle.querySelector("span").textContent = "☀️";
      localStorage.setItem("theme", "dark");
    }
  });

  // Language Toggle (רק UI בשלב זה)
  const langToggle = document.getElementById("lang-toggle");
  langToggle.addEventListener("click", function () {
    // בעתיד: לוגיקה אמיתית לשינוי שפה
    console.log("Language toggle clicked");
  });

  // Mobile Sidebar Toggle (אם נדרש)
  const sidebar = document.querySelector(".sidebar");
  if (window.innerWidth <= 768) {
    // לוגיקה למובייל בעתיד
  }
});
