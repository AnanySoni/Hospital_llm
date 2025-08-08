// API utility for hospital-scoped requests
import { HospitalData } from '../contexts/HospitalContext';

export interface ApiOptions {
  slug: string;
  token?: string;
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

export async function apiFetch(endpoint: string, options: ApiOptions) {
  const { slug, token, method = 'GET', body, headers = {} } = options;
  let url = endpoint;
  // Only prepend if not already a multi-tenant v2 path and slug is not empty
  if (!endpoint.includes('/v2/h/') && slug && slug.trim() !== '') {
    if (!endpoint.startsWith('/h/')) {
      url = `/h/${slug}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    }
  }
  const fetchOptions: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  };
  try {
    const res = await fetch(url, fetchOptions);
    if (!res.ok) {
      let errorMsg = `API error: ${res.status}`;
      try {
        const errJson = await res.json();
        errorMsg = errJson.message || errorMsg;
      } catch {}
      throw new Error(errorMsg);
    }
    return await res.json();
  } catch (err) {
    throw err;
  }
}

// Example: get doctors for current hospital
export async function getDoctors(slug: string, token?: string) {
  return apiFetch('/admin/doctors', { slug, token });
}

// Example: get hospital info
export async function getHospitalInfo(slug: string) {
  return apiFetch('/info', { slug });
}

// Add more API functions as needed, always include slug
