-- Table creations
CREATE TABLE candidates (
    CandidateID INT NOT NULL AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    DateOfBirth DATE,
    Phone VARCHAR(15),
    Address TEXT,
    LinkedInProfile TEXT,
    Skills TEXT,
    Status VARCHAR(50) DEFAULT 'Pending',
    PRIMARY KEY (CandidateID)
);

CREATE TABLE feedback (
    FeedbackID INT NOT NULL AUTO_INCREMENT,
    CandidateID INT,
    StageID INT,
    FeedbackDate DATE NOT NULL,
    ExperienceScore DECIMAL(3,2) NOT NULL,
    Comments TEXT,
    InterviewerName VARCHAR(50),
    InterviewDate DATE,
    Sentiment VARCHAR(20),
    FollowUpQuestion TEXT,
    ConsentGiven TINYINT(1),
    RecruiterID INT,
    PRIMARY KEY (FeedbackID),
    FOREIGN KEY (CandidateID) REFERENCES candidates(CandidateID),
    FOREIGN KEY (StageID) REFERENCES recruitmentstages(StageID),
    FOREIGN KEY (RecruiterID) REFERENCES recruiters(RecruiterID)
);

CREATE TABLE feedback_archive (
    FeedbackID INT NOT NULL AUTO_INCREMENT,
    CandidateID INT,
    StageID INT,
    FeedbackDate DATE NOT NULL,
    ExperienceScore DECIMAL(3,2) NOT NULL,
    Comments TEXT,
    InterviewerName VARCHAR(50),
    InterviewDate DATE,
    Sentiment VARCHAR(20),
    FollowUpQuestion TEXT,
    ConsentGiven TINYINT(1),
    RecruiterID INT,
    ArchiveDate DATE,
    PRIMARY KEY (FeedbackID),
    FOREIGN KEY (CandidateID) REFERENCES candidates(CandidateID),
    FOREIGN KEY (StageID) REFERENCES recruitmentstages(StageID),
    FOREIGN KEY (RecruiterID) REFERENCES recruiters(RecruiterID)
);

CREATE TABLE feedback_log (
    LogID INT NOT NULL AUTO_INCREMENT,
    FeedbackID INT,
    SubmissionDate DATE,
    SubmittedBy VARCHAR(50),
    PRIMARY KEY (LogID),
    FOREIGN KEY (FeedbackID) REFERENCES feedback(FeedbackID)
);

CREATE TABLE recruiters (
    RecruiterID INT NOT NULL AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Phone VARCHAR(15),
    Role VARCHAR(50),
    PRIMARY KEY (RecruiterID)
);

CREATE TABLE recruitmentstages (
    StageID INT NOT NULL AUTO_INCREMENT,
    StageName VARCHAR(100) NOT NULL,
    Description TEXT,
    PRIMARY KEY (StageID)
);

CREATE TABLE reports (
    ReportID INT NOT NULL AUTO_INCREMENT,
    RecruiterID INT,
    ReportDate DATE NOT NULL,
    Title VARCHAR(150),
    ReportContent TEXT,
    PRIMARY KEY (ReportID),
    FOREIGN KEY (RecruiterID) REFERENCES recruiters(RecruiterID)
);

CREATE TABLE surveyquestions (
    QuestionID INT NOT NULL AUTO_INCREMENT,
    SurveyID INT,
    QuestionText TEXT NOT NULL,
    QuestionType VARCHAR(50) NOT NULL,
    PRIMARY KEY (QuestionID),
    FOREIGN KEY (SurveyID) REFERENCES surveys(SurveyID)
);

CREATE TABLE surveys (
    SurveyID INT NOT NULL AUTO_INCREMENT,
    SurveyName VARCHAR(100) NOT NULL,
    Description TEXT,
    PRIMARY KEY (SurveyID)
);



