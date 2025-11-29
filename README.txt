INSTALLATION INSTRUCTIONS FOR SIMS

1. EXTRACT PROJECT FILES
   - Extract all project files to a directory of your choice

2. CREATE VIRTUAL ENVIRONMENT
   python -m venv venv
   
   On Windows:
   venv\Scripts\activate
   
   On Mac/Linux:
   source venv/bin/activate

3. INSTALL PYTHON DEPENDENCIES
   pip install django
   pip install djangorestframework
   pip install djangorestframework-simplejwt
   pip install django-cors-headers

4. SETUP DATABASE
   python manage.py makemigrations
   python manage.py migrate

5. CREATE ADMIN USER
   python manage.py createsuperuser

6. LOAD SAMPLE DATA (Optional)
   python setup_initial_data.py

7. START DEVELOPMENT SERVER
   python manage.py runserver

8. ACCESS APPLICATION
   Frontend: Open index.html in web browser
   Django Admin: http://localhost:8000/admin/
   API: http://localhost:8000/api/

TEST CREDENTIALS:
- Admin: username=admin, password=admin123
- Teacher: username=teacher1, password=test123
- Student: username=student1, password=test123
- Parent: username=parent1, password=test123

TROUBLESHOOTING:
- If port 8000 is already in use, run: python manage.py runserver 8080
- For database issues, delete db.sqlite3 and run migrations again
- Clear browser cache if frontend doesn't update

For more information, see README.md
