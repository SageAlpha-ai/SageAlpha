# auth.py (minimal blueprint: only logout/profile helpers)
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import logout_user

# blueprint name 'auth' is fine for namespacing other auth routes if you add them later
auth = Blueprint('auth', __name__, template_folder='templates')

# NOTE:
# This file intentionally does NOT define a /login view.
# Leave /login implemented at top-level in app.py to avoid duplicate routes/conflicts.

# Logout route — supports GET and POST and always redirects to /login
@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear Flask-Login state if used
    try:
        logout_user()
    except Exception:
        pass

    # Clear session (all user state)
    session.clear()

    # If request is AJAX (JS), return JSON with top-level login URL
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Use the top-level 'login' endpoint (implemented in app.py)
        return jsonify({"success": True, "next": url_for('login')})

    # Normal flow: redirect to top-level login page
    return redirect(url_for('login'))

# Example optional profile route — returns simple rendered page if you implement it.
@auth.route('/profile', methods=['GET'])
def profile():
    # If not logged in, redirect to login
    # (you can replace this logic with flask-login @login_required if you prefer)
    if not session.get('user') and not (hasattr(__import__('flask_login').login.current_user, 'is_authenticated') and __import__('flask_login').login.current_user.is_authenticated):
        return redirect(url_for('login'))
    # Render a simple profile page if you have templates/profile.html
    try:
        return render_template('profile.html')
    except Exception:
        # fallback: return JSON / simple text so missing template doesn't crash things
        return jsonify({"profile": session.get('user', 'Guest')}), 200
