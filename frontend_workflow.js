/* Small UI controller helpers. Import after frontend_api.js. */
function showBloodLinkError(target, error) {
  const el = typeof target === 'string' ? document.querySelector(target) : target;
  if (!el) return;
  el.textContent = error?.message || 'Something went wrong. Please try again.';
  el.setAttribute('role', 'alert');
}

async function submitBloodRequest(form) {
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.lat = Number(payload.lat); payload.lon = Number(payload.lon);
  payload.max_distance = Number(payload.max_distance || 30);
  try {
    const created = await BloodLinkAPI.createRequest(payload);
    const matches = await BloodLinkAPI.matchDonors(payload);
    return {created, matches};
  } catch (error) {
    showBloodLinkError(form.querySelector('[data-error]'), error);
    throw error;
  }
}

async function recordDonorResponse(requestId, donorId, response, probability = 0, rank = 0) {
  return BloodLinkAPI.logInteraction({
    request_id: Number(requestId), donor_id: Number(donorId),
    response, predicted_probability: Number(probability), rank_position: Number(rank)
  });
}

async function loadCurrentUser(selector = '[data-user-name]') {
  const result = await BloodLinkAPI.me();
  const el = document.querySelector(selector);
  if (el && result.user) el.textContent = result.user.display_name;
  return result.user;
}

if (typeof window !== 'undefined') {
  window.showBloodLinkError = showBloodLinkError;
  window.submitBloodRequest = submitBloodRequest;
  window.recordDonorResponse = recordDonorResponse;
  window.loadCurrentUser = loadCurrentUser;
}
