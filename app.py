from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'change_this_to_a_strong_secret_key'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

DATABASE = 'assets.db'


# ---------------------------
# Database helper function
# ---------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------
# User class
# ---------------------------
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = str(id)
        self.username = username
        self.password_hash = password_hash


# ---------------------------
# Flask-Login user loader
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    if user:
        return User(user["id"], user["username"], user["password_hash"])
    return None


# ---------------------------
# Asset database functions
# ---------------------------
def insert_asset(name, asset_type, owner, ip_address, os):
    conn = get_db_connection()
    conn.execute(
        '''
        INSERT INTO assets (name, asset_type, owner, ip_address, os)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (name, asset_type, owner, ip_address, os)
    )
    conn.commit()
    conn.close()


def get_all_assets():
    conn = get_db_connection()
    assets = conn.execute("SELECT * FROM assets").fetchall()
    conn.close()
    return assets


def get_asset_by_id(asset_id):
    conn = get_db_connection()
    asset = conn.execute(
        "SELECT * FROM assets WHERE id = ?",
        (asset_id,)
    ).fetchone()
    conn.close()
    return asset


def update_asset(asset_id, name, asset_type, owner, ip_address, os):
    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE assets
        SET name = ?, asset_type = ?, owner = ?, ip_address = ?, os = ?
        WHERE id = ?
        ''',
        (name, asset_type, owner, ip_address, os, asset_id)
    )
    conn.commit()
    conn.close()


def delete_asset(asset_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM assets WHERE id = ?",
        (asset_id,)
    )
    conn.commit()
    conn.close()


# ---------------------------
# Home route
# ---------------------------
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('view_assets'))
    return redirect(url_for('login'))


# ---------------------------
# Register route
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists. Please choose another one.", "warning")
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------------------
# Login route
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            login_user(User(user["id"], user["username"], user["password_hash"]))
            flash("Login successful!", "success")
            return redirect(url_for('view_assets'))
        else:
            flash("Invalid username or password. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------------------------
# Logout route
# ---------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# ---------------------------
# Register asset route
# ---------------------------
@app.route('/register_asset', methods=['GET', 'POST'])
@login_required
def register_asset():
    if request.method == 'POST':
        name = request.form['name'].strip()
        asset_type = request.form['type'].strip()
        owner = request.form['owner'].strip()
        ip_address = request.form['ip_address'].strip()
        os = request.form['os'].strip()

        if not name or not asset_type or not owner or not ip_address or not os:
            flash("All asset fields are required.", "danger")
            return redirect(url_for('register_asset'))

        insert_asset(name, asset_type, owner, ip_address, os)
        flash('Asset registered successfully!', 'success')
        return redirect(url_for('view_assets'))

    return render_template('register_asset.html')


# ---------------------------
# View assets route
# ---------------------------
@app.route('/view_assets')
@login_required
def view_assets():
    assets = get_all_assets()
    return render_template('view_assets.html', assets=assets)


# ---------------------------
# Edit asset route
# ---------------------------
@app.route('/edit_asset/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    asset = get_asset_by_id(asset_id)

    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for('view_assets'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        asset_type = request.form['type'].strip()
        owner = request.form['owner'].strip()
        ip_address = request.form['ip_address'].strip()
        os = request.form['os'].strip()

        if not name or not asset_type or not owner or not ip_address or not os:
            flash("All asset fields are required.", "danger")
            return redirect(url_for('edit_asset', asset_id=asset_id))

        update_asset(asset_id, name, asset_type, owner, ip_address, os)
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('view_assets'))

    return render_template('edit_asset.html', asset=asset)


# ---------------------------
# Delete asset route
# ---------------------------
@app.route('/delete_asset/<int:asset_id>', methods=['POST'])
@login_required
def delete_asset_route(asset_id):
    asset = get_asset_by_id(asset_id)

    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for('view_assets'))

    delete_asset(asset_id)
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('view_assets'))


if __name__ == '__main__':
    app.run(debug=True)