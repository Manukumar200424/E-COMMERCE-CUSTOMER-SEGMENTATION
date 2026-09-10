function money(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(value);
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('prediction-form');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const error = document.getElementById('form-error');
    error.textContent = '';
    const payload = Object.fromEntries(new FormData(form).entries());
    const response = await fetch('/api/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok) { error.textContent = result.error || 'Please check the form values.'; return; }
    document.getElementById('prediction-result').classList.remove('empty-result');
    document.getElementById('prediction-result').innerHTML = `<div class="result-content"><span class="result-icon">✓</span><p class="eyebrow">Predicted segment</p><h2>${result.segment}</h2><div class="result-meta"><span>Cluster ${result.cluster}</span><span>${result.spending_level} spending profile</span></div><p>${result.explanation}</p><div class="result-stat"><span>Cluster average spending</span><strong>${money(result.cluster_average.average_spending)}</strong></div></div>`;
  });
});
