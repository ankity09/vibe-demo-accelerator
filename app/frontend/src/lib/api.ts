import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.DEV ? 'http://localhost:8000/api' : '/api',
  timeout: 30000,
})
