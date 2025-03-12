# RetroNetPortal

A Flask-based web application for the Digital Artisans community portal.

## Features

- User authentication and management
- Digital Artisan Points (DAP) system
- Marketplace (Bazaar)
- Community networking
- Project management
- Treasury management

## Development Status

This repository contains the development version of the RetroNetPortal application.

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure environment variables
6. Run the application: `python app.py`

## Project Structure

- `app.py`: Main application file
- `models.py`: Database models
- `forms.py`: Form definitions
- `database.py`: Database configuration
- `templates/`: HTML templates
- `static/`: Static assets (CSS, JS, images)
- `db_backup/`: Database backup utilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.