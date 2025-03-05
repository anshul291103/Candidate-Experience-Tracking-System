import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, Feedback, Candidate, Stage, Recruiters, Report, User, Permission
from sqlalchemy import extract, func, or_, cast, Date, text
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ifkicyic123#@localhost/candidate_experience_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Generate a new secret key on each restart
app.config['SECRET_KEY'] = os.urandom(24)

db.init_app(app)


def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_role = session.get('role')  # Store user role in session
            if user_role not in allowed_roles:
                flash('You do not have permission to view this page.', 'danger')
                return redirect(url_for('index'))  # Redirect to home page 
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Hardcoded admin credentials
        admin_email = 'admin@example.com'         
        admin_password = 'admin123'

        # Check for admin login
        if email == admin_email and password == admin_password:
            session['user_id'] = 'admin'  
            session['email'] = admin_email
            session['role'] = 'Admin'  # Setting role as Admin
            flash('Admin login successful!', 'success')
            return redirect(url_for('index'))

        # Check if email exists in the Recruiters table
        recruiter_sql = text("SELECT RecruiterID, Email FROM recruiters WHERE Email = :email")
        recruiter = db.session.execute(recruiter_sql, {"email": email}).fetchone()

        # If recruiter not found, check in Candidates table
        if recruiter:
            user_id = recruiter.RecruiterID
            user_email = recruiter.Email
            role_id = 2  # Recruiters have a RoleID of 2
        else:
            candidate_sql = text("SELECT CandidateID, Email FROM candidates WHERE Email = :email")
            candidate = db.session.execute(candidate_sql, {"email": email}).fetchone()
            if candidate:
                user_id = candidate.CandidateID
                user_email = candidate.Email
                role_id = 3  # Candidates have a RoleID of 3
            else:
                flash('Invalid email or password.', 'danger')
                return render_template('login.html')  # Return to login page with flash message

        # Verify the password against the roles table using the corresponding RoleID
        role_sql = text("SELECT * FROM roles WHERE RoleID = :role_id")
        role = db.session.execute(role_sql, {"role_id": role_id}).fetchone()

        if role and role.Password == password:  # Check password
            session['user_id'] = user_id
            session['email'] = user_email
            session['role'] = role.RoleName  # Store the user's role in the session
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')  # Return to login page with flash message

    return render_template('login.html')


# Logout route to clear the session
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access the website.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
@role_required(['Admin', 'Recruiter', 'Candidate'])
def index():
    # Embedded SQL statement to count total feedback
    total_feedback_sql = text("SELECT COUNT(FeedbackID) FROM Feedback")
    total_feedback_count = db.session.execute(total_feedback_sql).scalar()

    # Embedded SQL statement to calculate average experience score
    average_score_sql = text("SELECT AVG(ExperienceScore) FROM Feedback")
    average_score = db.session.execute(average_score_sql).scalar()
    average_score = round(average_score, 2) if average_score else None  
    
    # SQL statement to fetch recent feedback
    recent_feedback_sql = text("SELECT * FROM Feedback ORDER BY FeedbackDate DESC LIMIT 5")
    recent_feedback = db.session.execute(recent_feedback_sql).fetchall()

    return render_template(
        'index.html',
        total_feedback=total_feedback_count,
        avg_score=average_score,
        recent_feedback=recent_feedback
    )


