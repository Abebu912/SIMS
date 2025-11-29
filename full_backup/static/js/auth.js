class Auth {
  constructor() {
    this.token = localStorage.getItem("access_token")
    this.user = JSON.parse(localStorage.getItem("user") || "null")
  }

  async login(username, password) {
    try {
      const response = await fetch("http://localhost:8000/api/users/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      })

      if (!response.ok) throw new Error("Login failed")

      const data = await response.json()
      this.token = data.access
      this.user = data.user

      localStorage.setItem("access_token", this.token)
      localStorage.setItem("user", JSON.stringify(this.user))

      return data
    } catch (error) {
      console.error("Login error:", error)
      throw error
    }
  }

  async register(userData) {
    try {
      const response = await fetch("http://localhost:8000/api/users/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData),
      })

      if (!response.ok) throw new Error("Registration failed")

      const data = await response.json()
      this.token = data.access
      this.user = data.user

      localStorage.setItem("access_token", this.token)
      localStorage.setItem("user", JSON.stringify(this.user))

      return data
    } catch (error) {
      console.error("Registration error:", error)
      throw error
    }
  }

  logout() {
    this.token = null
    this.user = null
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
  }

  isAuthenticated() {
    return !!this.token
  }

  getToken() {
    return this.token
  }

  getUser() {
    return this.user
  }
}

const auth = new Auth()
export default auth
