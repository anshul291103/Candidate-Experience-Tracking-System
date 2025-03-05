from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  

class Feedback(db.Model):
    __tablename__ = 'feedback'

    FeedbackID = db.Column(db.Integer, primary_key=True)
    CandidateID = db.Column(db.Integer, db.ForeignKey('candidates.CandidateID'), nullable=True)
    StageID = db.Column(db.Integer, db.ForeignKey('recruitmentstages.StageID'), nullable=True)
    RecruiterID = db.Column(db.Integer, db.ForeignKey('recruiters.RecruiterID'), nullable=True)  # Corrected to db.Column
    FeedbackDate = db.Column(db.Date, nullable=False)
    ExperienceScore = db.Column(db.Numeric(3, 2), nullable=True)  # Consider allowing null if scores may not always be provided
    Comments = db.Column(db.Text, nullable=True)
    InterviewerName = db.Column(db.String(50), nullable=True)  # Ensure this is still needed or update the logic accordingly
    InterviewDate = db.Column(db.Date, nullable=True)
    Sentiment = db.Column(db.String(20), nullable=True)
    FollowUpQuestion = db.Column(db.Text, nullable=True)
    ConsentGiven = db.Column(db.Boolean, nullable=True)

    def __repr__(self):
        return f'<Feedback {self.FeedbackID}>'

    
class Stage(db.Model):
    __tablename__ = 'recruitmentstages'  

    StageID = db.Column(db.Integer, primary_key=True)
    StageName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Stage {self.StageName}>'
    
class Recruiters(db.Model):
    __tablename__ = 'recruiters'
    RecruiterID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Phone = db.Column(db.String(15), nullable=True)
    Role = db.Column(db.String(50), nullable=True)
    
class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    CandidateID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=True)
    Phone = db.Column(db.String(15), nullable=True)
    Address = db.Column(db.Text, nullable=True)
    Status = db.Column(db.String(50), default='Pending') 
    LinkedInProfile = db.Column(db.Text, nullable=True)
    Skills = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Candidate {self.Name}>'
    
class Report(db.Model):
    __tablename__ = 'reports'
    ReportID = db.Column(db.Integer, primary_key=True)
    RecruiterID = db.Column(db.Integer, db.ForeignKey('recruiters.RecruiterID'), nullable=True)
    ReportDate = db.Column(db.Date, nullable=False)
    Title = db.Column(db.String(150), nullable=True)
    ReportContent = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Report {self.ReportID} Title: {self.Title}>'
    
class FeedbackArchive(db.Model):
    __tablename__ = 'feedback_archive'

    FeedbackID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CandidateID = db.Column(db.Integer, db.ForeignKey('candidates.CandidateID'), nullable=True)
    StageID = db.Column(db.Integer, db.ForeignKey('stages.StageID'), nullable=True)
    FeedbackDate = db.Column(db.Date, nullable=False)
    ExperienceScore = db.Column(db.Numeric(3, 2), nullable=False)
    Comments = db.Column(db.Text, nullable=True)
    InterviewerName = db.Column(db.String(50), nullable=True)
    InterviewDate = db.Column(db.Date, nullable=True)
    Sentiment = db.Column(db.String(20), nullable=True)
    FollowUpQuestion = db.Column(db.Text, nullable=True)
    ConsentGiven = db.Column(db.Boolean, nullable=True)
    RecruiterID = db.Column(db.Integer, db.ForeignKey('recruiters.RecruiterID'), nullable=True)
    ArchiveDate = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<FeedbackArchive {self.FeedbackID}>"
    
class Role(db.Model):
    __tablename__ = 'roles'
    
    RoleID = db.Column(db.Integer, primary_key=True)
    RoleName = db.Column(db.String(50), nullable=False)
    Password = db.Column(db.String(50), nullable=False)  # Ensure to handle passwords securely

    def __repr__(self):
        return f'<Role {self.RoleName}>'

class User(db.Model):
    __tablename__ = 'users'
    
    UserID = db.Column(db.Integer, primary_key=True)
    RoleID = db.Column(db.Integer, db.ForeignKey('roles.RoleID'), nullable=False)
    Username = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)

    role = db.relationship('Role', backref='users')  # Establish relationship to Role

    def __repr__(self):
        return f'<User {self.Username}>'

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    PermissionID = db.Column(db.Integer, primary_key=True)
    RoleID = db.Column(db.Integer, db.ForeignKey('roles.RoleID'), nullable=False)
    Action = db.Column(db.String(50), nullable=False)

    role = db.relationship('Role', backref='permissions')  # Establish relationship to Role

    def __repr__(self):
        return f'<Permission {self.Action} for RoleID {self.RoleID}>'


