async function loadCustomers(search = '') {
  const response = await fetch(`/api/customers?search=${encodeURIComponent(search)}`);
  const customers = await response.json();
  const rows = document.getElementById('customer-rows');
  rows.innerHTML = customers.map(customer => `<tr><td><strong>#${customer.CustomerID}</strong></td><td><span class="segment-pill ${customer.Segment.toLowerCase().replaceAll(' ', '-').replaceAll('/', '')}">${customer.Segment}</span></td><td>${customer.Age}</td><td>${money(customer.AnnualIncome)}</td><td>${customer.TotalPurchases}</td><td>${money(customer.TotalSpent)}</td><td>${customer.PurchaseFrequency.toFixed(1)}</td></tr>`).join('') || '<tr><td colspan="7" class="empty-cell">No customers match that ID.</td></tr>';
  document.getElementById('table-status').textContent = `${customers.length} records`; 
}

document.addEventListener('DOMContentLoaded', () => { loadCustomers(); document.getElementById('customer-search').addEventListener('input', event => loadCustomers(event.target.value)); });