@app.route('/submit_feedback', methods=['GET', 'POST'])
@role_required(['Admin', 'Candidate'])  # Only Admin and Candidate can access this route
def submit_feedback():
    # SQL to fetch all stages
    stages_sql = text("SELECT * FROM RecruitmentStages")
    stages = db.session.execute(stages_sql).fetchall()

    # SQL to fetch all recruiters
    recruiters_sql = text("SELECT * FROM Recruiters")
    recruiters = db.session.execute(recruiters_sql).fetchall()

    if request.method == 'POST':
        try:
            candidate_id = int(request.form.get('candidate_id'))
            stage_name = request.form.get('stage_name')

            # SQL to get stage by name
            stage_sql = text("SELECT * FROM RecruitmentStages WHERE StageName = :stage_name")
            stage = db.session.execute(stage_sql, {"stage_name": stage_name}).fetchone()

            interviewer_name = request.form.get('interviewer_name')

            # SQL to get recruiter by name
            recruiter_sql = text("SELECT * FROM Recruiters WHERE Name = :interviewer_name")
            recruiter = db.session.execute(recruiter_sql, {"interviewer_name": interviewer_name}).fetchone()

            if not stage or not recruiter:
                flash("Stage or interviewer not found.", 'danger')
                return redirect(url_for('submit_feedback'))

            # SQL to insert feedback
            feedback_sql = text("""
                INSERT INTO Feedback (CandidateID, StageID, RecruiterID, FeedbackDate, ExperienceScore, Comments,
                                      InterviewDate, InterviewerName, Sentiment, FollowUpQuestion, ConsentGiven)
                VALUES (:candidate_id, :stage_id, :recruiter_id, :feedback_date, :experience_score, :comments,
                        :interview_date, :interviewer_name, :sentiment, :follow_up_question, :consent_given)
            """)

            db.session.execute(feedback_sql, {
                "candidate_id": candidate_id,
                "stage_id": stage.StageID,
                "recruiter_id": recruiter.RecruiterID if recruiter else None,
                "feedback_date": datetime.now().date(),
                "experience_score": float(request.form['score']),
                "comments": request.form['feedback'],
                "interview_date": request.form.get('interview_date'),
                "interviewer_name": interviewer_name,
                "sentiment": request.form.get('sentiment') or None,
                "follow_up_question": request.form.get('follow_up_question'),
                "consent_given": request.form.get('consent') == 'on'
            })

            db.session.commit()
            flash('Feedback submitted successfully!', 'success')
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f"Invalid input: {e}", 'danger')
            return redirect(url_for('submit_feedback'))
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
            return redirect(url_for('submit_feedback'))

    return render_template('submit_feedback.html', stages=stages, recruiters=recruiters)


@app.route('/view_feedback')
@role_required(['Admin', 'Recruiter'])  # Only users with READ permission can access this
def view_feedback():
    query_input = request.args.get('query', '').strip()

    # Start with the base SQL query
    base_sql = """
        SELECT Feedback.FeedbackDate, RecruitmentStages.StageName, Feedback.InterviewDate,
               Recruiters.Name, Feedback.Sentiment, Feedback.Comments,
               Feedback.FollowUpQuestion, Feedback.ExperienceScore
        FROM Feedback
        JOIN RecruitmentStages ON RecruitmentStages.StageID = Feedback.StageID
        JOIN Recruiters ON Recruiters.RecruiterID = Feedback.RecruiterID
    """

    # If a search query is provided, add a WHERE clause
    if query_input:
        search = f"%{query_input}%"
        try:
            # Attempt to parse the date from the query input
            date_search = datetime.strptime(query_input, '%Y-%m-%d').date()

            # Add date-specific filter to the base SQL
            filter_sql = """
                WHERE CAST(Feedback.FeedbackDate AS DATE) = :date_search
                OR CAST(Feedback.InterviewDate AS DATE) = :date_search
            """
            full_query = text(base_sql + filter_sql)
            feedback_data = db.session.execute(full_query, {"date_search": date_search}).fetchall()

        except ValueError:
            # If not a valid date, apply other filters
            filter_sql = """
                WHERE Feedback.Comments LIKE :search
                OR Feedback.FollowUpQuestion LIKE :search
                OR Feedback.Sentiment LIKE :search
                OR RecruitmentStages.StageName LIKE :search
                OR Recruiters.Name LIKE :search
                OR CAST(Feedback.ExperienceScore AS CHAR) LIKE :search
            """
            full_query = text(base_sql + filter_sql)
            feedback_data = db.session.execute(full_query, {"search": search}).fetchall()
    else:
        # No filter applied, execute the base query only
        full_query = text(base_sql)
        feedback_data = db.session.execute(full_query).fetchall()

    return render_template('view_feedback.html', feedback=feedback_data)


