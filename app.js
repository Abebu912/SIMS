const API_BASE = "http://localhost:8000/api"
let currentUser = null
let authToken = localStorage.getItem("authToken")

function initApp() {
  if (authToken) {
    loadUserProfile()
    renderDashboard()
  } else {
    renderLoginPage()
  }
}

async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
  const data = await response.json()
  if (data.access) {
    authToken = data.access
    localStorage.setItem("authToken", authToken)
    loadUserProfile()
    renderDashboard()
  }
}

async function register(formData) {
  const response = await fetch(`${API_BASE}/users/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  })
  return await response.json()
}

async function loadUserProfile() {
  const response = await fetch(`${API_BASE}/users/profile/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  currentUser = await response.json()
}

function logout() {
  authToken = null
  currentUser = null
  localStorage.removeItem("authToken")
  renderLoginPage()
}

function renderLoginPage() {
  const app = document.getElementById("app")
  app.innerHTML = `
        <div style="display: flex; height: 100vh; align-items: center; justify-content: center; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);">
            <div class="form-container" style="background: white; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                <h1 style="color: #2563eb; margin-bottom: 1rem; text-align: center;">SIMS</h1>
                <p style="text-align: center; color: #6b7280; margin-bottom: 2rem;">Student Information Management System</p>
                <form onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%; margin-bottom: 1rem;">Login</button>
                    <p style="text-align: center; color: #6b7280;">Don't have an account? <a href="#" onclick="renderRegisterPage(); return false;" style="color: #2563eb; font-weight: 600;">Register</a></p>
                </form>
            </div>
        </div>
    `
}

function renderRegisterPage() {
  const app = document.getElementById("app")
  app.innerHTML = `
        <div style="display: flex; height: 100vh; align-items: center; justify-content: center; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);">
            <div class="form-container" style="background: white; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                <h1 style="color: #2563eb; margin-bottom: 1rem; text-align: center;">Create Account</h1>
                <form onsubmit="handleRegister(event)">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label for="role">Role</label>
                        <select id="role" name="role" required>
                            <option value="student">Student</option>
                            <option value="parent">Parent</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%; margin-bottom: 1rem;">Register</button>
                    <p style="text-align: center; color: #6b7280;">Already have an account? <a href="#" onclick="renderLoginPage(); return false;" style="color: #2563eb; font-weight: 600;">Login</a></p>
                </form>
            </div>
        </div>
    `
}

function renderDashboard() {
  const app = document.getElementById("app")
  const role = currentUser.role

  app.innerHTML = `
        <header>
            <div class="container">
                <div class="header-content">
                    <a href="#" class="logo" onclick="renderDashboard(); return false;">SIMS</a>
                    <nav>
                        <span style="color: #6b7280;">Welcome, ${currentUser.first_name || currentUser.username}</span>
                        <button class="btn btn-outline" onclick="logout()">Logout</button>
                    </nav>
                </div>
            </div>
        </header>
        <div class="container" style="padding-top: 2rem; padding-bottom: 4rem;">
            <div class="dashboard">
                <aside class="sidebar">
                    <div class="sidebar-nav">
                        <a href="#" onclick="showStudents(); return false;" class="nav-link active">Students</a>
                        <a href="#" onclick="showCourses(); return false;" class="nav-link">Courses</a>
                        <a href="#" onclick="showGrades(); return false;" class="nav-link">Grades</a>
                        <a href="#" onclick="showPayments(); return false;" class="nav-link">Payments</a>
                        <a href="#" onclick="showNotifications(); return false;" class="nav-link">Notifications</a>
                        <a href="#" onclick="showAIAdvisor(); return false;" class="nav-link">AI Advisor</a>
                        ${role === "admin" ? '<a href="#" onclick="showAdminPanel(); return false;" class="nav-link">Admin</a>' : ""}
                    </div>
                </aside>
                <main class="main-content">
                    <div id="content-area">
                        <h2>${role === "admin" ? "Admin Dashboard" : role === "teacher" ? "Teacher Dashboard" : role === "student" ? "Student Portal" : "Parent Portal"}</h2>
                        <p>Welcome to SIMS. Select an option from the sidebar to get started.</p>
                    </div>
                </main>
            </div>
        </div>
    `
}

async function showStudents() {
  const response = await fetch(`${API_BASE}/students/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const students = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Students</h2>
        <button class="btn btn-primary" onclick="showAddStudentForm()">Add Student</button>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Student ID</th>
                        <th>Name</th>
                        <th>Grade</th>
                        <th>Email</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.results
                      .map(
                        (s) => `
                        <tr>
                            <td>${s.student_id}</td>
                            <td>${s.user_name}</td>
                            <td>Grade ${s.grade_level}</td>
                            <td>${s.user_email || "N/A"}</td>
                            <td><span class="badge badge-success">${s.is_active ? "Active" : "Inactive"}</span></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function showCourses() {
  const response = await fetch(`${API_BASE}/courses/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const courses = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Courses</h2>
        <button class="btn btn-primary" onclick="showAddCourseForm()">Add Course</button>
        <div class="card-grid" style="margin-top: 2rem;">
            ${courses.results
              .map(
                (c) => `
                <div class="card">
                    <h3>${c.code}</h3>
                    <p style="font-weight: 600; margin-bottom: 0.5rem;">${c.name}</p>
                    <p>${c.description || "No description"}</p>
                    <p style="color: #2563eb; font-weight: 600;">Credits: ${c.credits}</p>
                </div>
            `,
              )
              .join("")}
        </div>
    `
}

async function showGrades() {
  const response = await fetch(`${API_BASE}/grades/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const grades = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Grades</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Course</th>
                        <th>Score</th>
                        <th>Grade</th>
                        <th>Feedback</th>
                    </tr>
                </thead>
                <tbody>
                    ${grades.results
                      .map(
                        (g) => `
                        <tr>
                            <td>${g.enrollment}</td>
                            <td>${g.score}</td>
                            <td><span class="badge badge-success">${g.grade_letter}</span></td>
                            <td>${g.feedback || "N/A"}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function showPayments() {
  const response = await fetch(`${API_BASE}/payments/my_payments/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const payments = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Payments</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Due Date</th>
                        <th>Payment Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${payments
                      .map(
                        (p) => `
                        <tr>
                            <td>${p.amount}</td>
                            <td><span class="badge ${p.status === "completed" ? "badge-success" : "badge-warning"}">${p.status}</span></td>
                            <td>${p.due_date}</td>
                            <td>${p.payment_date}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function showNotifications() {
  const response = await fetch(`${API_BASE}/notifications/unread/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const notifications = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Notifications</h2>
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            ${notifications
              .map(
                (n) => `
                <div style="background: #f0f9ff; border-left: 4px solid #2563eb; padding: 1rem; border-radius: 4px;">
                    <h4>${n.title}</h4>
                    <p>${n.message}</p>
                    <small style="color: #6b7280;">${new Date(n.created_at).toLocaleDateString()}</small>
                </div>
            `,
              )
              .join("")}
        </div>
    `
}

function showAddStudentForm() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Add New Student</h2>
        <form onsubmit="handleAddStudent(event)" class="form-container">
            <div class="form-group">
                <label>Student ID</label>
                <input type="text" id="student_id" required>
            </div>
            <div class="form-group">
                <label>First Name</label>
                <input type="text" id="first_name" required>
            </div>
            <div class="form-group">
                <label>Grade Level</label>
                <select id="grade_level" required>
                    <option value="">Select Grade</option>
                    ${Array.from({ length: 8 }, (_, i) => `<option value="${i + 1}">Grade ${i + 1}</option>`).join("")}
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Add Student</button>
            <button type="button" class="btn btn-outline" onclick="showStudents()">Cancel</button>
        </form>
    `
}

function showAddCourseForm() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Add New Course</h2>
        <form onsubmit="handleAddCourse(event)" class="form-container">
            <div class="form-group">
                <label>Course Code</label>
                <input type="text" id="code" required>
            </div>
            <div class="form-group">
                <label>Course Name</label>
                <input type="text" id="name" required>
            </div>
            <div class="form-group">
                <label>Credits</label>
                <input type="number" id="credits" value="3" required>
            </div>
            <button type="submit" class="btn btn-primary">Add Course</button>
            <button type="button" class="btn btn-outline" onclick="showCourses()">Cancel</button>
        </form>
    `
}

async function handleLogin(event) {
  event.preventDefault()
  const username = document.getElementById("username").value
  const password = document.getElementById("password").value
  await login(username, password)
}

async function handleRegister(event) {
  event.preventDefault()
  const formData = {
    username: document.getElementById("username").value,
    email: document.getElementById("email").value,
    password: document.getElementById("password").value,
    role: document.getElementById("role").value,
  }
  const result = await register(formData)
  if (result.id) {
    alert("Registration successful. Please login.")
    renderLoginPage()
  }
}

async function handleAddStudent(event) {
  event.preventDefault()
  // Form submission logic here
  showStudents()
}

async function handleAddCourse(event) {
  event.preventDefault()
  // Form submission logic here
  showCourses()
}

// AI Advisor functions
async function showAIAdvisor() {
  const response = await fetch(`${API_BASE}/ai/conversations/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const conversations = await response.json()

  let conversationId = null
  if (conversations.results && conversations.results.length > 0) {
    conversationId = conversations.results[0].id
  }

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>AI Academic Advisor</h2>
        <div style="background: #f0f9ff; border: 2px solid #2563eb; border-radius: 8px; padding: 2rem; max-width: 800px;">
            <div id="chat-box" style="height: 400px; overflow-y: auto; background: white; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e5e7eb;">
                <div style="text-align: center; color: #6b7280; padding: 2rem;">
                    <p>Ask me anything about your courses, grades, or academic path!</p>
                </div>
            </div>
            <form onsubmit="sendAIMessage(event, ${conversationId})" style="display: flex; gap: 0.5rem;">
                <input type="text" id="ai-message-input" placeholder="Ask me a question..." style="flex: 1;">
                <button type="submit" class="btn btn-primary">Send</button>
            </form>
        </div>
    `
}

async function sendAIMessage(event, conversationId) {
  event.preventDefault()
  const message = document.getElementById("ai-message-input").value

  if (!message.trim()) return

  // Create new conversation if needed
  if (!conversationId) {
    const createResp = await fetch(`${API_BASE}/ai/conversations/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${authToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    })
    const newConv = await createResp.json()
    conversationId = newConv.id
  }

  // Send message
  const response = await fetch(`${API_BASE}/ai/conversations/${conversationId}/send_message/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${authToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  })

  const data = await response.json()
  const chatBox = document.getElementById("chat-box")

  chatBox.innerHTML += `
        <div style="margin-bottom: 1rem; text-align: right;">
            <div style="background: #dbeafe; border-radius: 8px; padding: 0.75rem 1rem; display: inline-block; max-width: 70%;">
                ${data.user_message}
            </div>
        </div>
        <div style="margin-bottom: 1rem; text-align: left;">
            <div style="background: #ecfdf5; border-radius: 8px; padding: 0.75rem 1rem; display: inline-block; max-width: 70%;">
                ${data.ai_response}
            </div>
        </div>
    `

  chatBox.scrollTop = chatBox.scrollHeight
  document.getElementById("ai-message-input").value = ""
}

// Initialize app on load
document.addEventListener("DOMContentLoaded", initApp)
