import axios from 'axios';
import type { Employee, EmployeeStats, Feedback, FeedbackMapping, Criterion, Period, Summary, AuthToken } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: `${API_URL}/api` });

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      window.location.href = '/auth';
    }
    return Promise.reject(err);
  }
);

// Auth
export const verifyMagicLink = (token: string) =>
  api.get<AuthToken>(`/auth/verify?token=${token}`).then(r => r.data);

export const requestMagicLink = (email: string) =>
  api.post('/auth/magic-link', { email }).then(r => r.data);

// Employees
export const getEmployees = () =>
  api.get<Employee[]>('/employees/').then(r => r.data);

export const getEmployeesWithStats = (period_id?: string) =>
  api.get<EmployeeStats[]>('/employees/stats', { params: { period_id } }).then(r => r.data);

export const getEmployee = (id: string) =>
  api.get<Employee>(`/employees/${id}`).then(r => r.data);

// Feedback
export const getFeedback = (params: {
  employee_id?: string;
  period_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) => api.get<Feedback[]>('/feedback/', { params }).then(r => r.data);

export const createFeedback = (data: {
  employee_id: string;
  period_id?: string;
  original_text: string;
  source?: string;
  mappings?: Partial<FeedbackMapping>[];
}) => api.post<Feedback>('/feedback/', data).then(r => r.data);

export const updateFeedback = (id: string, data: { status?: string; period_id?: string }) =>
  api.patch<Feedback>(`/feedback/${id}`, data).then(r => r.data);

export const deleteFeedback = (id: string) =>
  api.delete(`/feedback/${id}`).then(r => r.data);

export const addMapping = (feedbackId: string, data: Partial<FeedbackMapping>) =>
  api.post<FeedbackMapping>(`/feedback/${feedbackId}/mappings`, data).then(r => r.data);

export const updateMapping = (feedbackId: string, mappingId: string, data: Partial<FeedbackMapping>) =>
  api.patch<FeedbackMapping>(`/feedback/${feedbackId}/mappings/${mappingId}`, data).then(r => r.data);

export const deleteMapping = (feedbackId: string, mappingId: string) =>
  api.delete(`/feedback/${feedbackId}/mappings/${mappingId}`).then(r => r.data);

// Criteria
export const getCriteria = (activeOnly = true) =>
  api.get<Criterion[]>('/criteria/', { params: { active_only: activeOnly } }).then(r => r.data);

export const createCriterion = (data: Partial<Criterion>) =>
  api.post<Criterion>('/criteria/', data).then(r => r.data);

export const updateCriterion = (id: string, data: Partial<Criterion>) =>
  api.patch<Criterion>(`/criteria/${id}`, data).then(r => r.data);

export const deactivateCriterion = (id: string) =>
  api.delete(`/criteria/${id}`).then(r => r.data);

// Periods
export const getPeriods = () =>
  api.get<Period[]>('/periods/').then(r => r.data);

export const createPeriod = (data: Partial<Period>) =>
  api.post<Period>('/periods/', data).then(r => r.data);

// Summary
export const getSummary = (employee_id: string, period_id: string) =>
  api.get<Summary | null>('/summary/', { params: { employee_id, period_id } }).then(r => r.data);

export const generateSummary = (employee_id: string, period_id: string) =>
  api.post('/summary/generate', null, { params: { employee_id, period_id } }).then(r => r.data);

// Export
export const getExportSummaryUrl = (employee_id: string, period_id: string): string => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : '';
  return `${API_URL}/api/export/summary?employee_id=${employee_id}&period_id=${period_id}`;
};

export const downloadSummary = async (employee_id: string, period_id: string) => {
  const resp = await api.get('/export/summary', {
    params: { employee_id, period_id },
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'text/html' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = `summary_${employee_id}.html`;
  a.click();
  window.URL.revokeObjectURL(url);
};

// LLM
export const analyzeFeedback = (data: {
  original_text: string;
  employee_name: string;
  employee_position?: string;
  employee_level?: string;
}) => api.post('/llm/analyze', data).then(r => r.data);
