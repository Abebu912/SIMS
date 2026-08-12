document.addEventListener('DOMContentLoaded', function() {
    const roleSelect = document.getElementById('role-select');
    const roleSpecificFields = document.querySelectorAll('.role-specific');
    
    function toggleRoleFields() {
        const selectedRole = roleSelect.value;
        
        // Hide all role-specific fields first
        roleSpecificFields.forEach(field => {
            field.style.display = 'none';
            field.required = false;
        });
        
        // Show fields based on selected role
        if (selectedRole === 'student') {
            document.querySelector('[name="program"]').closest('.form-group').style.display = 'block';
            document.querySelector('[name="program"]').required = true;
        } 
        else if (selectedRole === 'teacher') {
            document.querySelector('[name="department"]').closest('.form-group').style.display = 'block';
            document.querySelector('[name="qualification"]').closest('.form-group').style.display = 'block';
            document.querySelector('[name="department"]').required = true;
            document.querySelector('[name="qualification"]').required = true;
        }
        else if (selectedRole === 'parent') {
            document.querySelector('[name="occupation"]').closest('.form-group').style.display = 'block';
            document.querySelector('[name="relationship"]').closest('.form-group').style.display = 'block';
            document.querySelector('[name="student_id_link"]').closest('.form-group').style.display = 'block';
            document.querySelector('[name="occupation"]').required = true;
            document.querySelector('[name="relationship"]').required = true;
        }
    }
    
    if (roleSelect) {
        roleSelect.addEventListener('change', toggleRoleFields);
        // Initialize on page load
        toggleRoleFields();
    }
});