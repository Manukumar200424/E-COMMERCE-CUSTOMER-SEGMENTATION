const COLORS = ['#f4b942', '#58a6a6', '#6d8fe8', '#d98272'];
const SEGMENTS = ['Premium / High-Value', 'Regular', 'Occasional', 'Low-Value'];
function money(value) { return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value); }
function options(title, currency = false) { return { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#202725', padding: 12, callbacks: currency ? { label: item => ` ${money(item.raw)}` } : {} } }, scales: { x: { grid: { display: false }, ticks: { color: '#75807b', maxRotation: 30 } }, y: { beginAtZero: true, grid: { color: '#e8ece8' }, ticks: { color: '#75807b', callback: value => currency ? money(value) : value } } } }; }
function bar(id, values, title, currency = false) { new Chart(document.getElementById(id), { type: 'bar', data: { labels: SEGMENTS, datasets: [{ label: title, data: values, backgroundColor: COLORS, borderRadius: 5, barThickness: 28 }] }, options: options(title, currency) }); }

async function loadCharts() {
  const payload = await (await fetch('/api/statistics')).json();
  const charts = payload.charts;
  bar('distribution-chart', SEGMENTS.map(key => charts.distribution[key] || 0), 'Customers');
  new Chart(document.getElementById('percentage-chart'), { type: 'doughnut', data: { labels: SEGMENTS, datasets: [{ data: SEGMENTS.map(key => charts.distribution[key] || 0), backgroundColor: COLORS, borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } } } } });
  bar('spending-chart', SEGMENTS.map(key => charts.spending[key] || 0), 'Average spending', true);
  bar('frequency-chart', SEGMENTS.map(key => charts.frequency[key] || 0), 'Average frequency');
  const scatterSets = SEGMENTS.map((segment, index) => ({ label: segment, data: charts.scatter.filter(point => point.segment === segment).map(point => ({ x: point.income, y: point.spending })), backgroundColor: COLORS[index] }));
  new Chart(document.getElementById('scatter-chart'), { type: 'scatter', data: { datasets: scatterSets }, options: { ...options('Spending', true), plugins: { legend: { display: true, position: 'bottom', labels: { usePointStyle: true } } }, scales: { x: { title: { display: true, text: 'Annual income' }, grid: { color: '#e8ece8' } }, y: { title: { display: true, text: 'Total spending' }, grid: { color: '#e8ece8' }, ticks: { callback: value => money(value) } } } } });
  const ages = charts.ages; new Chart(document.getElementById('age-chart'), { type: 'bar', data: { labels: Object.keys(ages), datasets: [{ data: Object.values(ages), backgroundColor: '#58a6a6', borderRadius: 3 }] }, options: options('Customers') });
  new Chart(document.getElementById('elbow-chart'), { type: 'line', data: { labels: charts.wcss.map(point => `K=${point.k}`), datasets: [{ data: charts.wcss.map(point => point.wcss), borderColor: '#d98272', backgroundColor: '#d98272', tension: 0.25, pointRadius: 4 }] }, options: options('WCSS') });
  const pcaSets = SEGMENTS.map((segment, index) => ({ label: segment, data: charts.pca.filter(point => point.segment === segment).map(point => ({ x: point.x, y: point.y })), backgroundColor: COLORS[index] })); new Chart(document.getElementById('pca-chart'), { type: 'scatter', data: { datasets: pcaSets }, options: { ...options('Principal Component 2'), plugins: { legend: { display: true, position: 'bottom', labels: { usePointStyle: true } } }, scales: { x: { title: { display: true, text: 'Principal Component 1' } }, y: { title: { display: true, text: 'Principal Component 2' } } } } });
  document.getElementById('stats-rows').innerHTML = payload.stats.map(row => `<tr><td><span class="segment-pill">${row.segment}</span></td><td>${row.customers}</td><td>${money(row.average_income)}</td><td>${money(row.average_spending)}</td><td>${row.average_purchases}</td><td>${money(row.average_order_value)}</td><td>${row.average_frequency}</td><td class="recommendation">${row.recommendation}</td></tr>`).join('');
}
document.addEventListener('DOMContentLoaded', loadCharts);
