import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Put your MySQL password here if you have one
    "database": "cti_platform"
}


def create_database():
    """
    Creates the MySQL database if it does not already exist.
    This is separated from init_db because we need to connect first
    without selecting a database.
    """
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )

        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS cti_platform")
        conn.commit()

        cursor.close()
        conn.close()

        print("Database created or already exists.")

    except Error as e:
        print(f"Error creating database: {e}")


def init_db():
    """
    Initializes all required tables for the CTI platform.
    The database supports:
    - user authentication
    - asset management
    - asset categorisation
    - discovered services from scans
    - vulnerability storage
    - CVE-to-asset mapping
    """

    create_database()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # -------------------------
        # Users table
        # -------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # -------------------------
        # Categories table
        # -------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_name VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # -------------------------
        # Assets table
        # -------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                asset_type VARCHAR(100) NOT NULL,
                owner VARCHAR(150) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                os VARCHAR(150),
                criticality ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
                category_id INT,
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (category_id) REFERENCES categories(id)
                    ON DELETE SET NULL,

                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE SET NULL
            )
        """)

        # -------------------------
        # Asset services table
        # Stores services discovered through Nmap scanning
        # -------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                asset_id INT NOT NULL,
                port INT NOT NULL,
                protocol VARCHAR(20) DEFAULT 'tcp',
                service_name VARCHAR(100),
                service_version VARCHAR(255),
                product VARCHAR(255),
                scan_source VARCHAR(100) DEFAULT 'nmap',
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (asset_id) REFERENCES assets(id)
                    ON DELETE CASCADE
            )
        """)

        # -------------------------
        # Vulnerabilities table
        # Stores CVE information gathered from NVD or local dataset
        # -------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cve_id VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                cvss_score DECIMAL(3,1),
                severity ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
                source VARCHAR(100) DEFAULT 'NVD',
                published_date VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # -------------------------
        # Asset vulnerability mapping table
        # Connects assets to CVEs
        # -------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_vulnerabilities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                asset_id INT NOT NULL,
                vulnerability_id INT NOT NULL,
                service_id INT,
                risk_score DECIMAL(5,2),
                risk_level ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
                mapping_reason TEXT,
                mapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (asset_id) REFERENCES assets(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (vulnerability_id) REFERENCES vulnerabilities(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (service_id) REFERENCES asset_services(id)
                    ON DELETE SET NULL
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("MySQL database initialized successfully.")

    except Error as e:
        print(f"Error initializing database: {e}")


if __name__ == "__main__":
    init_db()