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

    document.addEventListener('click', function (e) {
      if (!navbar.contains(e.target)) {
        navbarNav.classList.remove('open');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- Search Modal + Live AJAX Suggestions ---------- */
  const searchModalOverlay = document.getElementById('searchModalOverlay');
  const searchModalBtn = document.getElementById('searchModalBtn');
  const searchModalClose = document.getElementById('searchModalClose');
  const searchModalInput = document.getElementById('searchModalInput');
  const searchResults = document.getElementById('searchResults');
  const quickLinks = document.getElementById('quickLinks');
  const searchSpinner = document.getElementById('searchSpinner');
  const searchEmpty = document.getElementById('searchEmpty');
  const SEARCH_URL = window.LEARNOVA_SEARCH_URL || '/api/search/';

  function openSearchModal() {
    if (!searchModalOverlay) return;
    searchModalOverlay.classList.add('open');
    if (searchModalInput) {
      setTimeout(function () { searchModalInput.focus(); }, 60);
    }
  }

  function closeSearchModal() {
    if (!searchModalOverlay) return;
    searchModalOverlay.classList.remove('open');
  }

  function showQuickLinks() {
    if (quickLinks) quickLinks.style.display = '';
    if (searchResults) searchResults.style.display = 'none';
    if (searchSpinner) searchSpinner.style.display = 'none';
    if (searchEmpty) searchEmpty.style.display = 'none';
  }

  function showResults(items) {
    if (quickLinks) quickLinks.style.display = 'none';
    if (searchSpinner) searchSpinner.style.display = 'none';
    if (!searchResults) return;

    if (!items.length) {
      searchResults.style.display = 'none';
      if (searchEmpty) searchEmpty.style.display = '';
      return;
    }

    if (searchEmpty) searchEmpty.style.display = 'none';
    searchResults.style.display = 'block';
    searchResults.innerHTML = '';

    const typeIcon = { topic: 'book', chapter: 'layer-group', lesson: 'file-lines' };

    items.forEach(function (item, idx) {
      const li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.dataset.url = item.url;
      li.innerHTML =
        '<a href="' + item.url + '" class="search-modal-suggestion-item search-result-item" tabindex="-1">' +
        '<i class="fa-solid fa-' + (typeIcon[item.type] || 'circle') + '" aria-hidden="true"></i>' +
        '<span class="search-result-body">' +
        '<span class="search-result-title">' + escapeHtml(item.title) + '</span>' +
        (item.meta ? '<span class="search-result-meta">' + escapeHtml(item.meta) + '</span>' : '') +
        '</span>' +
        '<span class="search-result-type">' + escapeHtml(item.type) + '</span>' +
        '</a>';
      searchResults.appendChild(li);
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  let searchDebounce;
  let activeIndex = -1;

  if (searchModalInput) {
    searchModalInput.addEventListener('input', function () {
      const q = searchModalInput.value.trim();
      activeIndex = -1;

      if (q.length < 2) {
        showQuickLinks();
        clearTimeout(searchDebounce);
        return;
      }

      if (searchSpinner) searchSpinner.style.display = '';
      if (quickLinks) quickLinks.style.display = 'none';
      if (searchResults) searchResults.style.display = 'none';
      if (searchEmpty) searchEmpty.style.display = 'none';

      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(function () {
        fetch(SEARCH_URL + '?q=' + encodeURIComponent(q))
          .then(function (r) { return r.json(); })
          .then(function (data) { showResults(data.results || []); })
          .catch(function () {
            if (searchSpinner) searchSpinner.style.display = 'none';
          });
      }, 250);
    });

    /* Keyboard navigation */
    searchModalInput.addEventListener('keydown', function (e) {
      const items = searchResults && searchResults.style.display !== 'none'
        ? Array.from(searchResults.querySelectorAll('a'))
        : [];

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, items.length - 1);
        if (items[activeIndex]) items[activeIndex].focus();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, -1);
        if (activeIndex === -1) searchModalInput.focus();
        else if (items[activeIndex]) items[activeIndex].focus();
      } else if (e.key === 'Enter') {
        if (activeIndex >= 0 && items[activeIndex]) {
          e.preventDefault();
          items[activeIndex].click();
        }
      }
    });
  }

  if (searchModalBtn) {
    searchModalBtn.addEventListener('click', openSearchModal);
  }

  if (searchModalClose) {
    searchModalClose.addEventListener('click', closeSearchModal);
  }

  if (searchModalOverlay) {
    searchModalOverlay.addEventListener('click', function (e) {
      if (e.target === searchModalOverlay) closeSearchModal();
    });
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeSearchModal();
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      openSearchModal();
    }
  });

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

  /* ---------- Reading Progress Bar (top of page) ---------- */
  const progressBar = document.getElementById('readingProgress');
  const lessonContentEl = document.getElementById('lessonContent');

  if (progressBar && lessonContentEl) {
    function updateProgress() {
      const contentTop = lessonContentEl.getBoundingClientRect().top + window.scrollY;
      const contentBottom = contentTop + lessonContentEl.offsetHeight;
      const windowBottom = window.scrollY + window.innerHeight;
      const total = contentBottom - contentTop;
      const progress = Math.min(100, Math.max(0, ((windowBottom - contentTop) / total) * 100));
      progressBar.style.width = progress + '%';
      progressBar.setAttribute('aria-valuenow', Math.round(progress));
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  }

})();
