from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import io
import nmap
import mysql.connector
from mysql.connector import Error
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from database import DB_CONFIG


app = Flask(__name__)
app.secret_key = 'change_this_to_a_strong_secret_key'


# ---------------------------
# Flask-Login setup
# ---------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


# ---------------------------
# Database helper function
# ---------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None


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

    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return User(user["id"], user["username"], user["password_hash"])

    return None


# ---------------------------
# Asset database functions
# ---------------------------
def insert_asset(name, asset_type, owner, ip_address, os, criticality="Medium"):
    conn = get_db_connection()

    if conn is None:
        return False

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO assets (name, asset_type, owner, ip_address, os, criticality, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (name, asset_type, owner, ip_address, os, criticality, current_user.id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return True


def get_all_assets():
    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM assets
        ORDER BY created_at DESC
    """)

    assets = cursor.fetchall()

    cursor.close()
    conn.close()

    return assets


def search_assets(search_term):
    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM assets
        WHERE name LIKE %s
        OR asset_type LIKE %s
        OR owner LIKE %s
        OR ip_address LIKE %s
        OR os LIKE %s
        OR criticality LIKE %s
        ORDER BY created_at DESC
    """

    wildcard_term = f"%{search_term}%"

    cursor.execute(
        query,
        (
            wildcard_term,
            wildcard_term,
            wildcard_term,
            wildcard_term,
            wildcard_term,
            wildcard_term
        )
    )

    assets = cursor.fetchall()

    cursor.close()
    conn.close()

    return assets


def get_asset_by_id(asset_id):
    conn = get_db_connection()

    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM assets WHERE id = %s",
        (asset_id,)
    )

    asset = cursor.fetchone()

    cursor.close()
    conn.close()

    return asset


def get_asset_by_ip(ip_address):
    conn = get_db_connection()

    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM assets WHERE ip_address = %s LIMIT 1",
        (ip_address,)
    )

    asset = cursor.fetchone()

    cursor.close()
    conn.close()

    return asset


