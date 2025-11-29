const API_BASE = "https://api.example.com" // Declare API_BASE variable
const authToken = "your_auth_token_here" // Declare authToken variable

async function showAdminPanel() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <div>
            <h2>Administration Panel</h2>
            <div class="card-grid" style="margin-bottom: 2rem;">
                <div class="card" onclick="showSystemStats()" style="cursor: pointer;">
                    <h3>📊 System Statistics</h3>
                    <p>View overall system metrics</p>
                </div>
                <div class="card" onclick="showUserManagement()" style="cursor: pointer;">
                    <h3>👥 User Management</h3>
                    <p>Manage system users</p>
                </div>
                <div class="card" onclick="showReports()" style="cursor: pointer;">
                    <h3>📈 Reports</h3>
                    <p>Generate system reports</p>
                </div>
                <div class="card" onclick="showSystemSettings()" style="cursor: pointer;">
                    <h3>⚙️ Settings</h3>
                    <p>Configure system settings</p>
                </div>
            </div>
        </div>
    `
}

async function showSystemStats() {
  const response = await fetch(`${API_BASE}/students/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const studentsData = await response.json()
  const studentCount = studentsData.count || 0

  const coursesResp = await fetch(`${API_BASE}/courses/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const coursesData = await coursesResp.json()
  const courseCount = coursesData.count || 0

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>System Statistics</h2>
        <div class="card-grid">
            <div class="card">
                <h3>${studentCount}</h3>
                <p>Total Students</p>
            </div>
            <div class="card">
                <h3>${courseCount}</h3>
                <p>Active Courses</p>
            </div>
            <div class="card">
                <h3>${Math.floor(Math.random() * 100)}</h3>
                <p>Pending Payments</p>
            </div>
            <div class="card">
                <h3>${Math.floor(Math.random() * 50)}</h3>
                <p>New Notifications</p>
            </div>
        </div>
    `
}

