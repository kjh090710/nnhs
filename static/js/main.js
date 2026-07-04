const body = document.body;
body.classList.add('js-ready');

const sidebar = document.querySelector('#sidebar');
const toggleButtons = document.querySelectorAll('[data-menu-toggle]');
const desktopQuery = window.matchMedia('(min-width: 1081px)');

function getCookie(name) {
  const cookies = document.cookie.split(';').map((cookie) => cookie.trim());

  for (const cookie of cookies) {
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(cookie.split('=')[1]);
    }
  }

  return null;
}

function setCookie(name, value) {
  const maxAge = 60 * 60 * 24 * 365;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

function saveSidebarState(isCollapsed) {
  localStorage.setItem('sidebar-collapsed', String(isCollapsed));
  setCookie('sidebar_collapsed', String(isCollapsed));
}

function getSavedSidebarState() {
  const cookieValue = getCookie('sidebar_collapsed');

  if (cookieValue === 'true') return true;
  if (cookieValue === 'false') return false;

  const localValue = localStorage.getItem('sidebar-collapsed');

  if (localValue === 'true') return true;
  if (localValue === 'false') return false;

  return false;
}

function applySidebarState() {
  if (!desktopQuery.matches) {
    body.classList.remove('sidebar-collapsed');
    return;
  }

  const isCollapsed = getSavedSidebarState();
  body.classList.toggle('sidebar-collapsed', isCollapsed);
}

function toggleSidebar(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }

  if (desktopQuery.matches) {
    const nextState = !body.classList.contains('sidebar-collapsed');
    body.classList.toggle('sidebar-collapsed', nextState);
    saveSidebarState(nextState);
    return;
  }

  body.classList.toggle('menu-open');
}

toggleButtons.forEach((button) => {
  button.addEventListener('click', toggleSidebar);
});

document.querySelectorAll('.nav-item').forEach((item) => {
  item.addEventListener('click', () => {
    if (desktopQuery.matches) {
      saveSidebarState(body.classList.contains('sidebar-collapsed'));
    }
  });
});

document.addEventListener('click', (event) => {
  if (!sidebar || !body.classList.contains('menu-open')) return;

  const clickedToggle = Array.from(toggleButtons).some((button) => {
    return button.contains(event.target);
  });

  if (sidebar.contains(event.target) || clickedToggle) return;

  body.classList.remove('menu-open');
});

if (typeof desktopQuery.addEventListener === 'function') {
  desktopQuery.addEventListener('change', () => {
    body.classList.remove('menu-open');
    applySidebarState();
  });
} else {
  desktopQuery.addListener(() => {
    body.classList.remove('menu-open');
    applySidebarState();
  });
}

applySidebarState();

const progressBar = document.querySelector('.scroll-progress');

function updateScrollProgress() {
  if (!progressBar) return;

  const scrollTop = window.scrollY;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const progress = docHeight <= 0 ? 0 : (scrollTop / docHeight) * 100;

  progressBar.style.width = `${progress}%`;
}

window.addEventListener('scroll', updateScrollProgress, { passive: true });
window.addEventListener('resize', updateScrollProgress);
updateScrollProgress();

const revealTargets = document.querySelectorAll(
  '.hero-card, .metric-card, .panel, .finding-card, .process-list div, .predictor-panel, .ozone-card'
);

revealTargets.forEach((el, index) => {
  el.classList.add('reveal');
  el.style.transitionDelay = `${Math.min(index * 24, 160)}ms`;
});

if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      revealObserver.unobserve(entry.target);
    });
  }, {
    threshold: 0.02,
    rootMargin: '0px 0px -20px 0px'
  });

  revealTargets.forEach((el) => revealObserver.observe(el));

  setTimeout(() => {
    revealTargets.forEach((el) => {
      el.classList.add('is-visible');
    });
  }, 450);
} else {
  revealTargets.forEach((el) => {
    el.classList.add('is-visible');
  });
}

const modal = document.querySelector('[data-image-modal]');
const modalImage = modal ? modal.querySelector('img') : null;
const modalClose = document.querySelector('[data-modal-close]');

document.querySelectorAll('.panel img, .chart-card img').forEach((img) => {
  img.addEventListener('click', () => {
    if (!modal || !modalImage) return;

    modalImage.src = img.src;
    modalImage.alt = img.alt || '확대된 그래프';
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    body.style.overflow = 'hidden';
  });
});

function closeModal() {
  if (!modal || !modalImage) return;

  modal.classList.remove('is-open');
  modal.setAttribute('aria-hidden', 'true');
  modalImage.src = '';
  body.style.overflow = '';
}

if (modalClose) {
  modalClose.addEventListener('click', closeModal);
}

if (modal) {
  modal.addEventListener('click', (event) => {
    if (event.target === modal) closeModal();
  });
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeModal();
    body.classList.remove('menu-open');
  }
});

document.querySelectorAll('.table-wrap').forEach((wrap) => {
  const table = wrap.querySelector('table');
  if (!table) return;

  if (wrap.previousElementSibling && wrap.previousElementSibling.classList.contains('table-tools')) {
    return;
  }

  const tools = document.createElement('div');
  tools.className = 'table-tools';

  const input = document.createElement('input');
  input.className = 'table-search';
  input.type = 'search';
  input.placeholder = '표 내용 검색';
  input.setAttribute('aria-label', '표 내용 검색');

  tools.appendChild(input);
  wrap.parentNode.insertBefore(tools, wrap);

  input.addEventListener('input', () => {
    const keyword = input.value.trim().toLowerCase();
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(keyword) ? '' : 'none';
    });
  });
});