@app.route('/dashboard')
@role_required(['Admin', 'Recruiter'])  # Only Admin and Recruiter can access this route
def dashboard():
    # Ensure only feedback with consent is considered
    
    # 1. Calculate the average overall score from feedback with consent
    avg_score_sql = text("""
        SELECT ROUND(AVG(ExperienceScore), 2) AS avg_score
        FROM Feedback
        WHERE ConsentGiven = TRUE
    """)
    average_score = db.session.execute(avg_score_sql).scalar() or "No data"

    # 2. Aggregate sentiment counts with consent
    sentiment_counts_sql = text("""
        SELECT Sentiment, COUNT(Sentiment) AS count
        FROM Feedback
        WHERE ConsentGiven = TRUE
        GROUP BY Sentiment
    """)
    sentiment_counts = db.session.execute(sentiment_counts_sql).fetchall()

    # 3. Calculate the average score by recruitment stage using nested query
    score_by_stage_sql = text("""
        SELECT StageName, 
               (SELECT ROUND(AVG(ExperienceScore), 2) 
                FROM Feedback 
                WHERE StageID = RecruitmentStages.StageID AND ConsentGiven = TRUE) AS avg_score
        FROM RecruitmentStages
    """)
    score_by_stage = db.session.execute(score_by_stage_sql).fetchall()

    # 4. Analyze score trends over time (monthly)
    score_trends_sql = text("""
        SELECT EXTRACT(YEAR FROM Feedback.FeedbackDate) AS year,
               EXTRACT(MONTH FROM Feedback.FeedbackDate) AS month,
               ROUND(AVG(ExperienceScore), 2) AS avg_score
        FROM Feedback
        WHERE ConsentGiven = TRUE
        GROUP BY year, month
        ORDER BY year, month
    """)
    score_trends = db.session.execute(score_trends_sql).fetchall()

    # Calculate labels and scores for trends chart
    labels = [f"{int(row.year)}-{int(row.month):02d}" for row in score_trends]
    scores = [row.avg_score for row in score_trends]

    # 5. Calculate consent percentage
    total_feedback_with_consent_sql = text("""
        SELECT COUNT(FeedbackID) 
        FROM Feedback
        WHERE ConsentGiven = TRUE
    """)
    total_feedback_sql = text("SELECT COUNT(FeedbackID) FROM Feedback")
    total_feedback_with_consent = db.session.execute(total_feedback_with_consent_sql).scalar()
    total_feedback = db.session.execute(total_feedback_sql).scalar()

    consent_percentage = round((total_feedback_with_consent / total_feedback * 100), 2) if total_feedback else 0

    return render_template('dashboard.html', 
                           average_score=average_score,
                           sentiment_counts=sentiment_counts,
                           score_by_stage=score_by_stage,
                           score_trends=score_trends,
                           consent_percentage=consent_percentage,
                           labels=labels,
                           scores=scores)


