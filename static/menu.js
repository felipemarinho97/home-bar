const API_BASE = '/api';

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    if (res.status === 401) throw new Error('Unauthorized');
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}

async function loadCocktails() {
  const grid = document.getElementById('cocktail-grid');
  const summary = document.getElementById('availability-summary');
  const btn = document.getElementById('refresh-btn');

  btn.classList.add('spinning');
  setTimeout(() => btn.classList.remove('spinning'), 600);

  try {
    const cocktails = await fetchJSON(`${API_BASE}/cocktails/available`);
    summary.textContent = `${cocktails.length} cocktail${cocktails.length !== 1 ? 's' : ''} available`;

    if (cocktails.length === 0) {
      grid.innerHTML = '<div class="empty-state">No cocktails available right now.<br>Check back after restocking!</div>';
      return;
    }

    grid.innerHTML = cocktails.map(c => `
      <div class="cocktail-card" data-id="${c.id}">
        ${c.primary_photo_url
          ? `<img class="card-img" src="${c.primary_photo_url}" alt="${c.name}" loading="lazy">`
          : `<div class="card-img-placeholder">&#x1f378;</div>`
        }
        <div class="card-body">
          <h3>${esc(c.name)}</h3>
          ${c.base_spirit ? `<div class="base-spirit">${esc(c.base_spirit)}</div>` : ''}
          ${c.tags && c.tags.length ? `
            <div class="card-tags">
              ${c.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    `).join('');

    document.querySelectorAll('.cocktail-card').forEach(card => {
      card.addEventListener('click', () => showDetail(card.dataset.id));
    });
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Failed to load cocktails.<br><small>${esc(err.message)}</small></div>`;
    summary.textContent = '';
  }
}

async function showDetail(id) {
  const overlay = document.getElementById('detail-overlay');
  const content = document.getElementById('detail-content');

  overlay.classList.remove('hidden');
  content.innerHTML = '<div class="loading">Loading...</div>';

  try {
    const c = await fetchJSON(`${API_BASE}/cocktails/${id}`);

    const photosHTML = c.photos && c.photos.length
      ? c.photos.map(p => `<img src="${p.url}" alt="${esc(c.name)}" loading="lazy">`).join('')
      : '';

    const ingredientsHTML = c.ingredients && c.ingredients.length
      ? c.ingredients.map(i => `
          <li>
            <span>${esc(i.ingredient_type_name || `Type #${i.ingredient_type_id}`)}</span>
            <span class="amount">${i.amount ? i.amount : ''} ${i.unit}</span>
          </li>
        `).join('')
      : '<li>No ingredients listed</li>';

    const glassesHTML = c.glasses && c.glasses.length
      ? c.glasses.map(g => esc(g.inventory_item_name || `Glass #${g.inventory_item_id}`)).join(', ')
      : '';

    const accessoriesHTML = c.accessories && c.accessories.length
      ? c.accessories.map(a => esc(a.inventory_item_name || `Accessory #${a.inventory_item_id}`)).join(', ')
      : '';

    content.innerHTML = `
      <div class="detail-header">
        <h2>${esc(c.name)}</h2>
        ${c.base_spirit ? `<div class="base-spirit">${esc(c.base_spirit)}</div>` : ''}
      </div>

      ${photosHTML ? `<div class="photo-gallery">${photosHTML}</div>` : ''}

      ${c.ingredients && c.ingredients.length ? `
        <div class="detail-section">
          <h4>Ingredients</h4>
          <ul class="ingredient-list">${ingredientsHTML}</ul>
        </div>
      ` : ''}

      ${c.method ? `
        <div class="detail-section">
          <h4>Method</h4>
          <p class="method-text">${esc(c.method)}</p>
        </div>
      ` : ''}

      ${c.garnish ? `
        <div class="detail-section">
          <h4>Garnish</h4>
          <p class="garnish-text">${esc(c.garnish)}</p>
        </div>
      ` : ''}

      ${glassesHTML ? `
        <div class="detail-section">
          <h4>Glass</h4>
          <p class="garnish-text">${glassesHTML}</p>
        </div>
      ` : ''}

      ${accessoriesHTML ? `
        <div class="detail-section">
          <h4>Accessories</h4>
          <p class="garnish-text">${accessoriesHTML}</p>
        </div>
      ` : ''}

      ${c.tags && c.tags.length ? `
        <div class="detail-section">
          <h4>Tags</h4>
          <div class="tag-list">
            ${c.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}
          </div>
        </div>
      ` : ''}
    `;
  } catch (err) {
    content.innerHTML = `<div class="empty-state">Failed to load details.</div>`;
  }
}

function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

document.getElementById('refresh-btn').addEventListener('click', loadCocktails);
document.getElementById('close-detail').addEventListener('click', () => {
  document.getElementById('detail-overlay').classList.add('hidden');
});
document.getElementById('detail-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    document.getElementById('detail-overlay').classList.add('hidden');
  }
});

loadCocktails();
