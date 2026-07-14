import { request } from '../../api/client.js';
export async function getCategories(options = {}) { return (await request('/api/meta/categories', options)).items; }
export async function getDistricts(options = {}) { return (await request('/api/meta/districts', options)).items; }
export function getRankings({ district, category, page = 1, size = 20, signal }) { return request('/api/rankings', { query:{ district, category, page, size }, signal }); }
