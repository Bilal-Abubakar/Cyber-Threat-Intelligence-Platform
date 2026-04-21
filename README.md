# Cyber Threat Intelligence Platform

A web-based Cyber Threat Intelligence (CTI) platform for identifying organizational assets, linking them to owners, and supporting risk awareness through structured asset management and vulnerability mapping.

## Project Overview

This project is designed to improve cyber defence by focusing on **asset visibility**, **owner accountability**, and **risk awareness**. Instead of only showing generic vulnerability alerts, the platform is intended to help organizations understand:

- what assets they have,
- who is responsible for those assets,
- what risks may affect them,
- and which issues should be prioritized.

## Current Features

At the current development stage, the platform supports:

- User registration
- User login and logout
- Manual asset registration
- Viewing all registered assets
- Editing asset records
- Deleting asset records
- SQLite database support
- Database backup script

## Planned Features

The following features are planned for future development:

- CSV asset upload
- Asset search and filtering
- Network-based asset discovery
- Vulnerability mapping
- Risk scoring and prioritization
- Report generation
- Dashboard improvements

## Technologies Used

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS
- **Authentication:** Flask-Login
- **Password Security:** Werkzeug password hashing

## Project Structure

```text
Cyber-Threat-Intelligence-Platform/
│
├── app.py
├── database.py
├── backup.py
├── assets.db
├── README.md
│
└── templates/
    ├── login.html
    ├── register.html
    ├── register_asset.html
    ├── view_assets.html
    └── edit_asset.html