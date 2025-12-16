from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models.database import Database
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    """Get attendance report"""
    role = request.args.get('role', 'student')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    person_id = request.args.get('id')
    
    db = Database()
    
    # Build query
    if role == 'student':
        query = """
            SELECT 
                sa.ID, sf.Name, sf.Course, sf.Sem, sa.Date, sa.CheckIn
            FROM 
                student_attendance sa
            JOIN 
                student_face sf ON sa.ID = sf.ID
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND sa.Date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND sa.Date <= %s"
            params.append(date_to)
        
        if person_id:
            query += " AND sa.ID = %s"
            params.append(person_id)
        
        query += " ORDER BY sa.Date DESC, sa.CheckIn DESC"
        
        results = db.fetch_data(query, tuple(params))
        
        attendance_list = [
            {
                'id': r[0],
                'name': r[1],
                'course': r[2],
                'sem': r[3],
                'date': str(r[4]),
                'check_in': str(r[5])
            }
            for r in results
        ]
    
    else:  # staff
        query = """
            SELECT 
                sa.ID, sf.Name, sf.Dep, sa.Date, sa.CheckIn, sa.CheckOut
            FROM 
                staff_attendance sa
            JOIN 
                staff_face sf ON sa.ID = sf.ID
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND sa.Date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND sa.Date <= %s"
            params.append(date_to)
        
        if person_id:
            query += " AND sa.ID = %s"
            params.append(person_id)
        
        query += " ORDER BY sa.Date DESC, sa.CheckIn DESC"
        
        results = db.fetch_data(query, tuple(params))
        
        attendance_list = [
            {
                'id': r[0],
                'name': r[1],
                'dep': r[2],
                'date': str(r[3]),
                'check_in': str(r[4]) if r[4] else None,
                'check_out': str(r[5]) if r[5] else None
            }
            for r in results
        ]
    
    return jsonify({
        'role': role,
        'data': attendance_list,
        'count': len(attendance_list)
    }), 200

@reports_bp.route('/attendance-sheet', methods=['GET'])
@jwt_required()
def get_attendance_sheet():
    """Get attendance in sheet format (dates as columns)"""
    role = request.args.get('role', 'student')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    person_id = request.args.get('id')
    
    db = Database()
    
    # Get date range
    if not date_from or not date_to:
        from datetime import datetime, timedelta
        date_to = datetime.now().strftime('%Y-%m-%d')
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Generate list of dates
    from datetime import datetime, timedelta
    start = datetime.strptime(date_from, '%Y-%m-%d')
    end = datetime.strptime(date_to, '%Y-%m-%d')
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # Get all persons
    if role == 'student':
        query = "SELECT ID, Name, Course, Sem FROM student_face"
        params = []
        if person_id:
            query += " WHERE ID = %s"
            params.append(person_id)
        query += " ORDER BY ID"
        results = db.fetch_data(query, tuple(params) if params else None)
        persons = [
            {'id': r[0], 'name': r[1], 'course': f"{r[2]} - Sem {r[3]}"}
            for r in results
        ]
    else:
        query = "SELECT ID, Name, Dep FROM staff_face"
        params = []
        if person_id:
            query += " WHERE ID = %s"
            params.append(person_id)
        query += " ORDER BY ID"
        results = db.fetch_data(query, tuple(params) if params else None)
        persons = [
            {'id': r[0], 'name': r[1], 'dep': r[2]}
            for r in results
        ]
    
    # Get all attendance records for date range
    if role == 'student':
        att_query = """
            SELECT ID, Date, CheckIn 
            FROM student_attendance 
            WHERE Date BETWEEN %s AND %s
        """
        if person_id:
            att_query += " AND ID = %s"
            att_results = db.fetch_data(att_query, (date_from, date_to, person_id))
        else:
            att_results = db.fetch_data(att_query, (date_from, date_to))
    else:
        att_query = """
            SELECT ID, Date, CheckIn, CheckOut 
            FROM staff_attendance 
            WHERE Date BETWEEN %s AND %s
        """
        if person_id:
            att_query += " AND ID = %s"
            att_results = db.fetch_data(att_query, (date_from, date_to, person_id))
        else:
            att_results = db.fetch_data(att_query, (date_from, date_to))
    
    # Build attendance dictionary
    attendance = {}
    for record in att_results:
        person_id_rec = record[0]
        date = str(record[1])
        check_in = str(record[2]) if record[2] else None
        check_out = str(record[3]) if len(record) > 3 and record[3] else None
        
        key = f"{person_id_rec}_{date}"
        attendance[key] = {
            'check_in': check_in,
            'check_out': check_out
        }
    
    return jsonify({
        'role': role,
        'persons': persons,
        'dates': dates,
        'attendance': attendance
    }), 200

@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """Get attendance summary"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    db = Database()
    
    # Student attendance count
    student_count = db.fetch_data(
        """
        SELECT COUNT(DISTINCT ID) 
        FROM student_attendance 
        WHERE Date = %s
        """,
        (date,)
    )[0][0]
    
    # Staff attendance count
    staff_count = db.fetch_data(
        """
        SELECT COUNT(DISTINCT ID) 
        FROM staff_attendance 
        WHERE Date = %s
        """,
        (date,)
    )[0][0]
    
    # Total enrolled
    total_students = db.fetch_data("SELECT COUNT(*) FROM student_face")[0][0]
    total_staff = db.fetch_data("SELECT COUNT(*) FROM staff_face")[0][0]
    
    return jsonify({
        'date': date,
        'students_present': student_count,
        'students_total': total_students,
        'staff_present': staff_count,
        'staff_total': total_staff
    }), 200
