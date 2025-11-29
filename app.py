from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date, timedelta
import cv2
import numpy as np
import base64
import os
import json
from werkzeug.utils import secure_filename
import database
import config
import face_utils
import report_analyzer
from functools import wraps
import sys

# Add module directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'module'))

# Import MySQL modules
try:
    from mysql_integration import AttendanceMySQL
    mysql_available = True
except ImportError:
    mysql_available = False
    print("MySQL modules not available, using SQLite")

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']

# Initialize MySQL database if available
if mysql_available:
    mysql_db = AttendanceMySQL()
else:
    mysql_db = None

# Configure upload folders
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
for folder in ['plans', 'reports', 'profiles']:
    os.makedirs(os.path.join(UPLOAD_FOLDER, folder), exist_ok=True)
os.makedirs('known_faces', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Role-based access control
def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                flash('Please login first', 'error')
                return redirect(url_for('login'))
            if session['user_role'] not in required_roles:
                flash('Access denied: Insufficient permissions', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# === AUTHENTICATION ===
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/do_login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = database.get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('login'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, username, fullname, role FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['fullname'] = user['fullname']
            session['user_role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'Login error: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Dashboard statistics
        cursor.execute("SELECT COUNT(*) as count FROM members WHERE status = 'active'")
        active_members = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM members WHERE status = 'pending'")
        pending_members = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_date >= %s", (date.today(),))
        upcoming_events = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(DISTINCT a.member_id) as count 
            FROM attendance a 
            JOIN events e ON a.event_id = e.id 
            WHERE e.event_date = %s
        """, (date.today(),))
        result = cursor.fetchone()
        today_attendance = result['count'] if result else 0
        
        # Recent activities
        cursor.execute("""
            SELECT m.fullname, a.recognized_at, e.title 
            FROM attendance a 
            JOIN members m ON a.member_id = m.id 
            JOIN events e ON a.event_id = e.id 
            ORDER BY a.recognized_at DESC 
            LIMIT 5
        """)
        recent_activities = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        active_members = pending_members = upcoming_events = today_attendance = 0
        recent_activities = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('dashboard.html',
                         active_members=active_members,
                         pending_members=pending_members,
                         upcoming_events=upcoming_events,
                         today_attendance=today_attendance,
                         recent_activities=recent_activities)

# === SIMPLE ATTENDANCE (MySQL Integration) ===
@app.route('/attendance')
def attendance():
    """Simple attendance page with MySQL integration"""
    if mysql_available:
        today_attendance = mysql_db.get_daily_report()
    else:
        today_attendance = []
    
    return render_template('attendance.html', attendance=today_attendance)

@app.route('/api/test')
def test_api():
    return jsonify({"status": "success", "message": "API is working!"})

@app.route('/api/mysql_health')
def mysql_health():
    """Check MySQL connection status"""
    if mysql_available:
        try:
            # Test MySQL connection
            result = mysql_db.get_today_attendance()
            return jsonify({
                "status": "success", 
                "message": "MySQL connection is working",
                "today_records": len(result) if result else 0
            })
        except Exception as e:
            return jsonify({
                "status": "error", 
                "message": f"MySQL error: {str(e)}"
            })
    else:
        return jsonify({
            "status": "error", 
            "message": "MySQL module not available"
        })

@app.route('/api/clock_in', methods=['POST'])
def clock_in():
    """Clock in using MySQL"""
    if not mysql_available:
        return jsonify({'status': 'error', 'message': 'MySQL not available'})
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        confidence = data.get('confidence', 0.0)
        
        if user_id and user_name:
            # Register user if not exists
            mysql_db.register_user(user_id, user_name)
            
            # Log attendance
            success = mysql_db.log_attendance(user_id, user_name, confidence)
            if success:
                return jsonify({'status': 'success', 'message': 'Clocked in successfully'})
        
        return jsonify({'status': 'error', 'message': 'Failed to clock in'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/clock_out', methods=['POST'])
def clock_out():
    """Clock out using MySQL"""
    if not mysql_available:
        return jsonify({'status': 'error', 'message': 'MySQL not available'})
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if user_id:
            success = mysql_db.clock_out_user(user_id)
            if success:
                return jsonify({'status': 'success', 'message': 'Clocked out successfully'})
        
        return jsonify({'status': 'error', 'message': 'Failed to clock out'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/attendance/today')
def get_today_attendance():
    """Get today's attendance from MySQL"""
    if not mysql_available:
        return jsonify({'status': 'error', 'message': 'MySQL not available', 'data': []})
    
    try:
        attendance_data = mysql_db.get_daily_report()
        return jsonify({'status': 'success', 'data': attendance_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e), 'data': []})

@app.route('/reports_mysql')
def mysql_reports():
    """MySQL-based reports page"""
    if not mysql_available:
        flash('MySQL reports not available', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        monthly_report = mysql_db.get_monthly_report()
        return render_template('mysql_reports.html', report=monthly_report)
    except Exception as e:
        flash(f'Error loading MySQL reports: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/export_csv')
def export_csv():
    """Export MySQL attendance data to CSV"""
    if not mysql_available:
        return jsonify({'status': 'error', 'message': 'MySQL not available'})
    
    try:
        # Export last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        filename = mysql_db.export_to_csv(start_date, end_date)
        if filename:
            return jsonify({'status': 'success', 'file': filename})
        else:
            return jsonify({'status': 'error', 'message': 'Export failed'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# === MEMBER MANAGEMENT ===
@app.route('/members')
@role_required(['admin', 'manager'])
def manage_members():
    status_filter = request.args.get('status', 'all')
    
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if status_filter == 'all':
            cursor.execute("""
                SELECT id, fullname, membership_number, email, phone, 
                       status, membership_type, join_date, face_encoding_path
                FROM members 
                ORDER BY fullname
            """)
        else:
            cursor.execute("""
                SELECT id, fullname, membership_number, email, phone, 
                       status, membership_type, join_date, face_encoding_path
                FROM members 
                WHERE status = %s
                ORDER BY fullname
            """, (status_filter,))
        
        members = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading members: {str(e)}', 'error')
        members = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('member_management.html', 
                         members=members, 
                         status_filter=status_filter)

@app.route('/members/register', methods=['GET', 'POST'])
def register_member():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        date_of_birth = request.form.get('date_of_birth')
        emergency_contact = request.form.get('emergency_contact')
        membership_type = request.form.get('membership_type')
        
        if not fullname or not email:
            flash('Fullname and email are required', 'error')
            return render_template('member_registration.html')
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Generate membership number
            cursor.execute("SELECT COUNT(*) as count FROM members")
            member_count = cursor.fetchone()[0]
            membership_number = f"MEM{member_count + 1:06d}"
            
            cursor.execute("""
                INSERT INTO members (
                    fullname, email, phone, address, date_of_birth, 
                    emergency_contact, membership_type, membership_number, 
                    status, join_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fullname, email, phone, address, date_of_birth,
                emergency_contact, membership_type, membership_number,
                'pending', date.today()
            ))
            
            member_id = cursor.lastrowid
            conn.commit()
            
            flash('Member registration submitted for approval!', 'success')
            return redirect(url_for('member_profile', member_id=member_id))
        
        except Exception as e:
            conn.rollback()
            flash(f'Error registering member: {str(e)}', 'error')
        
        finally:
            cursor.close()
            conn.close()
    
    return render_template('member_registration.html')

@app.route('/members/<int:member_id>')
@role_required(['admin', 'manager', 'user'])
def member_profile(member_id):
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, fullname, membership_number, email, phone, address,
                   date_of_birth, emergency_contact, membership_type, 
                   status, join_date, face_encoding_path
            FROM members WHERE id = %s
        """, (member_id,))
        
        member = cursor.fetchone()
        
        if not member:
            flash('Member not found', 'error')
            return redirect(url_for('manage_members'))
        
        cursor.execute("""
            SELECT e.title, e.event_date, a.status, a.recognized_at
            FROM attendance a
            JOIN events e ON a.event_id = e.id
            WHERE a.member_id = %s
            ORDER BY e.event_date DESC
            LIMIT 10
        """, (member_id,))
        
        attendance_history = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading member profile: {str(e)}', 'error')
        return redirect(url_for('manage_members'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('member_profile.html',
                         member=member,
                         attendance_history=attendance_history)

@app.route('/members/<int:member_id>/approve', methods=['POST'])
@role_required(['admin', 'manager'])
def approve_member(member_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE members 
            SET status = 'active', approved_by = %s, approved_at = %s 
            WHERE id = %s
        """, (session['user_id'], datetime.now(), member_id))
        
        conn.commit()
        flash('Member approved successfully!', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error approving member: {str(e)}', 'error')
    
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('approval_queue'))

@app.route('/members/<int:member_id>/reject', methods=['POST'])
@role_required(['admin', 'manager'])
def reject_member(member_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM members WHERE id = %s", (member_id,))
        conn.commit()
        flash('Member registration rejected and deleted', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error rejecting member: {str(e)}', 'error')
    
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('approval_queue'))

@app.route('/members/approval_queue')
@role_required(['admin', 'manager'])
def approval_queue():
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, fullname, email, phone, membership_type, join_date
            FROM members 
            WHERE status = 'pending'
            ORDER BY join_date
        """)
        
        pending_members = cursor.fetchall()
    
    except Exception as e:
        flash(f'Error loading approval queue: {str(e)}', 'error')
        pending_members = []
    
    finally:
        cursor.close()
        conn.close()
    
    return render_template('approval_queue.html', pending_members=pending_members)

# === FACE REGISTRATION ===
@app.route('/members/<int:member_id>/register_face', methods=['GET', 'POST'])
@role_required(['admin', 'manager'])
def register_face(member_id):
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, fullname FROM members WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        if not member:
            flash('Member not found', 'error')
            return redirect(url_for('manage_members'))
    except Exception as e:
        flash(f'Error loading member: {str(e)}', 'error')
        return redirect(url_for('manage_members'))
    finally:
        cursor.close()
        conn.close()
    
    if request.method == 'POST':
        if 'face_images' not in request.files:
            flash('No files selected', 'error')
            return render_template('register_face.html', member=member)
        
        files = request.files.getlist('face_images')
        success_count = 0
        
        for file in files:
            if file and file.filename != '' and face_utils.allowed_file(file.filename):
                filename = secure_filename(f"member_{member_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                file.save(filepath)
                
                try:
                    face_encoding_path = face_utils.encode_and_save_face(filepath, member_id)
                    if face_encoding_path:
                        conn = database.get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE members SET face_encoding_path = %s WHERE id = %s", (face_encoding_path, member_id))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        success_count += 1
                    else:
                        os.remove(filepath)
                except Exception as e:
                    flash(f'Error processing face image: {str(e)}', 'error')
        
        if success_count > 0:
            flash(f'Successfully registered {success_count} face image(s)!', 'success')
            return redirect(url_for('member_profile', member_id=member_id))
        else:
            flash('No valid face images were processed.', 'error')
    
    return render_template('register_face.html', member=member)

# === EVENT MANAGEMENT ===
@app.route('/events')
@role_required(['admin', 'manager', 'user'])
def manage_events():
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, title, event_date, start_time, end_time, 
                   location, description, created_at, status
            FROM events 
            ORDER BY event_date DESC
        """)
        events = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading events: {str(e)}', 'error')
        events = []
    
    finally:
        cursor.close()
        conn.close()
    
    return render_template('event_management.html', events=events)

@app.route('/events/create', methods=['GET', 'POST'])
@role_required(['admin', 'manager'])
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        event_date = request.form.get('event_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.get('location')
        description = request.form.get('description')
        event_type = request.form.get('event_type')
        
        if not title or not event_date:
            flash('Title and event date are required', 'error')
            return render_template('create_event.html')
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO events (title, event_date, start_time, end_time, 
                                  location, description, event_type, created_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'scheduled')
            """, (title, event_date, start_time, end_time, location, 
                  description, event_type, session['user_id']))
            
            conn.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('manage_events'))
        
        except Exception as e:
            conn.rollback()
            flash(f'Error creating event: {str(e)}', 'error')
        
        finally:
            cursor.close()
            conn.close()
    
    return render_template('create_event.html')

# === FACE RECOGNITION ATTENDANCE ===
@app.route('/events/<int:event_id>/video_attendance')
@role_required(['admin', 'manager'])
def video_attendance(event_id):
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, title, event_date, start_time, end_time FROM events WHERE id = %s", (event_id,))
        event = cursor.fetchone()
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('manage_events'))
    except Exception as e:
        flash(f'Error loading event: {str(e)}', 'error')
        return redirect(url_for('manage_events'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('video_attendance.html', event=event)

@app.route('/api/process_attendance', methods=['POST'])
@role_required(['admin', 'manager'])
def process_attendance():
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        image_data = data.get('image')
        
        if not event_id or not image_data:
            return jsonify({'success': False, 'message': 'Missing data'})
        
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        recognized_members = face_utils.recognize_faces(image)
        
        if recognized_members:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            recognized_at = datetime.now()
            success_count = 0
            recognized_details = []
            
            for member_id, confidence in recognized_members:
                try:
                    cursor.execute("SELECT id FROM attendance WHERE member_id = %s AND event_id = %s", (member_id, event_id))
                    existing_record = cursor.fetchone()
                    
                    if existing_record:
                        cursor.execute("UPDATE attendance SET status = 'present', recognized_at = %s, confidence = %s WHERE id = %s", (recognized_at, confidence, existing_record[0]))
                    else:
                        cursor.execute("INSERT INTO attendance (member_id, event_id, status, recognized_at, confidence) VALUES (%s, %s, %s, %s, %s)", (member_id, event_id, 'present', recognized_at, confidence))
                    
                    success_count += 1
                    cursor.execute("SELECT fullname FROM members WHERE id = %s", (member_id,))
                    member_name = cursor.fetchone()[0]
                    recognized_details.append({'name': member_name, 'confidence': round(confidence * 100, 2)})
                except Exception as e:
                    print(f"Error recording attendance: {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Attendance recorded for {success_count} member(s)',
                'recognized_members': recognized_details,
                'count': success_count
            })
        else:
            return jsonify({'success': False, 'message': 'No recognized faces found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing attendance: {str(e)}'})

# === ANNUAL PLANS AND REPORTS ===
@app.route('/plans/upload', methods=['GET', 'POST'])
@role_required(['admin', 'manager'])
def upload_plan():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        plan_type = request.form.get('plan_type')
        year = request.form.get('year')
        file = request.files.get('plan_file')
        
        if not title or not file:
            flash('Title and file are required', 'error')
            return render_template('upload_plan.html')
        
        if file and allowed_document_file(file.filename):
            filename = secure_filename(f"plan_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'plans', filename)
            file.save(filepath)
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("INSERT INTO annual_plans (title, description, plan_type, year, file_path, uploaded_by, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)", (title, description, plan_type, year, filepath, session['user_id'], datetime.now()))
                conn.commit()
                flash('Plan uploaded successfully!', 'success')
                return redirect(url_for('view_plans'))
            except Exception as e:
                conn.rollback()
                flash(f'Error uploading plan: {str(e)}', 'error')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Invalid file type.', 'error')
    
    current_year = datetime.now().year
    return render_template('upload_plan.html', current_year=current_year)

@app.route('/plans')
@role_required(['admin', 'manager', 'user'])
def view_plans():
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT p.id, p.title, p.description, p.plan_type, p.year,
                   p.file_path, p.uploaded_at, u.fullname as uploaded_by,
                   p.analysis_data
            FROM annual_plans p
            JOIN users u ON p.uploaded_by = u.id
            ORDER BY p.year DESC, p.uploaded_at DESC
        """)
        
        plans = cursor.fetchall()
    
    except Exception as e:
        flash(f'Error loading plans: {str(e)}', 'error')
        plans = []
    
    finally:
        cursor.close()
        conn.close()
    
    return render_template('view_plans.html', plans=plans)

@app.route('/plans/<int:plan_id>/analyze')
@role_required(['admin', 'manager'])
def analyze_plan(plan_id):
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT title, file_path, analysis_data FROM annual_plans WHERE id = %s", (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            flash('Plan not found', 'error')
            return redirect(url_for('view_plans'))
        
        analysis_results = report_analyzer.analyze_document(plan['file_path'])
        cursor.execute("UPDATE annual_plans SET analysis_data = %s, analyzed_at = %s WHERE id = %s", (json.dumps(analysis_results), datetime.now(), plan_id))
        conn.commit()
        return render_template('plan_analysis.html', plan_title=plan['title'], analysis=analysis_results)
    except Exception as e:
        flash(f'Error analyzing plan: {str(e)}', 'error')
        return redirect(url_for('view_plans'))
    finally:
        cursor.close()
        conn.close()

@app.route('/reports')
@role_required(['admin', 'manager'])
def view_reports():
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Membership growth report with MySQL date functions
        cursor.execute("""
            SELECT 
                DATE_FORMAT(join_date, '%Y-%m-01') as month, 
                COUNT(*) as new_members
            FROM members 
            WHERE join_date >= %s
            GROUP BY DATE_FORMAT(join_date, '%Y-%m-01')
            ORDER BY month
        """, (date.today() - timedelta(days=365),))
        
        membership_growth = cursor.fetchall()
        
        # Attendance statistics
        cursor.execute("""
            SELECT 
                e.title, 
                e.event_date, 
                COUNT(a.id) as attendance_count,
                COUNT(DISTINCT a.member_id) as unique_members
            FROM events e
            LEFT JOIN attendance a ON e.id = a.event_id
            WHERE e.event_date >= %s
            GROUP BY e.id, e.title, e.event_date
            ORDER BY e.event_date DESC
        """, (date.today() - timedelta(days=90),))
        
        attendance_stats = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'error')
        membership_growth = attendance_stats = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('reports.html', 
                         membership_growth=membership_growth,
                         attendance_stats=attendance_stats)

def allowed_document_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'xlsx', 'xls'}

if __name__ == '__main__':
    # Test database connection before starting
    if database.test_connection():
        print("✅ Starting Membership System...")
        print("📊 Access at: http://localhost:80")
        print("🔑 Login: admin / admin123")
        if mysql_available:
            print("✅ MySQL integration enabled")
        else:
            print("⚠️  MySQL integration not available")
        app.run(debug=True, host='127.0.0.1 ', port=3306)
    else:
        print("❌ Cannot start application: MySQL connection failed!")