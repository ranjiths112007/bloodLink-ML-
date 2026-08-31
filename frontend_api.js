/* BloodLink frontend API client.
   Keeps authentication, requests and interactions in one predictable layer. */
const BloodLinkAPI = (() => {
  async function call(path, options = {}) {
    const response = await fetch(path, {
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', ...(options.headers || {})},
      ...options
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = data?.error?.message || `Request failed (${response.status})`;
      const error = new Error(message); error.status = response.status; error.code = data?.error?.code; throw error;
    }
    return data;
  }
  return {
    me: () => call('/api/auth/me'),
    register: (payload) => call('/api/auth/register', {method:'POST', body:JSON.stringify(payload)}),
    login: (payload) => call('/api/auth/login', {method:'POST', body:JSON.stringify(payload)}),
    logout: () => call('/api/auth/logout', {method:'POST'}),
    createRequest: (payload) => call('/api/requests', {method:'POST', body:JSON.stringify(payload)}),
    matchDonors: (payload) => call('/api/match-donors', {method:'POST', body:JSON.stringify(payload)}),
    logInteraction: (payload) => call('/api/interactions', {method:'POST', body:JSON.stringify(payload)}),
    requestInteractions: (requestId) => call(`/api/requests/${requestId}/interactions`),
    adminMetrics: () => call('/api/admin/metrics')
  };
})();

if (typeof window !== 'undefined') window.BloodLinkAPI = BloodLinkAPI;
