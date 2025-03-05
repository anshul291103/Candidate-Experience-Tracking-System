# Candidate Experience Tracking System

A Flask-based web application for candidate feedback management, integrating a MySQL database with the frontend.

## Technologies Used
- **Backend:** Flask, Python
- **Database:** MySQL, SQLAlchemy
- **Frontend:** Flask (Jinja Templates)
- **Tools:** Git, Virtual Environment

## How to Run

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/yourusername/candidate-experience-tracking.git
   cd candidate-experience-tracking
   ```

2. **Create a Virtual Environment (Recommended)**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # On macOS/Linux
   venv\Scripts\activate      # On Windows
   ```

3. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask App**  
   ```bash
   python app.py
   ```

5. **Access the Application**  
   - Click on the link displayed in the terminal (usually `http://127.0.0.1:5000/`).
   - If Flask runs on a different port, adjust the URL accordingly.

## Database Setup
To set up the database, run the following command in MySQL:
```sql
source schema.sql;
```

## Environment Variables Setup

To secure sensitive credentials, use a .env file. Create a .env file in the project directory and add:
```
SQLALCHEMY_DATABASE_URI=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@localhost/candidate_experience_db
SECRET_KEY=your_secret_key_here
```

## Note
Make sure to generate the `requirements.txt` file before pushing your project by running:
```bash
pip freeze > requirements.txt
```

This ensures all dependencies are listed for easy installation.
