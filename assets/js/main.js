/* White Tank Water Restoration · main.js */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear();
  });

  const menuBtn = document.querySelector(".menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener("click", () => {
      const open = menuBtn.getAttribute("aria-expanded") === "true";
      menuBtn.setAttribute("aria-expanded", String(!open));
      mobileMenu.classList.toggle("is-open", !open);
    });
  }

  const toggles = document.querySelectorAll(".nav-toggle-sub");
  const closeAll = (except) => {
    toggles.forEach((t) => {
      if (t === except) return;
      t.setAttribute("aria-expanded", "false");
      const menu = document.getElementById(t.getAttribute("aria-controls"));
      if (menu) menu.classList.remove("is-open");
    });
  };
  toggles.forEach((btn) => {
    const menu = document.getElementById(btn.getAttribute("aria-controls"));
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = btn.getAttribute("aria-expanded") === "true";
      closeAll(btn);
      btn.setAttribute("aria-expanded", String(!open));
      if (menu) menu.classList.toggle("is-open", !open);
    });
  });
  document.addEventListener("click", () => closeAll());
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAll();
  });

  const here = location.pathname.replace(/index\.html$/, "");
  document.querySelectorAll(".side-links a, .nav-link").forEach((a) => {
    if (a.getAttribute("href") === here) a.setAttribute("aria-current", "page");
  });

  const toc = document.querySelector("[data-toc]");
  const prose = document.querySelector(".prose");
  if (toc && prose) {
    const list = document.createElement("ol");
    prose.querySelectorAll("h2").forEach((h, i) => {
      if (!h.id) h.id = "section-" + (i + 1);
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);
      list.appendChild(li);
    });
    toc.appendChild(list);
  }

  document.querySelectorAll(".media img").forEach((img) => {
    const mark = () => img.closest(".media").classList.add("is-missing");
    if (img.complete && img.naturalWidth === 0) mark();
    img.addEventListener("error", mark);
  });
});
