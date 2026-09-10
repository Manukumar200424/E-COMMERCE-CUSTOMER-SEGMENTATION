async function getAnalytics() {
  const response = await fetch('/api/statistics');
  if (!response.ok) throw new Error('Could not load analytics');
  return response.json();
}

function money(value) { return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value); }

async function loadDashboard() {
  try {
    const payload = await getAnalytics();
    const summary = payload.summary;
    const total = document.getElementById('total-customers');
    if (total) {
      total.textContent = summary.total_customers;
      document.getElementById('total-segments').textContent = summary.total_segments;
      document.getElementById('average-spending').textContent = money(summary.average_spending);
      document.getElementById('average-purchases').textContent = summary.average_purchases.toFixed(1);
    }
    const canvas = document.getElementById('segment-overview-chart');
    if (canvas) {
      const labels = Object.keys(payload.charts.distribution);
      new Chart(canvas, { type: 'bar', data: { labels, datasets: [{ data: Object.values(payload.charts.distribution), backgroundColor: ['#f4b942', '#58a6a6', '#6d8fe8', '#d98272'], borderRadius: 5, barThickness: 30 }] }, options: chartOptions('Customers', false) });
    }
  } catch (error) { console.error(error); }
}

function chartOptions(label, beginAtZero = true) { return { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#202725', padding: 12, displayColors: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#75807b', font: { family: 'DM Sans' } } }, y: { beginAtZero, grid: { color: '#e8ece8' }, ticks: { color: '#75807b', font: { family: 'DM Sans' } }, title: { display: true, text: label, color: '#75807b' } } } }; }

document.addEventListener('DOMContentLoaded', loadDashboard);