-- Trigger for logging feedback
CREATE TRIGGER log_feedback_submission
AFTER INSERT ON feedback
FOR EACH ROW
BEGIN
    INSERT INTO feedback_log (FeedbackID, SubmittedBy)
    VALUES (NEW.FeedbackID, NEW.SubmittedBy);
END;


-- Trigger for updating candidate status
DELIMITER //
CREATE TRIGGER update_candidate_status
AFTER INSERT ON feedback
FOR EACH ROW
BEGIN
    DECLARE new_status VARCHAR(50);
    SET new_status = CASE 
        WHEN NEW.ExperienceScore >= 8 THEN 'Highly Satisfactory'
        WHEN NEW.ExperienceScore >= 5 THEN 'Satisfactory'
        ELSE 'Needs Improvement'
    END;
    
    UPDATE candidates
    SET Status = new_status
    WHERE CandidateID = NEW.CandidateID;
END //
DELIMITER ;


-- Procedure to add a new candidate
DELIMITER //
CREATE PROCEDURE AddNewCandidate(
    IN candidate_name VARCHAR(50),
    IN candidate_email VARCHAR(100),
    IN date_of_birth DATE,
    IN phone VARCHAR(15),
    IN address TEXT,
    IN linkedin_profile TEXT,
    IN skills TEXT
)
BEGIN
    INSERT INTO candidates (
        Name, Email, DateOfBirth, Phone, Address, LinkedInProfile, Skills, Status
    ) VALUES (
        candidate_name, candidate_email, date_of_birth, phone, address, linkedin_profile, skills, 'Pending'
    );
END //
DELIMITER ;


-- Procedure to archive 1 year old feedback
DELIMITER //
CREATE PROCEDURE ArchiveOldFeedback()
BEGIN
    INSERT INTO feedback_archive
    SELECT *, CURDATE() AS ArchiveDate FROM feedback
    WHERE FeedbackDate < DATE_SUB(NOW(), INTERVAL 1 YEAR);

    DELETE FROM feedback
    WHERE FeedbackDate < DATE_SUB(NOW(), INTERVAL 1 YEAR);
END //
DELIMITER ;


-- Event to run the procedure 'ArchiveOldFeedback' everyday
CREATE EVENT IF NOT EXISTS ArchiveOldFeedbackDaily
ON SCHEDULE EVERY 1 DAY
DO
    CALL ArchiveOldFeedback();


-- Procedure to delete a candidate given the candidate id
DELIMITER //

CREATE PROCEDURE DeleteCandidateByID(IN candidate_id INT)
BEGIN
    -- Check if the candidate exists
    IF EXISTS (SELECT 1 FROM candidates WHERE CandidateID = candidate_id) THEN
        -- Delete the candidate record
        DELETE FROM candidates WHERE CandidateID = candidate_id;
        SELECT CONCAT('Candidate with ID ', candidate_id, ' has been successfully deleted.') AS ResultMessage;
    ELSE
        -- Return a message if candidate is not found
        SELECT CONCAT('No candidate found with ID ', candidate_id) AS ResultMessage;
    END IF;
END //

DELIMITER ;



-- User creation and privileges

-- Admin user
CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'admin_password';
-- Recruiter user
CREATE USER 'recruiter_user'@'localhost' IDENTIFIED BY 'recruiter_password';
-- Candidate user
CREATE USER 'candidate_user'@'localhost' IDENTIFIED BY 'candidate_password';

-- Admin: Full access to the entire database
GRANT ALL PRIVILEGES ON candidate_experience_db.* TO 'admin_user'@'localhost';

-- Recruiter: Specific privileges to view feedback, create and view reports
GRANT SELECT ON candidate_experience_db.Feedback TO 'recruiter_user'@'localhost';
GRANT INSERT, SELECT ON candidate_experience_db.Reports TO 'recruiter_user'@'localhost';

-- Candidate: Privileges to submit feedback
GRANT INSERT ON candidate_experience_db.Feedback TO 'candidate_user'@'localhost';

-- Step 3: Apply changes
FLUSH PRIVILEGES;






