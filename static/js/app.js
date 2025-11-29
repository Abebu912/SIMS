import auth from "./auth.js"

class SIMSApp {
  constructor() {
    this.currentPage = "dashboard"
    this.init()
  }

  init() {
    this.setupEventListeners()
    this.renderLoginPage()
  }

  setupEventListeners() {
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("nav-link")) {
        e.preventDefault()
        this.currentPage = e.target.dataset.page
        this.render()
      }
      if (e.target.classList.contains("logout-btn")) {
        auth.logout()
        this.renderLoginPage()
      }
    })
  }

  renderLoginPage() {
    document.body.innerHTML = `
            <div class="login-container">
                <div class="login-box">
                    <div class="login-header">
                        <h1 class="login-title">SIMS</h1>
                        <p class="login-subtitle">Student Information Management System</p>
                    </div>
                    <form id="loginForm">
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" id="username" class="form-input" placeholder="Enter username" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" id="password" class="form-input" placeholder="Enter password" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Role</label>
                            <select id="role" class="form-select">
                                <option value="student">Student</option>
                                <option value="teacher">Teacher</option>
                                <option value="parent">Parent</option>
                                <option value="admin">Administrator</option>
                                <option value="registrar">Registrar</option>
                                <option value="finance">Finance Officer</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                    </form>
                </div>
            </div>
        `

    document.getElementById("loginForm").addEventListener("submit", async (e) => {
      e.preventDefault()
      const username = document.getElementById("username").value
      const password = document.getElementById("password").value

      try {
        await auth.login(username, password)
        this.renderApp()
      } catch (error) {
        alert("Login failed: " + error.message)
      }
    })
  }

  renderApp() {
    const user = auth.getUser()
    document.body.innerHTML = `
            <div class="header">
                <div class="container">
                    <div class="header-content">
                        <div class="logo">SIMS</div>
                        <div class="nav-links">
                            <span>Welcome, ${user.first_name}!</span>
                            <div class="user-profile">
                                <div class="avatar">${user.first_name[0]}</div>
                                <button class="logout-btn btn btn-secondary">Logout</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div style="display: flex;">
                <div class="sidebar">
                    <ul class="sidebar-menu">
                        <li><a href="#" class="nav-link" data-page="dashboard">📊 Dashboard</a></li>
                        <li><a href="#" class="nav-link" data-page="courses">📚 Courses</a></li>
                        <li><a href="#" class="nav-link" data-page="grades">📝 Grades</a></li>
                        <li><a href="#" class="nav-link" data-page="payments">💳 Payments</a></li>
                        <li><a href="#" class="nav-link" data-page="notifications">🔔 Notifications</a></li>
                        ${user.role === "admin" ? '<li><a href="#" class="nav-link" data-page="admin">⚙️ Admin</a></li>' : ""}
                        ${user.role === "teacher" ? '<li><a href="#" class="nav-link" data-page="teaching">🎓 Teaching</a></li>' : ""}
                        <li><a href="#" class="nav-link" data-page="ai-advisor">🤖 AI Advisor</a></li>
                    </ul>
                </div>

                <div class="main-content" style="flex: 1;">
                    <div id="content"></div>
                </div>
            </div>
        `

    // Setup event listeners after rendering
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault()
        this.currentPage = e.target.dataset.page
        this.render()
      })
    })

    document.querySelector(".logout-btn").addEventListener("click", () => {
      auth.logout()
      this.renderLoginPage()
    })

    this.render()
  }

  render() {
    const contentDiv = document.getElementById("content")

    if (this.currentPage === "dashboard") {
      this.renderDashboard()
    } else if (this.currentPage === "courses") {
      this.renderCourses()
    } else if (this.currentPage === "grades") {
      this.renderGrades()
    } else if (this.currentPage === "payments") {
      this.renderPayments()
    } else if (this.currentPage === "notifications") {
      this.renderNotifications()
    } else if (this.currentPage === "ai-advisor") {
      this.renderAIAdvisor()
    }
  }

  renderDashboard() {
    const user = auth.getUser()
    const content = document.getElementById("content")

    content.innerHTML = `
            <div class="container">
                <h1 style="margin-bottom: 2rem;">Welcome back, ${user.first_name}!</h1>
                
                <div class="dashboard">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">GPA</div>
                        </div>
                        <div class="card-value">3.75</div>
                        <div class="card-label">Current Semester</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">Courses</div>
                        </div>
                        <div class="card-value">6</div>
                        <div class="card-label">Enrolled Courses</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">Attendance</div>
                        </div>
                        <div class="card-value">95%</div>
                        <div class="card-label">This Semester</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">Fee Status</div>
                        </div>
                        <div class="card-value" style="color: var(--success);">Paid</div>
                        <div class="card-label">All Current Fees</div>
                    </div>
                </div>

                <div style="margin-top: 2rem;">
                    <h2 style="margin-bottom: 1rem;">Quick Actions</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                        <button class="btn btn-primary" onclick="window.location.hash='#courses'">📚 Enroll Courses</button>
                        <button class="btn btn-primary" onclick="window.location.hash='#grades'">📝 View Grades</button>
                        <button class="btn btn-primary" onclick="window.location.hash='#payments'">💳 Pay Fees</button>
                        <button class="btn btn-primary" onclick="window.location.hash='#ai-advisor'">🤖 Ask AI Advisor</button>
                    </div>
                </div>

                <div style="margin-top: 2rem;">
                    <h2 style="margin-bottom: 1rem;">Recent Announcements</h2>
                    <div class="card">
                        <h3>Final Exam Schedule Posted</h3>
                        <p style="color: #666; margin-bottom: 0.5rem;">Dec 15, 2024</p>
                        <p>The final examination schedule has been posted. Please check your course pages for details.</p>
                    </div>
                </div>
            </div>
        `
  }

  renderCourses() {
    const content = document.getElementById("content")
    content.innerHTML = `
            <div class="container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h1>My Courses</h1>
                    <button class="btn btn-primary">+ Enroll Course</button>
                </div>
                
                <table class="table">
                    <thead>
                        <tr>
                            <th>Course Code</th>
                            <th>Course Name</th>
                            <th>Instructor</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>CS101</td>
                            <td>Introduction to Programming</td>
                            <td>Mr. Ahmed Hassan</td>
                            <td><span class="badge badge-success">Active</span></td>
                            <td><button class="btn btn-secondary">View</button></td>
                        </tr>
                        <tr>
                            <td>MATH201</td>
                            <td>Advanced Mathematics</td>
                            <td>Ms. Sarah Johnson</td>
                            <td><span class="badge badge-success">Active</span></td>
                            <td><button class="btn btn-secondary">View</button></td>
                        </tr>
                        <tr>
                            <td>SCI301</td>
                            <td>Physics Laboratory</td>
                            <td>Mr. Michael Brown</td>
                            <td><span class="badge badge-success">Active</span></td>
                            <td><button class="btn btn-secondary">View</button></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `
  }

  renderGrades() {
    const content = document.getElementById("content")
    content.innerHTML = `
            <div class="container">
                <h1 style="margin-bottom: 2rem;">Grades & Transcripts</h1>
                
                <table class="table">
                    <thead>
                        <tr>
                            <th>Course</th>
                            <th>Instructor</th>
                            <th>Score</th>
                            <th>Grade</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Introduction to Programming</td>
                            <td>Mr. Ahmed Hassan</td>
                            <td>92</td>
                            <td>A</td>
                            <td><span class="badge badge-success">Final</span></td>
                        </tr>
                        <tr>
                            <td>Advanced Mathematics</td>
                            <td>Ms. Sarah Johnson</td>
                            <td>88</td>
                            <td>B+</td>
                            <td><span class="badge badge-success">Final</span></td>
                        </tr>
                        <tr>
                            <td>Physics Laboratory</td>
                            <td>Mr. Michael Brown</td>
                            <td>95</td>
                            <td>A</td>
                            <td><span class="badge badge-warning">Pending</span></td>
                        </tr>
                    </tbody>
                </table>

                <div style="margin-top: 2rem;">
                    <button class="btn btn-primary">📥 Download Transcript</button>
                    <button class="btn btn-secondary">🖨️ Print Transcript</button>
                </div>
            </div>
        `
  }

  renderPayments() {
    const content = document.getElementById("content")
    content.innerHTML = `
            <div class="container">
                <h1 style="margin-bottom: 2rem;">Fee Management</h1>
                
                <div class="dashboard" style="margin-bottom: 2rem;">
                    <div class="card">
                        <div class="card-title">Total Owed</div>
                        <div class="card-value">ETB 15,000</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Total Paid</div>
                        <div class="card-value" style="color: var(--success);">ETB 10,000</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Balance</div>
                        <div class="card-value" style="color: var(--danger);">ETB 5,000</div>
                    </div>
                </div>

                <div class="card" style="margin-bottom: 2rem;">
                    <h2>Make Payment</h2>
                    <form>
                        <div class="form-group">
                            <label class="form-label">Amount</label>
                            <input type="number" class="form-input" placeholder="Enter amount" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Payment Method</label>
                            <select class="form-select">
                                <option>Bank Transfer</option>
                                <option>Credit Card</option>
                                <option>Mobile Money</option>
                                <option>Cash</option>
                            </select>
                        </div>
                        <button type="button" class="btn btn-primary">Process Payment</button>
                    </form>
                </div>

                <h2 style="margin-bottom: 1rem;">Payment History</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Amount</th>
                            <th>Method</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Dec 10, 2024</td>
                            <td>ETB 5,000</td>
                            <td>Bank Transfer</td>
                            <td><span class="badge badge-success">Completed</span></td>
                        </tr>
                        <tr>
                            <td>Nov 15, 2024</td>
                            <td>ETB 5,000</td>
                            <td>Credit Card</td>
                            <td><span class="badge badge-success">Completed</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `
  }

  renderNotifications() {
    const content = document.getElementById("content")
    content.innerHTML = `
            <div class="container">
                <h1 style="margin-bottom: 2rem;">Notifications</h1>
                
                <div class="notification success">
                    <strong>✓ Grade Posted</strong>
                    <p>Your grade for Introduction to Programming has been posted. Score: 92/100</p>
                    <small style="color: #999;">2 hours ago</small>
                </div>

                <div class="notification warning">
                    <strong>⚠️ Fee Reminder</strong>
                    <p>Your semester fee is due on December 25, 2024. Outstanding balance: ETB 5,000</p>
                    <small style="color: #999;">1 day ago</small>
                </div>

                <div class="notification info">
                    <strong>📢 Announcement</strong>
                    <p>Final exam schedule has been published. Please review it on the courses page.</p>
                    <small style="color: #999;">3 days ago</small>
                </div>

                <div class="notification success">
                    <strong>✓ Enrollment Confirmed</strong>
                    <p>You have been successfully enrolled in Physics Laboratory.</p>
                    <small style="color: #999;">1 week ago</small>
                </div>
            </div>
        `
  }

  renderAIAdvisor() {
    const content = document.getElementById("content")
    content.innerHTML = `
            <div class="container">
                <h1 style="margin-bottom: 2rem;">🤖 AI Academic Advisor</h1>
                
                <div class="chat-container">
                    <div class="chat-messages">
                        <div class="message ai">
                            <div class="message-bubble">
                                Hello! I'm your AI Academic Advisor. I can help you with course recommendations, study tips, and academic guidance. What would you like to know?
                            </div>
                        </div>
                        <div class="message user">
                            <div class="message-bubble">
                                What courses should I take next semester?
                            </div>
                        </div>
                        <div class="message ai">
                            <div class="message-bubble">
                                Based on your excellent GPA of 3.75 and strong performance in STEM subjects, I recommend:
                                <br>1. Advanced Mathematics - Builds on your current skills
                                <br>2. Physics Laboratory - Complements your programming background
                                <br>3. Data Structures - Perfect next step after Introduction to Programming
                            </div>
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="aiInput" placeholder="Type your question...">
                        <button onclick="sendAIMessage()">Send</button>
                    </div>
                </div>

                <div style="margin-top: 2rem;">
                    <h2 style="margin-bottom: 1rem;">Recommended Courses</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Course</th>
                                <th>Reason</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Advanced Mathematics</td>
                                <td>Your strong GPA indicates readiness for advanced coursework.</td>
                                <td><span class="badge badge-success">95%</span></td>
                            </tr>
                            <tr>
                                <td>Physics Laboratory</td>
                                <td>Complements your programming skills well.</td>
                                <td><span class="badge badge-success">90%</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `
  }
}

function sendAIMessage() {
  const input = document.getElementById("aiInput")
  const message = input.value
  if (message.trim()) {
    console.log("[v0] Sending message:", message)
    input.value = ""
  }
}

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  window.app = new SIMSApp()
})