def update_asset(asset_id, name, asset_type, owner, ip_address, os, criticality):
    conn = get_db_connection()

    if conn is None:
        return False

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE assets
        SET name = %s,
            asset_type = %s,
            owner = %s,
            ip_address = %s,
            os = %s,
            criticality = %s
        WHERE id = %s
        """,
        (name, asset_type, owner, ip_address, os, criticality, asset_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return True


def delete_asset(asset_id):
    conn = get_db_connection()

    if conn is None:
        return False

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM assets WHERE id = %s",
        (asset_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return True


def insert_asset_service(asset_id, port, protocol, service_name, service_version, product):
    conn = get_db_connection()

    if conn is None:
        return False

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO asset_services 
        (asset_id, port, protocol, service_name, service_version, product)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (asset_id, port, protocol, service_name, service_version, product)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return True


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

        if conn is None:
            flash("Database connection failed.", "danger")
            return redirect(url_for('register'))

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            flash("Username already exists. Please choose another one.", "warning")
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )

        conn.commit()
        cursor.close()
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

        if conn is None:
            flash("Database connection failed.", "danger")
            return redirect(url_for('login'))

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            login_user(User(user["id"], user["username"], user["password_hash"]))
            flash("Login successful!", "success")
            return redirect(url_for('view_assets'))

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
        criticality = request.form.get('criticality', 'Medium').strip()

        if not name or not asset_type or not owner or not ip_address:
            flash("Name, asset type, owner, and IP address are required.", "danger")
            return redirect(url_for('register_asset'))

        success = insert_asset(name, asset_type, owner, ip_address, os, criticality)

        if success:
            flash('Asset registered successfully!', 'success')
            return redirect(url_for('view_assets'))

        flash("Failed to register asset.", "danger")
        return redirect(url_for('register_asset'))

    return render_template('register_asset.html')


# ---------------------------
# CSV upload route
# ---------------------------
@app.route('/upload_csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part found.", "danger")
            return redirect(url_for('upload_csv'))

        file = request.files['file']

        if file.filename == '':
            flash("Please choose a CSV file.", "warning")
            return redirect(url_for('upload_csv'))

        if not file.filename.lower().endswith('.csv'):
            flash("Only CSV files are allowed.", "danger")
            return redirect(url_for('upload_csv'))

        try:
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)

            required_columns = ['name', 'asset_type', 'owner', 'ip_address', 'os']

            if csv_reader.fieldnames is None:
                flash("CSV file is empty or invalid.", "danger")
                return redirect(url_for('upload_csv'))

            missing_columns = [col for col in required_columns if col not in csv_reader.fieldnames]

            if missing_columns:
                flash(f"Missing required columns: {', '.join(missing_columns)}", "danger")
                return redirect(url_for('upload_csv'))

            count = 0

            for row in csv_reader:
                name = row['name'].strip()
                asset_type = row['asset_type'].strip()
                owner = row['owner'].strip()
                ip_address = row['ip_address'].strip()
                os_name = row['os'].strip()
                criticality = row.get('criticality', 'Medium').strip() or 'Medium'

                if name and asset_type and owner and ip_address:
                    success = insert_asset(
                        name,
                        asset_type,
                        owner,
                        ip_address,
                        os_name,
                        criticality
                    )

                    if success:
                        count += 1

            flash(f"{count} assets uploaded successfully!", "success")
            return redirect(url_for('view_assets'))

        except Exception as e:
            flash(f"Error processing CSV file: {str(e)}", "danger")
            return redirect(url_for('upload_csv'))

    return render_template('upload_csv.html')


# ---------------------------
# View assets route
# ---------------------------
@app.route('/view_assets', methods=['GET', 'POST'])
@login_required
def view_assets():
    if request.method == 'POST':
        search_term = request.form['search'].strip()
        assets = search_assets(search_term)

        if not assets:
            flash("No matching assets found.", "warning")

        return render_template(
            'view_assets.html',
            assets=assets,
            search_term=search_term
        )

    assets = get_all_assets()

    return render_template(
        'view_assets.html',
        assets=assets,
        search_term=''
    )


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
        criticality = request.form.get('criticality', 'Medium').strip()

        if not name or not asset_type or not owner or not ip_address:
            flash("Name, asset type, owner, and IP address are required.", "danger")
            return redirect(url_for('edit_asset', asset_id=asset_id))

        success = update_asset(
            asset_id,
            name,
            asset_type,
            owner,
            ip_address,
            os,
            criticality
        )

        if success:
            flash('Asset updated successfully!', 'success')
            return redirect(url_for('view_assets'))

        flash("Failed to update asset.", "danger")
        return redirect(url_for('edit_asset', asset_id=asset_id))

    return render_template('edit_asset.html', asset=asset)


# ---------------------------
# Network scan route
# ---------------------------
@app.route('/network_scan', methods=['GET', 'POST'])
@login_required
def network_scan():
    if request.method == 'POST':
        target_range = request.form['target_range'].strip()
        scan_type = request.form.get('scan_type', 'quick')

        if not target_range:
            flash("Please enter a target IP address or network range.", "danger")
            return redirect(url_for('network_scan'))

        try:
            scanner = nmap.PortScanner()

            if scan_type == "quick":
                scan_arguments = "-sn -T4"
            else:
                scan_arguments = "-sV -T4"

            scanner.scan(hosts=target_range, arguments=scan_arguments)

            discovered_count = 0
            duplicate_count = 0
            service_count = 0

            for host in scanner.all_hosts():
                host_state = scanner[host].state()

                if host_state != "up":
                    continue

                ip_address = host
                existing_asset = get_asset_by_ip(ip_address)

                if existing_asset:
                    asset_id = existing_asset["id"]
                    duplicate_count += 1
                else:
                    os_name = "Unknown"
                    asset_name = f"Discovered Host - {host}"
                    asset_type = "Network Device"
                    owner = "Unassigned"
                    criticality = "Medium"

                    success = insert_asset(
                        asset_name,
                        asset_type,
                        owner,
                        ip_address,
                        os_name,
                        criticality
                    )

                    if not success:
                        continue

                    discovered_count += 1

                    new_asset = get_asset_by_ip(ip_address)

                    if not new_asset:
                        continue

                    asset_id = new_asset["id"]

                if scan_type == "detailed":
                    for protocol in scanner[host].all_protocols():
                        ports = scanner[host][protocol].keys()

                        for port in ports:
                            port_data = scanner[host][protocol][port]

                            service_name = port_data.get('name', 'unknown')
                            product = port_data.get('product', '')
                            service_version = port_data.get('version', '')

                            service_saved = insert_asset_service(
                                asset_id,
                                port,
                                protocol,
                                service_name,
                                service_version,
                                product
                            )

                            if service_saved:
                                service_count += 1

            if scan_type == "quick":
                flash(
                    f"Quick scan completed. {discovered_count} new assets discovered. {duplicate_count} existing assets skipped.",
                    "success"
                )
            else:
                flash(
                    f"Detailed scan completed. {discovered_count} new assets discovered, {duplicate_count} existing assets skipped, and {service_count} services discovered.",
                    "success"
                )

            return redirect(url_for('view_assets'))

        except Exception as e:
            flash(f"Network scan failed: {str(e)}", "danger")
            return redirect(url_for('network_scan'))

    return render_template('network_scan.html')


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

    success = delete_asset(asset_id)

    if success:
        flash('Asset deleted successfully!', 'success')
    else:
        flash("Failed to delete asset.", "danger")

    return redirect(url_for('view_assets'))


if __name__ == '__main__':
    app.run(debug=True)