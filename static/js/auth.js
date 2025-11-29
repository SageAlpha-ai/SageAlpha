// static/js/auth.js
document.getElementById("loginBtn").addEventListener("click", async () => {
  const u = document.getElementById("username").value.trim();
  const p = document.getElementById("password").value;

  const errEl = document.getElementById("loginError");
  errEl.hidden = true;

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });
    const j = await res.json().catch(()=>({ok:false, message:"Invalid response"}));
    if (!res.ok || !j.ok) {
      errEl.textContent = j.message || "Login failed";
      errEl.hidden = false;
      // subtle shake animation
      const card = document.querySelector(".login-card");
      card && card.classList.add("shake");
      setTimeout(()=> card && card.classList.remove("shake"), 420);
      return;
    }
    // smooth fade + nav
    document.querySelector(".login-card").style.transition = "opacity .25s ease, transform .25s ease";
    document.querySelector(".login-card").style.opacity = 0;
    document.querySelector(".login-card").style.transform = "translateY(-8px)";
    setTimeout(()=> { window.location.href = j.redirect || "/"; }, 260);
  } catch (e) {
    errEl.textContent = "Network error";
    errEl.hidden = false;
  }
});
