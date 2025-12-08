// static/js/login.js
// Handles login via fetch + toggling between Sign-in and Sign-up views.

(function () {
  // Elements
  const loginForm     = document.getElementById('loginForm');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const toggleBtn     = document.getElementById('togglePassword');
  const signinBtn     = document.getElementById('signinBtn');
  const errorBox      = document.getElementById('loginError');

  const registerForm  = document.getElementById('registerForm');
  const showRegister  = document.getElementById('showRegister');
  const showLogin     = document.getElementById('showLogin');

  // Defensive checks
  if (!loginForm) {
    console.warn('login.js: login form not found, aborting script.');
    return;
  }

  // Ensure errorBox exists; if not, create one so script won't crash
  let localErrorBox = errorBox;
  if (!localErrorBox) {
    localErrorBox = document.createElement('div');
    localErrorBox.id = 'loginError';
    localErrorBox.className = 'form-error';
    localErrorBox.setAttribute('role', 'alert');
    localErrorBox.setAttribute('aria-live', 'polite');
    localErrorBox.hidden = true;
    loginForm.insertBefore(localErrorBox, loginForm.querySelector('button[type="submit"]') || null);
  }

  // --- View toggling between login / register ---

  function showLoginView() {
    if (loginForm)    loginForm.hidden = false;
    if (registerForm) registerForm.hidden = true;
    const titleEl = document.getElementById('loginTitle');
    if (titleEl) titleEl.textContent = 'Sign in to SageAlpha';
  }

  function showRegisterView() {
    if (loginForm)    loginForm.hidden = true;
    if (registerForm) registerForm.hidden = false;
    const titleEl = document.getElementById('loginTitle');
    if (titleEl) titleEl.textContent = 'Create your SageAlpha account';
  }

  if (showRegister && registerForm) {
    showRegister.addEventListener('click', (e) => {
      e.preventDefault();
      showRegisterView();
    });
  }

  if (showLogin && registerForm) {
    showLogin.addEventListener('click', (e) => {
      e.preventDefault();
      showLoginView();
    });
  }

  // If server rendered with show_register=True, the template already set hidden attrs.
  // No extra JS needed on load.

  // --- Helpers for login error handling ---

  function showError(msg) {
    localErrorBox.textContent = msg;
    localErrorBox.hidden = false;
    localErrorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  function hideError() {
    localErrorBox.hidden = true;
    localErrorBox.textContent = '';
  }

  // Toggle password visibility (if toggle present)
  if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const isHidden = passwordInput.type === 'password';
      passwordInput.type = isHidden ? 'text' : 'password';
      toggleBtn.setAttribute('aria-pressed', isHidden ? 'true' : 'false');
      toggleBtn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
      passwordInput.focus();
      toggleBtn.classList.toggle('visible', isHidden);
    });

    toggleBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleBtn.click();
      }
    });
  }

  // Disable/enable signin button with accessible state
  function setBusy(isBusy) {
    if (signinBtn) {
      signinBtn.disabled = !!isBusy;
      if (isBusy) {
        signinBtn.setAttribute('aria-busy', 'true');
      } else {
        signinBtn.removeAttribute('aria-busy');
      }
    }
  }

  // Submit handler: post form-encoded to /login
  loginForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    hideError();
    setBusy(true);

    const username = (usernameInput && usernameInput.value || '').trim();
    const password = (passwordInput && passwordInput.value) || '';

    if (!username || !password) {
      showError('Username and password are required.');
      setBusy(false);
      return;
    }

    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    try {
      const resp = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params.toString(),
        credentials: 'same-origin',
        redirect: 'follow'
      });

      const contentType = (resp.headers.get('Content-Type') || '').toLowerCase();

      if (contentType.includes('application/json')) {
        const j = await resp.json().catch(() => ({}));
        if (resp.ok && (j.redirect || j.ok)) {
          window.location.href = j.redirect || '/';
          return;
        } else {
          const msg = j.error || j.message || 'Login failed. Please check your credentials.';
          showError(msg);
          setBusy(false);
          return;
        }
      }

      const text = await resp.text().catch(() => '');

      if (text.toLowerCase().includes('sign in to sagealpha') || text.toLowerCase().includes('sign in')) {
        const m = text.match(/(?:<div[^>]*id="loginError"[^>]*>([\s\S]*?)<\/div>)/i);
        if (m && m[1]) {
          showError(m[1].replace(/<[^>]+>/g, '').trim());
        } else {
          showError('Invalid username or password.');
        }
        setBusy(false);
        return;
      }

      window.location.reload();
    } catch (err) {
      console.error('login.js network error:', err);
      showError('Network or server error. Please try again.');
      setBusy(false);
    } finally {
      setTimeout(() => setBusy(false), 2000);
    }
  });

  // small convenience: allow Ctrl/Alt+M to toggle password while focus on password input
  passwordInput?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.altKey) && (e.key === 'm' || e.key === 'M')) {
      e.preventDefault();
      toggleBtn?.click();
    }
  });
})();