async function showUserManagement() {
  const response = await fetch(`${API_BASE}/users/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const users = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>User Management</h2>
        <button class="btn btn-primary" onclick="showCreateUserForm()">Create New User</button>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.results
                      .map(
                        (u) => `
                        <tr>
                            <td>${u.username}</td>
                            <td>${u.email}</td>
                            <td><span class="badge badge-success">${u.role}</span></td>
                            <td>
                                <button class="btn btn-outline" style="font-size: 0.85rem; padding: 6px 12px;">Edit</button>
                                <button class="btn btn-outline" style="font-size: 0.85rem; padding: 6px 12px; color: #ef4444; border-color: #ef4444;">Delete</button>
                            </td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

function showCreateUserForm() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Create New User</h2>
        <form onsubmit="handleCreateUser(event)" class="form-container">
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" required>
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="email" required>
            </div>
            <div class="form-group">
                <label>Role</label>
                <select id="role" required>
                    <option value="student">Student</option>
                    <option value="teacher">Teacher</option>
                    <option value="parent">Parent</option>
                    <option value="admin">Admin</option>
                    <option value="registrar">Registrar</option>
                    <option value="finance">Finance Officer</option>
                </select>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Create User</button>
            <button type="button" class="btn btn-outline" onclick="showUserManagement()">Cancel</button>
        </form>
    `
}

async function showReports() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Reports</h2>
        <div class="card-grid">
            <div class="card" onclick="generateEnrollmentReport()" style="cursor: pointer;">
                <h3>Enrollment Report</h3>
                <p>Student enrollment statistics</p>
            </div>
            <div class="card" onclick="generateFinancialReport()" style="cursor: pointer;">
                <h3>Financial Report</h3>
                <p>Fee collection and payments</p>
            </div>
            <div class="card" onclick="generatePerformanceReport()" style="cursor: pointer;">
                <h3>Performance Report</h3>
                <p>Academic performance metrics</p>
            </div>
            <div class="card" onclick="generateAttendanceReport()" style="cursor: pointer;">
                <h3>Attendance Report</h3>
                <p>Student attendance summary</p>
            </div>
        </div>
    `
}

async function generateEnrollmentReport() {
  const response = await fetch(`${API_BASE}/courses/enrollments/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const enrollments = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Enrollment Report</h2>
        <button class="btn btn-primary" onclick="exportToCSV('enrollment-report')">Export as CSV</button>
        <div class="table-container">
            <table id="enrollment-report">
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Course</th>
                        <th>Enrolled Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${enrollments.results
                      .map(
                        (e) => `
                        <tr>
                            <td>${e.student}</td>
                            <td>${e.course}</td>
                            <td>${new Date(e.enrolled_at).toLocaleDateString()}</td>
                            <td><span class="badge badge-success">${e.status}</span></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function generateFinancialReport() {
  const response = await fetch(`${API_BASE}/payments/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const payments = await response.json()

  let totalCollected = 0
  let totalPending = 0

  payments.results.forEach((p) => {
    if (p.status === "completed") totalCollected += Number.parseFloat(p.amount)
    else if (p.status === "pending") totalPending += Number.parseFloat(p.amount)
  })

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Financial Report</h2>
        <div class="card-grid" style="margin-bottom: 2rem;">
            <div class="card">
                <h3>$${totalCollected.toFixed(2)}</h3>
                <p>Total Collected</p>
            </div>
            <div class="card">
                <h3>$${totalPending.toFixed(2)}</h3>
                <p>Pending Payments</p>
            </div>
            <div class="card">
                <h3>${payments.results.length}</h3>
                <p>Total Transactions</p>
            </div>
        </div>
        <button class="btn btn-primary" onclick="exportToCSV('financial-report')">Export as CSV</button>
        <div class="table-container">
            <table id="financial-report">
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${payments.results
                      .map(
                        (p) => `
                        <tr>
                            <td>${p.student}</td>
                            <td>$${p.amount}</td>
                            <td><span class="badge ${p.status === "completed" ? "badge-success" : "badge-warning"}">${p.status}</span></td>
                            <td>${new Date(p.payment_date).toLocaleDateString()}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function generatePerformanceReport() {
  const response = await fetch(`${API_BASE}/grades/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const grades = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Performance Report</h2>
        <button class="btn btn-primary" onclick="exportToCSV('performance-report')">Export as CSV</button>
        <div class="table-container">
            <table id="performance-report">
                <thead>
                    <tr>
                        <th>Course</th>
                        <th>Score</th>
                        <th>Grade</th>
                        <th>Date</th>
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
                            <td>${new Date(g.created_at).toLocaleDateString()}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function generateAttendanceReport() {
  const response = await fetch(`${API_BASE}/students/attendance/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const attendance = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Attendance Report</h2>
        <button class="btn btn-primary" onclick="exportToCSV('attendance-report')">Export as CSV</button>
        <div class="table-container">
            <table id="attendance-report">
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${attendance.results
                      .map(
                        (a) => `
                        <tr>
                            <td>${a.student}</td>
                            <td>${new Date(a.date).toLocaleDateString()}</td>
                            <td><span class="badge ${a.present ? "badge-success" : "badge-danger"}">${a.present ? "Present" : "Absent"}</span></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

function showSystemSettings() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>System Settings</h2>
        <form onsubmit="handleSaveSettings(event)" class="form-container">
            <div class="form-group">
                <label>School Name</label>
                <input type="text" id="school_name" value="Ginba Junior School" required>
            </div>
            <div class="form-group">
                <label>Academic Year</label>
                <input type="text" id="academic_year" value="2024-2025" required>
            </div>
            <div class="form-group">
                <label>School Email</label>
                <input type="email" id="school_email" value="admin@ginba.school" required>
            </div>
            <div class="form-group">
                <label>System Logo URL</label>
                <input type="text" id="logo_url" value="https://via.placeholder.com/150">
            </div>
            <div class="form-group">
                <label>Notification Email Enabled</label>
                <input type="checkbox" id="notifications_enabled" checked>
            </div>
            <div class="form-group">
                <label>Auto-backup Enabled</label>
                <input type="checkbox" id="backup_enabled" checked>
            </div>
            <button type="submit" class="btn btn-primary">Save Settings</button>
        </form>
    `
}

async function handleCreateUser(event) {
  event.preventDefault()
  // User creation logic
  alert("User created successfully")
  showUserManagement()
}

async function handleSaveSettings(event) {
  event.preventDefault()
  alert("Settings saved successfully")
}

function exportToCSV(tableId) {
  const table = document.getElementById(tableId)
  const csv = []
  const rows = table.querySelectorAll("tr")

  rows.forEach((row) => {
    const cols = row.querySelectorAll("td, th")
    const csvRow = []
    cols.forEach((col) => csvRow.push(col.innerText))
    csv.push(csvRow.join(","))
  })

  const csvFile = new Blob([csv.join("\n")], { type: "text/csv" })
  const downloadLink = document.createElement("a")
  downloadLink.href = URL.createObjectURL(csvFile)
  downloadLink.download = `${tableId}.csv`
  downloadLink.click()
}
