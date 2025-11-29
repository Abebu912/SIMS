from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AIConversation, AIMessage, SubjectRecommendation
from .serializers import AIConversationSerializer, AIMessageSerializer, SubjectRecommendationSerializer
from ranks.models import Grade
from subjects.models import Subject
from django.db.models import Avg
from django.shortcuts import get_object_or_404

class AIConversationViewSet(viewsets.ModelViewSet):
    serializer_class = AIConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Added error handling for student_profile
        try:
            student = self.request.user.student_profile
            return AIConversation.objects.filter(user=self.request.user)
        except AttributeError:
            # Handle case where student_profile doesn't exist
            return AIConversation.objects.none()
    
    def perform_create(self, serializer):
        # Ensure user is set when creating conversation
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        user_message = request.data.get("message", "")
        
        if not user_message:
            return Response(
                {"error": "Message content is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        AIMessage.objects.create(
            conversation=conversation,
            content=user_message,
            is_user=True
        )
        
        # Generate AI response
        try:
            ai_response = self._generate_ai_response(user_message, self.request.user)
        except Exception as e:
            ai_response = "I'm sorry, I'm having trouble helping right now. Please try again!"
        
        # Create AI message
        ai_msg = AIMessage.objects.create(
            conversation=conversation,
            content=ai_response,
            is_user=False
        )
        
        return Response({
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": ai_msg.created_at
        }, status=status.HTTP_201_CREATED)
    
    def _generate_ai_response(self, user_input, user):
        user_input_lower = user_input.lower()
        
        # Grade 1 specific responses
        if any(word in user_input_lower for word in ['grade 1', 'first grade', 'grade one']):
            return "First grade is so much fun! You'll learn reading, basic math, science about animals and plants, and lots of fun activities! What's your favorite thing to learn?"
        
        # Subject requests
        elif any(word in user_input_lower for word in ['subjects', 'classes', 'learn what']):
            return "In first grade, you'll have fun learning: 📚 Reading and stories, ➕ Math with numbers, 🌱 Science about plants and animals, 🎨 Art and drawing, 🎵 Music and songs! Which one sounds most fun to you?"
        
        # Science requests - fixed spelling detection
        elif any(word in user_input_lower for word in ['science', 'scince', 'sciense', 'experiment', 'animal', 'plant', 'weather']):
            return "Science is amazing! In first grade, you'll learn about: 🐻 Animals and their homes, 🌻 Plants and how they grow, 🌞 Weather and seasons, 🪨 Rocks and soil. Would you like to know more about animals, plants, or weather?"
        
        # Math requests
        elif any(word in user_input_lower for word in ['math', 'mathematics', 'number', 'count', 'add', 'subtract']):
            return "Math is fun with numbers! In first grade, you'll learn: 1️⃣ Counting to 100, 2️⃣ Adding and subtracting, 3️⃣ Shapes and patterns, 4️⃣ Measuring things. Would you like to practice counting or learn about shapes?"
        
        # Reading requests
        elif any(word in user_input_lower for word in ['reading', 'read', 'book', 'story', 'alphabet']):
            return "Reading opens up wonderful stories! In first grade, you'll: 📖 Learn new words, 🔤 Master the alphabet, 📚 Read fun stories, ✍️ Write your own sentences. What kind of stories do you like - animals, adventures, or fairy tales?"
        
        # Homework help
        elif any(word in user_input_lower for word in ['homework', 'assignment', 'help me']):
            return "I'd love to help with homework! Is it for: 📝 Reading practice, 🧮 Math problems, 🔬 Science questions, or ✏️ Writing practice? Tell me what you're working on!"
        
        # Study help
        elif any(word in user_input_lower for word in ['study', 'learn how', 'practice']):
            return "Great question! Here are fun ways to study: 🎵 Sing your ABCs or counting songs, 🎨 Draw pictures of what you learn, 🧩 Use colorful flashcards, ⏰ Practice for 15 minutes each day. What subject do you want to practice?"
        
        # Greetings
        elif any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "Hello! I'm your learning helper! I can help with: 📚 School subjects, 🧮 Math problems, 📖 Reading help, 🔬 Science facts, or 🎯 Study tips. What would you like to learn about today?"
        
        # Feelings/emotions
        elif any(word in user_input_lower for word in ['sad', 'happy', 'excited', 'nervous', 'scared']):
            if 'sad' in user_input_lower or 'scared' in user_input_lower or 'nervous' in user_input_lower:
                return "It's okay to have feelings! Learning new things can be tricky sometimes, but you're doing great! Remember: everyone learns at their own pace. What can I help you with to make it more fun?"
            else:
                return "That's wonderful! Being excited about learning is awesome! What are you most excited to learn about?"
        
        # Default response - more engaging for kids
        else:
            fun_responses = [
                "I'd love to help you learn! You can ask me about: reading stories, math games, science facts, or fun learning activities!",
                "What would you like to explore today? We can talk about numbers, animals, stories, or anything you're learning in school!",
                "Learning is an adventure! Tell me what you're curious about - I know lots about first grade subjects!",
                "I'm here to make learning fun! Want to talk about counting, reading, science, or something else you're learning?"
            ]
            import random
            return random.choice(fun_responses)
    
    def _recommend_subjects(self, user):
        try:
            # Get student profile
            student = user.student_profile
            
            # Get recommended subjects (excluding already enrolled ones)
            recommended_subjects = Subject.objects.exclude(
                enrollments__student=student
            )[:5]
            
            if recommended_subjects.exists():
                subjects_text = ", ".join([s.name for s in recommended_subjects])
                return f"Here are some fun subjects you might enjoy: {subjects_text}. These would be great for you to try next!"
            else:
                return "You're doing great in all your subjects! Keep up the good work!"
                
        except Exception as e:
            return "I think you'd enjoy trying some new learning activities! What are your favorite things to learn about?"
    
    def _discuss_grades(self, user):
        try:
            student = user.student_profile
            grades = Grade.objects.filter(enrollment__student=student)
            if grades.exists():
                avg = grades.aggregate(avg=Avg("score"))["avg"] or 0
                count = grades.count()
                return f"You've completed {count} subjects with an average score of {avg:.1f}%. That's fantastic! Keep up the great work!"
            else:
                return "You're just getting started! Learning is fun and I'm here to help you do your best!"
        except Exception as e:
            return "You're doing great in school! Learning new things is what's most important."
    
    def _homework_help(self, user_input):
        help_responses = [
            "I'd love to help with your homework! Can you tell me which subject it's for?",
            "Homework can be tricky sometimes. What specific problem are you working on?",
            "Let's tackle this homework together! What part are you finding difficult?",
            "I'm here to help with homework! Which subject do you need help with - math, reading, science, or something else?"
        ]
        import random
        return random.choice(help_responses)

class SubjectRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubjectRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            student = self.request.user.student_profile
            return SubjectRecommendation.objects.filter(student=student).order_by("-confidence_score")
        except AttributeError:
            return SubjectRecommendation.objects.none()

# Additional helper views for elementary students
class StudyTipsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get study tips appropriate for the student's grade level"""
        try:
            # Simple study tips for elementary students
            tips = [
                "Find a quiet place to do your homework",
                "Take short breaks between subjects",
                "Ask for help when you don't understand something",
                "Read for 20 minutes every day",
                "Practice math facts while having fun",
                "Use colors and drawings to help remember things",
                "Try to explain what you learned to someone else"
            ]
            return Response({"tips": tips})
        except Exception as e:
            return Response({"tips": ["Find a quiet spot to study and take breaks when you need to!"]})

class LearningActivitiesViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get fun learning activities"""
        activities = [
            "Read a book about your favorite animal",
            "Practice math with cooking measurements",
            "Write a short story about an adventure",
            "Draw a picture of what you learned today",
            "Create flashcards for new vocabulary words",
            "Build something with blocks or LEGO to practice shapes",
            "Sing educational songs to remember facts"
        ]
        return Response({"activities": activities})