@app.route('/create_report', methods=['GET', 'POST'])
@role_required(['Admin', 'Recruiter'])
def create_report():
    if request.method == 'POST':
        recruiter_id = request.form.get('recruiter_id')
        report_title = request.form.get('report_title')
        report_content = request.form.get('report_content')
        report_date = datetime.now().date()

        # SQL statement to insert a new report
        sql = text("""
            INSERT INTO Reports (RecruiterID, ReportDate, Title, ReportContent)
            VALUES (:recruiter_id, :report_date, :title, :content)
        """)

        try:
            # Execute the SQL with parameters
            db.session.execute(sql, {
                "recruiter_id": recruiter_id,
                "report_date": report_date,
                "title": report_title,
                "content": report_content
            })
            db.session.commit()
            flash('Report created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", 'danger')
        
        return redirect(url_for('index'))

    return render_template('create_report.html')


@app.route('/view_reports')
@role_required(['Admin', 'Recruiter'])
def view_reports():
    # SQL to fetch all reports
    sql = text("SELECT * FROM Reports")
    result = db.session.execute(sql)
    
    # Fetch all rows and store them in the `reports` variable
    reports = result.fetchall()
    
    return render_template('view_reports.html', reports=reports)


@app.route('/request_delete_report', methods=['GET', 'POST'])
@role_required(['Admin', 'Recruiter'])
def request_delete_report():
    if request.method == 'POST':
        report_id = request.form.get('report_id')
        
        try:
            # Directly delete the report by ReportID
            result = db.session.execute(text("DELETE FROM Reports WHERE ReportID = :report_id"), {'report_id': report_id})
            db.session.commit()
            
            # Check if any row was affected (i.e., the report existed and was deleted)
            if result.rowcount > 0:
                flash("Report deleted successfully.", 'success')
            else:
                flash("Report not found.", 'warning')
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting report: {str(e)}", 'danger')

        return redirect(url_for('view_reports'))
    
    # For GET request, show the form and the list of reports
    reports = db.session.execute(text("SELECT * FROM Reports")).fetchall()
    return render_template('request_delete_report.html', reports=reports)


@app.route('/delete_report/<int:report_id>', methods=['POST'])
# @role_required(['Admin'])
def delete_report(report_id):
    try:
        # Directly delete the report by ReportID
        result = db.session.execute(
            text("DELETE FROM Reports WHERE ReportID = :report_id"),
            {'report_id': report_id}
        )
        db.session.commit()  # Commit transaction

        # Check if any row was affected (i.e., the report existed and was deleted)
        if result.rowcount > 0:
            flash("Report deleted successfully.", 'success')
        else:
            flash("Report not found.", 'warning')

    except Exception as e:
        db.session.rollback()  # Rollback transaction on error
        flash(f'Error deleting report: {str(e)}', 'danger')
    
    return redirect(url_for('view_reports'))


@app.route('/add_candidate', methods=['GET', 'POST'])
@role_required(['Admin'])
def add_candidate():
    if request.method == 'POST':
        try:
            # Fetch form data
            candidate_name = request.form['name']
            candidate_email = request.form['email']
            date_of_birth = request.form.get('date_of_birth')  
            phone = request.form.get('phone')  
            address = request.form.get('address')  
            linkedin_profile = request.form.get('linkedin_profile')  
            skills = request.form.get('skills')  

            # Execute stored procedure with embedded SQL
            sql = text(
                "CALL AddNewCandidate(:candidate_name, :candidate_email, :date_of_birth, :phone, :address, :linkedin_profile, :skills)"
            )
            db.session.execute(sql, {
                'candidate_name': candidate_name,
                'candidate_email': candidate_email,
                'date_of_birth': date_of_birth,
                'phone': phone,
                'address': address,
                'linkedin_profile': linkedin_profile,
                'skills': skills
            })
            db.session.commit()  # Commit transaction

            flash('Candidate added successfully!', 'success')
            return redirect(url_for('add_candidate'))
        except Exception as e:
            db.session.rollback()  # Rollback transaction on error
            flash(str(e), 'danger')

    return render_template('add_candidate.html')


@app.route('/view_candidates')
@role_required(['Admin'])
def view_candidates():
    # SQL query to select all candidates
    sql = text("SELECT * FROM Candidates")
    candidates = db.session.execute(sql).fetchall()  # Execute query and fetch results
    return render_template('view_candidates.html', candidates=candidates)


@app.route('/request_edit_candidate', methods=['GET', 'POST'])
@role_required(['Admin'])
def request_edit_candidate():
    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id')
        candidate = Candidate.query.get(candidate_id)
        if candidate:
            return redirect(url_for('edit_candidate', candidate_id=candidate_id))
        else:
            flash('Candidate not found. Please enter a valid Candidate ID.', 'error')
            return redirect(url_for('request_edit_candidate'))
    return render_template('request_edit_candidate.html')


@app.route('/edit_candidate/<int:candidate_id>', methods=['GET', 'POST'])
def edit_candidate(candidate_id):
    # Use SQL to fetch the candidate by ID
    sql = text("SELECT * FROM Candidates WHERE CandidateID = :candidate_id")
    candidate = db.session.execute(sql, {'candidate_id': candidate_id}).fetchone()

    if candidate:
        if request.method == 'POST':
            # Update candidate details using SQL
            update_sql = text("""
                UPDATE Candidates 
                SET Name = :name,
                    Email = :email,
                    DateOfBirth = :dob,
                    Phone = :phone,
                    Address = :address,
                    LinkedInProfile = :linkedin,
                    Skills = :skills
                WHERE CandidateID = :candidate_id
            """)
            db.session.execute(update_sql, {
                'name': request.form['name'],
                'email': request.form['email'],
                'dob': request.form.get('dob'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address'),
                'linkedin': request.form.get('linkedin'),
                'skills': request.form.get('skills'),
                'candidate_id': candidate_id
            })
            db.session.commit()
            flash('Candidate details updated successfully!', 'success')
            return redirect(url_for('edit_candidate', candidate_id=candidate_id))

        return render_template('edit_candidate.html', candidate=candidate)
    else:
        flash('No candidate found with the specified ID.', 'error')
        return redirect(url_for('request_edit_candidate'))


@app.route('/view_archived_feedback', methods=['GET'])
@role_required(['Admin', 'Recruiter'])
def view_archived_feedback():
    search_query = request.args.get('query', '')  # Get the search query from URL parameters
    try:
        # Use text() for the SELECT query
        if search_query:
            # Construct a search query using LIKE for relevant fields
            archived_feedback_list = db.session.execute(
                text("""
                    SELECT * FROM feedback_archive
                    WHERE FeedbackID LIKE :query OR
                          CandidateID LIKE :query OR
                          FeedbackDate LIKE :query OR
                          Comments LIKE :query OR
                          InterviewerName LIKE :query OR
                          ExperienceScore LIKE :query OR
                          ArchiveDate LIKE :query
                """),
                {'query': f'%{search_query}%'}  # Using wildcard for partial matches
            ).fetchall()
        else:
            # If no search query, fetch all archived feedback
            archived_feedback_list = db.session.execute(text("SELECT * FROM feedback_archive")).fetchall()
        
        return render_template('view_archived_feedback.html', archived_feedback_list=archived_feedback_list, search_query=search_query)
    except Exception as e:
        flash(f'Error retrieving archived feedback: {str(e)}', 'danger')
        return redirect(url_for('feedback_page'))


@app.route('/view_feedback_log', methods=['GET'])
@role_required(['Admin', 'Recruiter'])
def view_feedback_log():
    try:
        # Fetch all records from the feedback_log table
        feedback_log_list = db.session.execute(text("SELECT * FROM feedback_log")).fetchall()
        return render_template('view_feedback_log.html', feedback_log_list=feedback_log_list)
    except Exception as e:
        flash(f'Error retrieving feedback log: {str(e)}', 'danger')
        return redirect(url_for('feedback_page'))  
    

@app.route('/request_delete_candidate', methods=['GET', 'POST'])
@role_required(['Admin'])
def request_delete_candidate():
    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id')
        
        try:
            # Call the stored procedure to delete the candidate
            result = db.session.execute(text("CALL DeleteCandidateByID(:candidate_id)"), {'candidate_id': candidate_id})
            db.session.commit()
            
            # Fetch the result message from the procedure
            message = result.fetchone()[0]
            flash(message, 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting candidate: {str(e)}", 'danger')

        return redirect(url_for('view_candidates'))
    
    # For GET request, show the form and the list of candidates
    candidates = db.session.execute(text("SELECT * FROM candidates")).fetchall()
    return render_template('request_delete_candidate.html', candidates=candidates)
    

@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    try:
        # Call stored procedure to delete candidate
        result = db.session.execute(
            text("CALL DeleteCandidateByID(:candidate_id)"),
            {'candidate_id': candidate_id}
        ).fetchone()
        db.session.commit()  # Commit transaction

        # Show success message from the procedure
        flash(result[0], 'success')
    except Exception as e:
        db.session.rollback()  # Rollback transaction on error
        flash(f'Error deleting candidate: {str(e)}', 'danger')
    
    return redirect(url_for('view_candidates'))

if __name__ == "__main__":
    app.run(debug=True)
