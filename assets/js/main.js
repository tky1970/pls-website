/**
 * PLS - Professional Logistics Service
 * Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
  // Initialize all modules
  initMobileMenu();
  initScrollHeader();
  initScrollAnimations();
  initSmoothScroll();
  initEmailObfuscation();
});

/**
 * Email Obfuscation for Spam Prevention
 */
function initEmailObfuscation() {
  const elements = document.querySelectorAll('.email-obfuscated');

  elements.forEach(el => {
    const user = el.getAttribute('data-user');
    const domain = el.getAttribute('data-domain');
    const type = el.getAttribute('data-type') || 'text';
    const subject = el.getAttribute('data-subject');

    if (user && domain) {
      const email = `${user}@${domain}`;

      if (type === 'link') {
        const link = document.createElement('a');
        let mailto = `mailto:${email}`;
        if (subject) {
          mailto += `?subject=${encodeURIComponent(subject)}`;
        }
        link.href = mailto;
        link.textContent = email;

        // Copy classes and styles if needed
        if (el.className) {
          link.className = el.className.replace('email-obfuscated', '').trim();
        }

        el.parentNode.replaceChild(link, el);
      } else {
        el.textContent = email;
      }
    }
  });
}

/**
 * Mobile Menu Toggle
 */
function initMobileMenu() {
  const menuToggle = document.querySelector('.menu-toggle');
  const navMobile = document.querySelector('.nav-mobile');
  const navOverlay = document.querySelector('.nav-overlay');
  const navLinks = document.querySelectorAll('.nav-mobile a');

  if (!menuToggle || !navMobile) return;

  function toggleMenu() {
    menuToggle.classList.toggle('active');
    navMobile.classList.toggle('active');
    navOverlay.classList.toggle('active');
    document.body.style.overflow = navMobile.classList.contains('active') ? 'hidden' : '';
  }

  function closeMenu() {
    menuToggle.classList.remove('active');
    navMobile.classList.remove('active');
    navOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  menuToggle.addEventListener('click', toggleMenu);
  navOverlay.addEventListener('click', closeMenu);
  navLinks.forEach(link => link.addEventListener('click', closeMenu));
}

/**
 * Header Scroll Effect
 */
function initScrollHeader() {
  const header = document.querySelector('.header');
  if (!header) return;

  let lastScroll = 0;

  window.addEventListener('scroll', function () {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }

    lastScroll = currentScroll;
  });
}

/**
 * Scroll Animations (Fade In)
 */
function initScrollAnimations() {
  const elements = document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right');

  if (!elements.length) return;

  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  elements.forEach(el => observer.observe(el));
}

/**
 * Smooth Scroll for Anchor Links
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');

      if (targetId === '#') return;

      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        e.preventDefault();
        const headerHeight = document.querySelector('.header').offsetHeight;
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

/**
 * Counter Animation (Optional - for stats)
 */
function animateCounter(element, target, duration = 2000) {
  let start = 0;
  const increment = target / (duration / 16);

  function updateCounter() {
    start += increment;
    if (start < target) {
      element.textContent = Math.floor(start);
      requestAnimationFrame(updateCounter);
    } else {
      element.textContent = target;
    }
  }

  updateCounter();
}
