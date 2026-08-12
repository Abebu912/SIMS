const API_BASE = "https://api.example.com" // Declare API_BASE variable
const authToken = "your-auth-token" // Declare authToken variable

async function showTeacherDashboard() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Teacher Dashboard</h2>
        <div class="card-grid">
            <div class="card" onclick="showMyClasses()" style="cursor: pointer;">
                <h3>My Classes</h3>
                <p>View assigned courses</p>
            </div>
            <div class="card" onclick="showGradeEntry()" style="cursor: pointer;">
                <h3>Enter Grades</h3>
                <p>Submit student grades</p>
            </div>
            <div class="card" onclick="showClassRosters()" style="cursor: pointer;">
                <h3>Class Rosters</h3>
                <p>View enrolled students</p>
            </div>
            <div class="card" onclick="showPostAnnouncement()" style="cursor: pointer;">
                <h3>Announcements</h3>
                <p>Post class updates</p>
            </div>
        </div>
    `
}

async function showMyClasses() {
  const response = await fetch(`${API_BASE}/courses/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const courses = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>My Courses</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Course Code</th>
                        <th>Course Name</th>
                        <th>Credits</th>
                        <th>Students</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${courses.results
                      .map(
                        (c) => `
                        <tr>
                            <td>${c.code}</td>
                            <td>${c.name}</td>
                            <td>${c.credits}</td>
                            <td>${c.enrollments}</td>
                            <td>
                                <button class="btn btn-outline" style="font-size: 0.85rem; padding: 6px 12px;">Manage</button>
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

function showGradeEntry() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Enter Grades</h2>
        <form onsubmit="handleGradeSubmission(event)" class="form-container">
            <div class="form-group">
                <label>Course</label>
                <select id="course" required>
                    <option value="">Select Course</option>
                </select>
            </div>
            <div class="form-group">
                <label>Students (Add Grades)</label>
                <div id="student-grades" style="display: flex; flex-direction: column; gap: 1rem;">
                    <div style="display: flex; gap: 1rem; align-items: center;">
                        <input type="text" placeholder="Student Name" readonly style="flex: 1; background: #f3f4f6;">
                        <input type="number" placeholder="Score" min="0" max="100" step="0.5" style="width: 120px;">
                    </div>
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Submit Grades</button>
        </form>
    `
}

function showClassRosters() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Class Rosters</h2>
        <div class="form-group">
            <label>Select Course</label>
            <select onchange="loadRosterForCourse(this.value)">
                <option value="">Choose a course...</option>
            </select>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Student ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Enrollment Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td colspan="4" style="text-align: center; color: #6b7280;">Select a course to view roster</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `
}

function showPostAnnouncement() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Post Announcement</h2>
        <form onsubmit="handleAnnouncementSubmit(event)" class="form-container">
            <div class="form-group">
                <label>Course</label>
                <select id="announcement_course" required>
                    <option value="">Select Course</option>
                </select>
            </div>
            <div class="form-group">
                <label>Title</label>
                <input type="text" id="announcement_title" required>
            </div>
            <div class="form-group">
                <label>Message</label>
                <textarea id="announcement_message" rows="6" required></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Post Announcement</button>
        </form>
    `
}

async function handleGradeSubmission(event) {
  event.preventDefault()
  alert("Grades submitted successfully")
}

async function handleAnnouncementSubmit(event) {
  event.preventDefault()
  alert("Announcement posted successfully")
}

async function loadRosterForCourse(courseId) {
  const response = await fetch(`${API_BASE}/courses/${courseId}/students`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const students = await response.json()

  const studentTableBody = document.querySelector("#content-area table tbody")
  studentTableBody.innerHTML = students.results
    .map(
      (s) => `
        <tr>
            <td>${s.id}</td>
            <td>${s.name}</td>
            <td>${s.email}</td>
            <td>${s.enrollmentStatus}</td>
        </tr>
    `,
    )
    .join("")
}
