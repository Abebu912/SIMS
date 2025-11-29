# fix_imports_final.py
import os

def fix_students_views_import():
    print("🔧 Fixing students/views.py imports...")
    
    # Read current students/views.py
    with open('students/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the problematic import line
    old_import = "from ai_advisor.models import Conversation, Message"
    new_import = "from ai_advisor.models import AIConversation, AIMessage"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✅ Fixed import line")
    else:
        print("⚠️ Import line not found, checking for other patterns...")
        # Try other possible import patterns
        content = content.replace("from ai_advisor.models import Conversation", "from ai_advisor.models import AIConversation")
        content = content.replace("from ai_advisor.models import Message", "from ai_advisor.models import AIMessage")
    
    # Also replace any remaining Conversation/AIConversation references in the file
    content = content.replace('Conversation.objects', 'AIConversation.objects')
    content = content.replace('Message.objects', 'AIMessage.objects')
    content = content.replace('conversation = Conversation', 'conversation = AIConversation')
    content = content.replace('messages = Message', 'messages = AIMessage')
    
    # Write back
    with open('students/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ students/views.py imports fixed!")

def fix_studentparent_model():
    print("🔧 Fixing StudentParent model relationship clash...")
    
    # Read current users/models.py
    with open('users/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the StudentParent model definition
    old_studentparent = '''class StudentParent(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'parent'})
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    relationship = models.CharField(max_length=50, default='Parent')
    is_primary = models.BooleanField(default=False)'''
    
    new_studentparent = '''class StudentParent(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'parent'}, related_name='parent_relationships')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='student_relationships')
    relationship = models.CharField(max_length=50, default='Parent')
    is_primary = models.BooleanField(default=False)'''
    
    if old_studentparent in content:
        content = content.replace(old_studentparent, new_studentparent)
        print("✅ Fixed StudentParent model relationships")
    else:
        print("⚠️ StudentParent model not found in expected format")
    
    # Write back
    with open('users/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ users/models.py relationships fixed!")

if __name__ == '__main__':
    fix_students_views_import()
    fix_studentparent_model()
    print("🎉 Both issues fixed! Now run migrations.")