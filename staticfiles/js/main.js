/* ============================================================
   Learnova — Main JavaScript
   ============================================================ */

(function () {
  'use strict';

  /* ---------- Theme ---------- */
  const THEME_KEY = 'learnova-theme';
  const html = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');

  function applyTheme(theme) {
    html.setAttribute('data-theme', theme);
    if (themeIcon) {
      themeIcon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
    localStorage.setItem(THEME_KEY, theme);
  }

  // Init theme from localStorage
  const savedTheme = localStorage.getItem(THEME_KEY) ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  applyTheme(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const current = html.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  /* ---------- Navbar Scroll Shadow ---------- */
  const navbar = document.getElementById('navbar');
  if (navbar) {
    function updateNavbar() {
      navbar.classList.toggle('scrolled', window.scrollY > 10);
    }
    window.addEventListener('scroll', updateNavbar, { passive: true });
    updateNavbar();
  }

  /* ---------- Mobile Hamburger ---------- */
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const navbarNav = document.getElementById('navbarNav');

  if (hamburgerBtn && navbarNav) {
    hamburgerBtn.addEventListener('click', function () {
      const open = navbarNav.classList.toggle('open');
      hamburgerBtn.setAttribute('aria-expanded', String(open));
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!navbar.contains(e.target)) {
        navbarNav.classList.remove('open');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- Back to Top ---------- */
  const backToTop = document.getElementById('backToTop');
  if (backToTop) {
    window.addEventListener('scroll', function () {
      backToTop.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });

    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- Copy Code Buttons ---------- */
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const code = btn.getAttribute('data-code') ||
        btn.closest('.code-block')?.querySelector('code')?.textContent || '';

      navigator.clipboard.writeText(code).then(function () {
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
          btn.classList.remove('copied');
        }, 2000);
      }).catch(function () {
        // Fallback for older browsers
        const ta = document.createElement('textarea');
        ta.value = code;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
          btn.classList.remove('copied');
        }, 2000);
      });
    });
  });

  /* ---------- Filter Buttons (Topics page) ---------- */
  document.querySelectorAll('.filter-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  /* ---------- Newsletter Form Feedback ---------- */
  document.querySelectorAll('.newsletter-form, .newsletter-inline').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      const btn = form.querySelector('button[type="submit"]');
      if (!input || !input.value.trim()) return;
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-check"></i> Subscribed!';
      btn.disabled = true;
      input.value = '';
      setTimeout(function () {
        btn.innerHTML = orig;
        btn.disabled = false;
      }, 3000);
    });
  });

  /* ---------- Smooth Scroll for Internal Anchors ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      const id = a.getAttribute('href').slice(1);
      const el = document.getElementById(id);
      if (el) {
        e.preventDefault();
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ---------- Active TOC Highlight on Scroll ---------- */
  const tocLinks = document.querySelectorAll('#tocList a[href^="#"]');
  if (tocLinks.length) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          tocLinks.forEach(l => l.classList.remove('toc-active'));
          const active = document.querySelector('#tocList a[href="#' + entry.target.id + '"]');
          if (active) active.classList.add('toc-active');
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });

    document.querySelectorAll('.lesson-content h2, .lesson-content h3').forEach(function (h) {
      observer.observe(h);
    });
  }

  /* ---------- Reading Progress Bar ---------- */
  const progressBar = document.getElementById('readingProgress');
  const lessonContent = document.getElementById('lessonContent');

  if (progressBar && lessonContent) {
    function updateProgress() {
      const contentTop = lessonContent.getBoundingClientRect().top + window.scrollY;
      const contentBottom = contentTop + lessonContent.offsetHeight;
      const windowBottom = window.scrollY + window.innerHeight;
      const total = contentBottom - contentTop;
      const progress = Math.min(100, Math.max(0, ((windowBottom - contentTop) / total) * 100));
      progressBar.style.width = progress + '%';
      progressBar.setAttribute('aria-valuenow', Math.round(progress));
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  }

  /* ---------- Smooth Anchor Scroll with Navbar Offset ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const id = anchor.getAttribute('href').slice(1);
      if (!id) return;
      const el = document.getElementById(id);
      if (el) {
        e.preventDefault();
        const navH = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-h') || '66', 10);
        const top = el.getBoundingClientRect().top + window.scrollY - navH - 16;
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
      }
    });
  });

})();
