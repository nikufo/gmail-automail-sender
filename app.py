from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'attachments'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

LOG_FILE = 'email_log.txt'

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create log file if it doesn't exist
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()

# Log function to save email info in log file
def log_email_sent(recipient_email, status):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{datetime.now()}, {recipient_email}, {status}\n")

# Function to send an individual email
def send_email(sender_name, recipient_email, subject, body, attachment=None, html_content=None):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "winhitz777@gmail.com"
    sender_password = "thdz finr drzg pgir"

    msg = MIMEMultipart()
    msg["From"] = sender_name
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Attach plain text and optional HTML content
    msg.attach(MIMEText(body, "plain"))
    if html_content:
        msg.attach(MIMEText(html_content, "html"))

    # Attach file if provided
    if attachment:
        part = MIMEBase('application', 'octet-stream')
        with open(attachment, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            log_email_sent(recipient_email, "Success")
            return "Success"
    except Exception as e:
        log_email_sent(recipient_email, f"Failed: {str(e)}")
        return f"Failed: {str(e)}"

# Route for the homepage (renders the HTML form)
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle single email sending via AJAX
@app.route('/send_email', methods=['POST'])
def handle_email():
    sender_name = request.form['sender_name']
    recipient_email = request.form['recipient_email']
    subject = request.form['subject']
    body = request.form['body']
    html_content = request.form['html_content']

    # Handle file attachment
    file = request.files['attachment']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    else:
        file_path = None

    # Send the email
    status = send_email(sender_name, recipient_email, subject, body, attachment=file_path, html_content=html_content)
    
    # Return response based on email status
    if "Success" in status:
        return jsonify({"status": "success", "message": f"Email sent to {recipient_email}"})
    else:
        return jsonify({"status": "failed", "message": status})

# Route to handle bulk email sending
@app.route('/import_email_list', methods=['POST'])
def import_email_list():
    sender_name = request.form['sender_name']
    subject = request.form['subject']
    body = request.form['body']
    html_content = request.form['html_content']
    delay = int(request.form['delay'])

    # Handle file attachment
    file = request.files['attachment']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    else:
        file_path = None

    # Read email list from CSV file
    email_list_file = request.files['email_list']
    if email_list_file:
        email_addresses = []
        file_content = email_list_file.read().decode("utf-8").splitlines()
        for row in file_content:
            email_addresses.append(row)  # Assuming each line contains a single email address
        
        # Send email to each recipient with delay
        success_count = 0
        failure_count = 0
        for email in email_addresses:
            status = send_email(sender_name, email, subject, body, attachment=file_path, html_content=html_content)
            if "Success" in status:
                success_count += 1
            else:
                failure_count += 1
            time.sleep(delay)  # Add delay between sending emails

    return jsonify({"status": "success", "message": f"Bulk emails sent: {success_count} success, {failure_count} failed."})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
