from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os
from werkzeug.utils import secure_filename
import mysql.connector

app = Flask(__name__)
app.secret_key = "secretkey123"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- MySQL Connection ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Pranathi@14",  # change this
    database="assignment_portal"
)
cursor = conn.cursor(dictionary=True)

# ---------------- Login ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

# ---------------- Register ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        cursor.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                       (username, email, password, role))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------------- Logout ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- Admin Dashboard ----------------
@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('admin_dashboard.html', files=files)

# ---------------- Create Assignment Page ----------------
@app.route('/create')
def create():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('create.html')

# ---------------- Create Assignment Task ----------------
@app.route('/create_task', methods=['POST'])
def create_task():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    title = request.form['title']
    description = request.form['description']
    deadline = request.form['deadline']
    cursor.execute("INSERT INTO tasks (title, description, deadline) VALUES (%s, %s, %s)",
                   (title, description, deadline))
    conn.commit()
    return redirect(url_for('admin_dashboard'))

# ---------------- View File ----------------
@app.route('/view/<filename>')
def view_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------------- Download File ----------------
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# ---------------- Delete File ----------------
@app.route('/delete/<filename>')
def delete_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('admin_dashboard'))

# ---------------- Student Dashboard ----------------
@app.route('/student')
def student_dashboard():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    student_id = session['user_id']

    # Fetch all tasks
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    # Fetch all submissions by this student
    cursor.execute("SELECT * FROM submissions WHERE student_id=%s", (student_id,))
    submissions = cursor.fetchall()

    return render_template('student_dashboard.html',
                           student={'username': session['username']},
                           tasks=tasks,
                           submissions=submissions)

# ---------------- Upload Assignment ----------------
@app.route('/upload', methods=['POST'])
def upload():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    file = request.files['file']
    task_id = request.form['task_id']
    student_id = session['user_id']

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save submission in database
        cursor.execute("INSERT INTO submissions (student_id, task_id, filename) VALUES (%s,%s,%s)",
                       (student_id, task_id, filename))
        conn.commit()

    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)