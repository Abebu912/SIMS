const API_BASE = "https://api.example.com" // Declare API_BASE variable
const authToken = "your_auth_token_here" // Declare authToken variable

async function showStudentPortal() {
  const response = await fetch(`${API_BASE}/students/my_profile/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const student = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Student Portal</h2>
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #ecfdf5 100%); padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: #1e40af; margin-bottom: 0.5rem;">Welcome Back!</h3>
                    <p style="color: #6b7280;">Student ID: ${student.student_id}</p>
                    <p style="color: #6b7280;">Grade Level: ${student.grade_level}</p>
                </div>
                <div style="text-align: right; font-size: 3rem;">📚</div>
            </div>
        </div>
        <div class="card-grid">
            <div class="card" onclick="showStudentCourses()" style="cursor: pointer;">
                <h3>My Courses</h3>
                <p>View enrolled courses</p>
            </div>
            <div class="card" onclick="showStudentGrades()" style="cursor: pointer;">
                <h3>My Grades</h3>
                <p>View academic performance</p>
            </div>
            <div class="card" onclick="showStudentTranscript()" style="cursor: pointer;">
                <h3>Transcript</h3>
                <p>Download official transcript</p>
            </div>
            <div class="card" onclick="showStudentPayments()" style="cursor: pointer;">
                <h3>Payment Status</h3>
                <p>View fee information</p>
            </div>
        </div>
    `
}

async function showStudentCourses() {
  const response = await fetch(`${API_BASE}/courses/enrollments/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const enrollments = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>My Courses</h2>
        <button class="btn btn-primary" onclick="showEnrollmentForm()">Enroll in Course</button>
        <div class="table-container">
            <table>
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
                    ${enrollments.results
                      .map(
                        (e) => `
                        <tr>
                            <td>${e.course_code}</td>
                            <td>${e.course_name}</td>
                            <td>${e.teacher_name}</td>
                            <td><span class="badge badge-success">${e.status}</span></td>
                            <td><button class="btn btn-outline" style="font-size: 0.85rem;">View</button></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function showStudentGrades() {
  const response = await fetch(`${API_BASE}/grades/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const grades = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>My Grades</h2>
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
                            <td>${g.feedback || "No feedback yet"}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

async function showStudentTranscript() {
  const response = await fetch(`${API_BASE}/grades/my_transcript/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const transcript = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Official Transcript</h2>
        <div style="background: white; padding: 2rem; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2rem; border-bottom: 2px solid #2563eb; padding-bottom: 1rem;">
                <div>
                    <h3>Ginba Junior School</h3>
                    <p style="color: #6b7280;">Student Transcript</p>
                </div>
                <div style="text-align: right;">
                    <p><strong>GPA:</strong> ${transcript.gpa.toFixed(2)}</p>
                    <p><strong>Total Credits:</strong> ${transcript.total_credits}</p>
                </div>
            </div>
            <button class="btn btn-primary" onclick="downloadTransriptPDF()">Download PDF</button>
            <button class="btn btn-outline" onclick="printTranscript()">Print</button>
        </div>
    `
}

async function showStudentPayments() {
  const response = await fetch(`${API_BASE}/payments/my_payments/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const payments = await response.json()

  let totalDue = 0
  payments.forEach((p) => {
    if (p.status === "pending") totalDue += Number.parseFloat(p.amount)
  })

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Payment Status</h2>
        <div class="card-grid" style="margin-bottom: 2rem;">
            <div class="card">
                <h3>$${totalDue.toFixed(2)}</h3>
                <p>Amount Due</p>
            </div>
            <div class="card">
                <h3>${payments.filter((p) => p.status === "completed").length}</h3>
                <p>Payments Made</p>
            </div>
        </div>
        <button class="btn btn-primary" onclick="showPaymentForm()">Make Payment</button>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Due Date</th>
                        <th>Date Paid</th>
                    </tr>
                </thead>
                <tbody>
                    ${payments
                      .map(
                        (p) => `
                        <tr>
                            <td>$${p.amount}</td>
                            <td><span class="badge ${p.status === "completed" ? "badge-success" : "badge-warning"}">${p.status}</span></td>
                            <td>${new Date(p.due_date).toLocaleDateString()}</td>
                            <td>${p.status === "completed" ? new Date(p.payment_date).toLocaleDateString() : "Pending"}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `
}

function showEnrollmentForm() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Enroll in Course</h2>
        <form onsubmit="handleCourseEnrollment(event)" class="form-container">
            <div class="form-group">
                <label>Select Course</label>
                <select id="course_select" required>
                    <option value="">Choose a course...</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Enroll</button>
            <button type="button" class="btn btn-outline" onclick="showStudentCourses()">Cancel</button>
        </form>
    `
}

function showPaymentForm() {
  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Make Payment</h2>
        <form onsubmit="handlePaymentSubmit(event)" class="form-container">
            <div class="form-group">
                <label>Amount</label>
                <input type="number" id="payment_amount" min="0.01" step="0.01" required>
            </div>
            <div class="form-group">
                <label>Payment Method</label>
                <select id="payment_method" required>
                    <option value="">Select method</option>
                    <option value="card">Credit/Debit Card</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="mobile_money">Mobile Money</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reference Number</label>
                <input type="text" id="reference_number" required>
            </div>
            <button type="submit" class="btn btn-primary">Submit Payment</button>
            <button type="button" class="btn btn-outline" onclick="showStudentPayments()">Cancel</button>
        </form>
    `
}

function downloadTransriptPDF() {
  alert("Transcript PDF download started")
}

function printTranscript() {
  window.print()
}

async function handleCourseEnrollment(event) {
  event.preventDefault()
  alert("Successfully enrolled in course")
  showStudentCourses()
}

async function handlePaymentSubmit(event) {
  event.preventDefault()
  alert("Payment submitted successfully")
  showStudentPayments()
}
