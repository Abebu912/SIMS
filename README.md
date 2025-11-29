# Student Information Management System (SIMS)

## Overview
A comprehensive web-based Student Information Management System for Ginba Junior School, built with Django backend and modern HTML/CSS/JavaScript frontend.

## Features

### Authentication & Authorization
- JWT token-based authentication
- Role-based access control (Admin, Teacher, Student, Parent, Registrar, Finance Officer)
- Secure password management

### Core Features

#### Admin Dashboard
- System statistics and metrics
- User management (create, edit, delete)
- System settings configuration
- Comprehensive reporting:
  - Enrollment reports
  - Financial reports
  - Performance reports
  - Attendance reports
  - CSV export functionality

#### Teacher Dashboard
- Manage assigned courses
- Enter and track student grades
- View class rosters
- Post class announcements
- Access performance analytics

#### Student Portal
- View enrolled courses
- Check grades and transcripts
- Monitor payment status
- Make online payments
- Interact with AI Academic Advisor
- Receive notifications

#### Parent Portal
- Monitor child's academic performance
- Track attendance records
- View payment history
- Make fee payments online
- Receive real-time notifications

### Advanced Features
- **AI Academic Advisor**: Intelligent course recommendations and academic guidance
- **Real-time Notifications**: Grade updates, payment reminders, announcements
- **Financial Management**: Automated fee tracking, payment processing, financial reports
- **Transcript Management**: Generate and download official transcripts
- **Attendance Tracking**: Automated attendance records and analytics

## Technology Stack

### Backend
- **Framework**: Django with Django REST Framework
- **Database**: SQLite (production-ready with PostgreSQL migration option)
- **Authentication**: JWT (JSON Web Tokens)
- **API**: RESTful API with comprehensive endpoints

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with flexbox and grid
- **JavaScript**: Vanilla JS with modern ES6+ syntax

### Key Libraries
- djangorestframework-simplejwt: JWT authentication
- django-cors-headers: CORS support
- rest-framework: API framework

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Virtual environment tool

### Backend Setup

1. **Create virtual environment**
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

2. **Install dependencies**
\`\`\`bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers
\`\`\`

3. **Initialize database**
\`\`\`bash
python manage.py makemigrations
python manage.py migrate
python setup_initial_data.py
\`\`\`

4. **Create superuser**
\`\`\`bash
python manage.py createsuperuser
\`\`\`

5. **Run development server**
\`\`\`bash
python manage.py runserver
\`\`\`

### Frontend Setup

1. Open `index.html` in a modern web browser
2. Update API_BASE URL in JavaScript files if needed
3. Login with test credentials:
   - Admin: `admin` / `admin123`
   - Teacher: `teacher1` / `test123`
   - Student: `student1` / `test123`

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token

### Users
- `GET/POST /api/users/` - List/create users
- `GET /api/users/profile/` - Get current user profile
- `POST /api/users/register/` - User registration

### Students
- `GET/POST /api/students/` - List/create students
- `GET /api/students/my_profile/` - Get student profile
- `GET/POST /api/students/attendance/` - Manage attendance

### Courses
- `GET/POST /api/courses/` - List/create courses
- `GET/POST /api/courses/enrollments/` - Manage enrollments
- `POST /api/courses/enrollments/enroll/` - Enroll in course

### Grades
- `GET/POST /api/grades/` - Manage grades
- `GET /api/grades/transcripts/` - Manage transcripts
- `GET /api/grades/my_transcript/` - Get student transcript

### Payments
- `GET/POST /api/payments/` - Manage payments
- `GET /api/payments/fees/` - List fee structures
- `POST /api/payments/process_payment/` - Process payment

### Notifications
- `GET /api/notifications/` - List notifications
- `POST /api/notifications/mark_as_read/` - Mark as read
- `GET /api/notifications/unread/` - Get unread notifications

### AI Advisor
- `GET/POST /api/ai/conversations/` - Manage conversations
- `POST /api/ai/conversations/{id}/send_message/` - Send AI message
- `GET /api/ai/recommendations/` - Get course recommendations

## Database Models

### User Model
- CustomUser (extends Django User)
- Roles: admin, teacher, student, parent, registrar, finance

### Student
- Student profile with enrollment info
- Grade level and enrollment date
- Links to parent account

### Course
- Course details (code, name, credits)
- Teacher assignment
- Enrollment capacity

### Enrollment
- Links students to courses
- Tracks enrollment status
- Timestamps

### Grade
- Student grades per course
- Letter grades and numerical scores
- Feedback for students

### Payment
- Fee tracking
- Payment status (pending/completed/failed)
- Transaction history

### Notification
- System notifications
- Read/unread status
- Multiple notification types

## Security Features

- JWT-based authentication with token refresh
- Role-based access control (RBAC)
- CORS configuration for API security
- Input validation and sanitization
- SQL injection prevention via ORM
- CSRF protection on forms

## File Structure

\`\`\`
sims/
├── manage.py
├── sims/
│   ├── settings.py       # Django settings
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI config
├── users/               # User management app
├── students/            # Student management app
├── courses/             # Course management app
├── grades/              # Grade management app
├── payments/            # Payment management app
├── notifications/       # Notification app
├── ai_advisor/          # AI advisor app
├── index.html           # Frontend entry point
├── styles.css           # Global styles
├── app.js               # Main app logic
├── admin-dashboard.js   # Admin features
├── teacher-dashboard.js # Teacher features
├── student-portal.js    # Student features
└── parent-portal.js     # Parent features
\`\`\`

## Usage Guide

### For Students
1. Login with student credentials
2. Enroll in available courses
3. Check grades and transcripts
4. Make online fee payments
5. Chat with AI advisor for course recommendations

### For Teachers
1. Login with teacher credentials
2. View assigned courses
3. Enter student grades
4. Post course announcements
5. Track class performance

### For Parents
1. Login with parent credentials
2. Select child to monitor
3. View grades and attendance
4. Make fee payments
5. Receive notifications

### For Admins
1. Login with admin credentials
2. Manage users and system settings
3. Generate comprehensive reports
4. Monitor system statistics
5. Configure fee structures

## Troubleshooting

### Database Issues
- Delete `db.sqlite3` and run migrations again
- Check that all app models are in `INSTALLED_APPS`

### Authentication Errors
- Verify JWT token expiration settings
- Clear browser localStorage and login again
- Check CORS configuration

### API Connection Errors
- Confirm backend server is running
- Update API_BASE URL in JavaScript files
- Check network connectivity

## Future Enhancements

- Mobile app development (React Native/Flutter)
- Advanced analytics dashboards
- Parent-teacher communication portal
- Document management system
- Integration with SMS/Email gateways
- Biometric attendance system
- Advanced reporting with charts and graphs

## Support

For issues or questions, contact the development team or refer to the comprehensive documentation in the codebase.

## License

This project is developed for Ginba Junior School and maintained by the development team.
