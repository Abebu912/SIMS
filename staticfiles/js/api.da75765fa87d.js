import auth from "./auth.js" // Declare or import the auth variable

class API {
  constructor(baseURL = "http://localhost:8000/api") {
    this.baseURL = baseURL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    }

    if (auth.isAuthenticated()) {
      headers["Authorization"] = `Bearer ${auth.getToken()}`
    }

    const config = {
      ...options,
      headers,
    }

    try {
      const response = await fetch(url, config)

      if (response.status === 401) {
        auth.logout()
        window.location.href = "/login"
      }

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "API error")
      }

      return await response.json()
    } catch (error) {
      console.error("API Error:", error)
      throw error
    }
  }

  get(endpoint) {
    return this.request(endpoint, { method: "GET" })
  }

  post(endpoint, data) {
    return this.request(endpoint, { method: "POST", body: JSON.stringify(data) })
  }

  put(endpoint, data) {
    return this.request(endpoint, { method: "PUT", body: JSON.stringify(data) })
  }

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" })
  }
}

const api = new API()
export default api
