const API_BASE = "https://api.example.com" // Declare API_BASE variable
const authToken = "your_auth_token_here" // Declare authToken variable

async function showParentPortal() {
  const response = await fetch(`${API_BASE}/students/`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const children = await response.json()

  const content = document.getElementById("content-area")
  content.innerHTML = `
        <h2>Parent Portal</h2>
        <p style="color: #6b7280; margin-bottom: 2rem;">Monitor your child's academic progress and manage payments</p>
        <div style="display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
            ${children.results
              .map(
                (child) => `
                <button class="btn btn-primary" onclick="selectChild('${child.id}', '${child.user_name}')">
                    ${child.user_name} (Grade ${child.grade_level})
                </button>
            `,
              )
              .join("")}
        </div>
        <div id="child-details"></div>
    `

  if (children.results.length > 0) {
    selectChild(children.results[0].id, children.results[0].user_name)
  }
}

async function selectChild(childId, childName) {
  const content = document.getElementById("child-details")
  content.innerHTML = `
        <h3>${childName}'s Dashboard</h3>
        <div class="card-grid" style="margin-bottom: 2rem;">
            <div class="card" onclick="showChildGrades('${childId}')" style="cursor: pointer;">
                <h3>Academic Performance</h3>
                <p>View grades and progress</p>
            </div>
            <div class="card" onclick="showChildAttendance('${childId}')" style="cursor: pointer;">
                <h3>Attendance</h3>
                <p>Check attendance record</p>
            </div>
            <div class="card" onclick="showChildPayments('${childId}')" style="cursor: pointer;">
                <h3>Payments</h3>
                <p>Manage fees and payments</p>
            </div>
            <div class="card" onclick="showChildCourses('${childId}')" style="cursor: pointer;">
                <h3>Enrolled Courses</h3>
                <p>View course information</p>
            </div>
        </div>
    `
}

async function showChildGrades(childId) {
  const response = await fetch(`${API_BASE}/grades/?student=${childId}`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const grades = await response.json()

  let averageScore = 0
  if (grades.results.length > 0) {
    averageScore = grades.results.reduce((sum, g) => sum + Number.parseFloat(g.score), 0) / grades.results.length
  }

  const content = document.getElementById("child-details")
  content.innerHTML = `
        <h3>Academic Performance</h3>
        <div class="card-grid" style="margin-bottom: 2rem;">
            <div class="card">
                <h3>${averageScore.toFixed(1)}</h3>
                <p>Average Score</p>
            </div>
            <div class="card">
                <h3>${grades.results.length}</h3>
                <p>Completed Courses</p>
            </div>
        </div>
        <h4 style="margin-top: 2rem; margin-bottom: 1rem;">Detailed Grades</h4>
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
                            <td>${g.feedback || "No feedback"}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
        <button class="btn btn-outline" onclick="showParentPortal()" style="margin-top: 1rem;">Back</button>
    `
}

async function showChildAttendance(childId) {
  const response = await fetch(`${API_BASE}/students/attendance/?student=${childId}`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const attendance = await response.json()

  let presentDays = 0
  let totalDays = 0

  attendance.results.forEach((a) => {
    totalDays++
    if (a.present) presentDays++
  })

  const attendancePercentage = totalDays > 0 ? ((presentDays / totalDays) * 100).toFixed(1) : 0

  const content = document.getElementById("child-details")
  content.innerHTML = `
        <h3>Attendance Record</h3>
        <div class="card-grid" style="margin-bottom: 2rem;">
            <div class="card">
                <h3>${attendancePercentage}%</h3>
                <p>Attendance Rate</p>
            </div>
            <div class="card">
                <h3>${presentDays}</h3>
                <p>Days Present</p>
            </div>
            <div class="card">
                <h3>${totalDays - presentDays}</h3>
                <p>Days Absent</p>
            </div>
        </div>
        <h4 style="margin-top: 2rem; margin-bottom: 1rem;">Recent Attendance</h4>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${attendance.results
                      .slice(-10)
                      .reverse()
                      .map(
                        (a) => `
                        <tr>
                            <td>${new Date(a.date).toLocaleDateString()}</td>
                            <td><span class="badge ${a.present ? "badge-success" : "badge-danger"}">${a.present ? "Present" : "Absent"}</span></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
        <button class="btn btn-outline" onclick="showParentPortal()" style="margin-top: 1rem;">Back</button>
    `
}

async function showChildPayments(childId) {
  const response = await fetch(`${API_BASE}/payments/?student=${childId}`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const payments = await response.json()

  let totalDue = 0
  let totalPaid = 0

  payments.results.forEach((p) => {
    if (p.status === "completed") totalPaid += Number.parseFloat(p.amount)
    else if (p.status === "pending") totalDue += Number.parseFloat(p.amount)
  })

  const content = document.getElementById("child-details")
  content.innerHTML = `
        <h3>Payment Status</h3>
        <div class="card-grid" style="margin-bottom: 2rem;">
            <div class="card">
                <h3>$${totalDue.toFixed(2)}</h3>
                <p>Amount Due</p>
            </div>
            <div class="card">
                <h3>$${totalPaid.toFixed(2)}</h3>
                <p>Amount Paid</p>
            </div>
            <div class="card">
                <h3>${payments.results.length}</h3>
                <p>Total Transactions</p>
            </div>
        </div>
        <button class="btn btn-primary" onclick="showParentPaymentForm('${childId}')">Make Payment</button>
        <h4 style="margin-top: 2rem; margin-bottom: 1rem;">Payment History</h4>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Due Date</th>
                        <th>Paid Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${payments.results
                      .map(
                        (p) => `
                        <tr>
                            <td>$${p.amount}</td>
                            <td><span class="badge ${p.status === "completed" ? "badge-success" : "badge-warning"}">${p.status}</span></td>
                            <td>${new Date(p.due_date).toLocaleDateString()}</td>
                            <td>${p.status === "completed" ? new Date(p.payment_date).toLocaleDateString() : "-"}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
        <button class="btn btn-outline" onclick="showParentPortal()" style="margin-top: 1rem;">Back</button>
    `
}

async function showChildCourses(childId) {
  const response = await fetch(`${API_BASE}/courses/enrollments/?student=${childId}`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
  const enrollments = await response.json()

  const content = document.getElementById("child-details")
  content.innerHTML = `
        <h3>Enrolled Courses</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Course Code</th>
                        <th>Course Name</th>
                        <th>Instructor</th>
                        <th>Credits</th>
                        <th>Status</th>
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
                            <td>${e.credits}</td>
                            <td><span class="badge badge-success">${e.status}</span></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
        <button class="btn btn-outline" onclick="showParentPortal()" style="margin-top: 1rem;">Back</button>
    `
}

function showParentPaymentForm(childId) {
  const content = document.getElementById("child-details")
  content.innerHTML = `
        <h3>Make Payment</h3>
        <form onsubmit="handleParentPayment(event, '${childId}')" class="form-container">
            <div class="form-group">
                <label>Payment Amount</label>
                <input type="number" id="parent_payment_amount" min="0.01" step="0.01" required>
            </div>
            <div class="form-group">
                <label>Payment Method</label>
                <select id="parent_payment_method" required>
                    <option value="">Select method</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="debit_card">Debit Card</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="mobile_money">Mobile Money</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reference/Invoice Number</label>
                <input type="text" id="parent_reference" placeholder="Enter reference number" required>
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea id="parent_payment_notes" placeholder="Optional notes about payment" rows="4"></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Submit Payment</button>
            <button type="button" class="btn btn-outline" onclick="showChildPayments('${childId}')">Cancel</button>
        </form>
    `
}

async function handleParentPayment(event, childId) {
  event.preventDefault()
  alert("Payment submitted successfully. We will process it shortly.")
  showParentPortal()
}
