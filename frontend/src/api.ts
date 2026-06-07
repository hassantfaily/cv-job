import axios from "axios";

const api = axios.create({ baseURL: "/api" });
const browserApi = axios.create({ baseURL: "/browser" });

export const cvApi = {
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/cv/upload", fd);
  },
  getProfile: (id: string) => api.get(`/cv/profile/${id}`),
  listProfiles: () => api.get("/cv/profiles"),
};

export const jobsApi = {
  search: (query: string, location: string, sources: string[]) =>
    api.post("/jobs/search", { query, location, sources }),
  searchStatus: (runId: string) => api.get(`/jobs/search/${runId}`),
  list: (params?: { q?: string; source?: string; skip?: number; limit?: number }) =>
    api.get("/jobs", { params }),
  get: (id: string) => api.get(`/jobs/${id}`),
};

export const applicationsApi = {
  create: (jobId: string, profileId: string, method: string, hrEmail?: string) =>
    api.post("/applications", { job_id: jobId, profile_id: profileId, method, hr_email: hrEmail }),
  bulkApply: (jobIds: string[], profileId: string, method: string) =>
    api.post("/applications/bulk", null, {
      params: { profile_id: profileId, method },
      data: jobIds,
    }),
  list: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get("/applications", { params }),
  get: (id: string) => api.get(`/applications/${id}`),
  stats: () => api.get("/applications/stats/summary"),
  downloadCv: (id: string) => `/api/applications/${id}/cv`,
  downloadCl: (id: string) => `/api/applications/${id}/cover-letter`,
};

export const settingsApi = {
  get: () => api.get("/settings"),
  testEmail: () => api.post("/settings/test-email"),
};

export const linkedinApi = {
  search: (query: string, location: string) =>
    browserApi.post("/linkedin/search", { query, location }),
};

export default api;
