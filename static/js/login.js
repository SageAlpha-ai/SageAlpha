// static/js/login.js
// Robust login script — posts form to /login (form-encoded) and handles JSON or HTML responses.
// Place this at static/js/login.js (overwrite existing).

(function () {
  // Elements
  const form = document.getElementById('loginForm');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const toggleBtn = document.getElementById('togglePassword');
  const signinBtn = document.getElementById('signinBtn');
  const errorBox = document.getElementById('loginError');

  // Defensive checks
  if (!form) {
    console.warn('login.js: login form not found, aborting script.');
    return;
  }

  // Ensure errorBox exists; if not, create one visually-hidden so script won't crash
  let localErrorBox = errorBox;
  if (!localErrorBox) {
    localErrorBox = document.createElement('div');
    localErrorBox.id = 'loginError';
    localErrorBox.className = 'form-error';
    localErrorBox.setAttribute('role','alert');
    localErrorBox.setAttribute('aria-live','polite');
    localErrorBox.hidden = true;
    form.insertBefore(localErrorBox, form.querySelector('button[type="submit"]') || null);
  }

  // Helper to show errors
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
      // keep focus
      passwordInput.focus();
      // visual class toggle optional
      toggleBtn.classList.toggle('visible', isHidden);
    });

    // small accessibility: Enter on toggle also toggles
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

  // Submit handler: post form-encoded to /login (robust fallback for HTML or JSON responses)
  form.addEventListener('submit', async (ev) => {
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

    // Build x-www-form-urlencoded body for maximum server compatibility
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    try {
      const resp = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: params.toString(),
        credentials: 'same-origin',
        redirect: 'follow'
      });

      // If server responds with JSON (API form): parse and react
      const contentType = (resp.headers.get('Content-Type') || '').toLowerCase();

      if (contentType.includes('application/json')) {
        const j = await resp.json().catch(() => ({}));
        if (resp.ok && (j.redirect || j.ok)) {
          // success — redirect
          window.location.href = j.redirect || '/';
          return;
        } else {
          const msg = j.error || j.message || 'Login failed. Please check your credentials.';
          showError(msg);
          setBusy(false);
          return;
        }
      }

      // If server returned HTML (typical server-rendered login page on failure or redirect on success)
      const text = await resp.text().catch(()=>'');

      // Heuristic: if the returned page contains a login form title -> login failed
      if (text.toLowerCase().includes('sign in to sagealpha') || text.toLowerCase().includes('sign in')) {
        // Try to extract server-side error message inside returned HTML (simple search)
        const m = text.match(/(?:<div[^>]*class="form-error"[^>]*>([\s\S]*?)<\/div>)/i);
        if (m && m[1]) {
          showError(m[1].replace(/<[^>]+>/g,'').trim());
        } else {
          showError('Invalid username or password.');
        }
        setBusy(false);
        return;
      }

      // Otherwise assume login succeeded or server redirected us; reload to current location
      // If server performed HTTP redirect, browser likely already followed; reload ensures we reach dashboard.
      window.location.reload();
    } catch (err) {
      console.error('login.js network error:', err);
      showError('Network or server error. Please try again.');
      setBusy(false);
    } finally {
      // ensure we clear busy state in timeout in case redirect didn't happen
      setTimeout(()=> setBusy(false), 2000);
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
