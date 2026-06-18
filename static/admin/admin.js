const API_BASE = '/admin';
let authHeader = sessionStorage.getItem('homebar_auth') || '';

if (authHeader) {
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/health`, { headers: { Authorization: authHeader } });
      if (!res.ok) throw new Error('invalid');
      document.getElementById('login-screen').classList.add('hidden');
      document.getElementById('app-screen').classList.remove('hidden');
      loadInventory();
    } catch (_) {
      authHeader = '';
      sessionStorage.removeItem('homebar_auth');
    }
  })();
}

function apiHeaders() {
  const h = { 'Content-Type': 'application/json' };
  if (authHeader) h['Authorization'] = authHeader;
  return h;
}

async function api(url, opts = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    ...opts,
    headers: { ...apiHeaders(), ...(opts.headers || {}) },
  });
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
  if (res.status === 204) return null;
  const text = await res.text();
  if (!res.ok) {
    let msg = text;
    try { msg = JSON.parse(text).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  return text ? JSON.parse(text) : null;
}

async function apiUpload(url, file, extraFields = {}) {
  const formData = new FormData();
  formData.append('file', file);
  Object.entries(extraFields).forEach(([k, v]) => formData.append(k, v));

  const h = {};
  if (authHeader) h['Authorization'] = authHeader;

  const res = await fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers: h,
    body: formData,
  });
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
  if (!res.ok) {
    const text = await res.text();
    let msg = text;
    try { msg = JSON.parse(text).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function toast(msg, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${isError ? 'error' : ''}`;
  setTimeout(() => el.classList.add('hidden'), 2500);
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  authHeader = 'Basic ' + btoa(username + ':' + password);

  try {
    await api('/health');
    sessionStorage.setItem('homebar_auth', authHeader);
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    loadInventory();
  } catch (err) {
    document.getElementById('login-error').classList.remove('hidden');
    document.getElementById('login-error').textContent = 'Invalid credentials';
    authHeader = '';
  }
});

document.getElementById('logout-btn').addEventListener('click', logout);

function logout() {
  authHeader = '';
  sessionStorage.removeItem('homebar_auth');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('app-screen').classList.add('hidden');
  document.getElementById('login-password').value = '';
}

document.querySelectorAll('.sidebar li[data-tab]').forEach(li => {
  li.addEventListener('click', () => switchTab(li.dataset.tab));
});

function switchTab(tab) {
  document.querySelectorAll('.sidebar li[data-tab]').forEach(li => li.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelector(`.sidebar li[data-tab="${tab}"]`).classList.add('active');
  document.getElementById(`tab-${tab}`).classList.add('active');

  if (tab === 'inventory') loadInventory();
  else if (tab === 'ingredient-types') loadIngredientTypes();
  else if (tab === 'cocktails') loadCocktails();
}

function openModal(html) {
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

document.getElementById('modal-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeModal();
});

function openSubModal(html) {
  document.getElementById('sub-modal-content').innerHTML = html;
  document.getElementById('sub-modal-overlay').classList.remove('hidden');
}

function closeSubModal() {
  document.getElementById('sub-modal-overlay').classList.add('hidden');
}

document.getElementById('sub-modal-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeSubModal();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (!document.getElementById('sub-modal-overlay').classList.contains('hidden')) {
      closeSubModal();
    } else {
      closeModal();
    }
  }
});

// ====================================================================
// INVENTORY
// ====================================================================

async function loadInventory() {
  const filter = document.getElementById('inventory-filter').value;
  const params = filter ? `?category=${filter}` : '';
  try {
    const items = await api(`/inventory${params}`);
    renderInventory(items);
  } catch (err) {
    document.getElementById('inventory-list').innerHTML = `<p class="error-msg">${esc(err.message)}</p>`;
  }
}

function renderInventory(items) {
  if (!items.length) {
    document.getElementById('inventory-list').innerHTML = '<p style="color:#555;padding:1rem;">No items found.</p>';
    return;
  }

  document.getElementById('inventory-list').innerHTML = items.map(item => {
    let badge = '';
    if (item.is_expired) badge = '<span class="status-badge expired">Expired</span>';
    else if (item.is_in_stock) badge = '<span class="status-badge in-stock">In Stock</span>';
    else badge = '<span class="status-badge out-of-stock">Out</span>';

    const meta = [
      item.category,
      item.size_ml ? `${item.size_ml}ml` : '',
      item.ingredient_type ? item.ingredient_type.name : '',
      item.expiry_date ? `Exp: ${item.expiry_date}` : '',
    ].filter(Boolean).join(' · ');

    return `
      <div class="item-card">
        <div class="item-info">
          <div class="item-name">${esc(item.name)} ${badge}</div>
          <div class="item-meta">${meta}</div>
        </div>
        <div class="item-actions">
          <div class="qty-controls">
            <button onclick="adjustQty(${item.id}, -1)">\u2212</button>
            <span class="qty-value">${item.quantity}</span>
            <button onclick="adjustQty(${item.id}, 1)">+</button>
          </div>
          <button class="btn secondary small" onclick="editInventoryItem(${item.id})">Edit</button>
          <button class="btn danger small" onclick="removeInventoryItem(${item.id})">\u00d7</button>
        </div>
      </div>
    `;
  }).join('');
}

async function adjustQty(id, delta) {
  try {
    const item = await api(`/inventory/${id}`);
    await api(`/inventory/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity: Math.max(0, item.quantity + delta) }),
    });
    loadInventory();
  } catch (err) { toast(err.message, true); }
}

async function removeInventoryItem(id) {
  if (!confirm('Set quantity to 0? Item will not be deleted.')) return;
  try {
    await api(`/inventory/${id}`, { method: 'DELETE' });
    toast('Item quantity set to 0');
    loadInventory();
  } catch (err) { toast(err.message, true); }
}

async function showInventoryForm(editId = null) {
  let item = null;
  let ingredientTypes = [];

  try {
    ingredientTypes = await api('/ingredient-types');
    if (editId) item = await api(`/inventory/${editId}`);
  } catch (err) { toast(err.message, true); return; }

  const title = editId ? 'Edit Inventory Item' : 'Add Inventory Item';
  openModal(`
    <h4>${title}</h4>
    <form onsubmit="saveInventoryItem(event, ${editId || 'null'})">
      <div class="form-group">
        <label>Name</label>
        <input type="text" name="name" value="${esc(item?.name || '')}" required>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Category</label>
          <select name="category" required>
            ${['spirit','mixer','syrup','fruit','accessory','glass'].map(c =>
              `<option value="${c}" ${item?.category === c ? 'selected' : ''}>${c}</option>`
            ).join('')}
          </select>
        </div>
        <div class="form-group">
          <label>Size (ml)</label>
          <input type="number" name="size_ml" value="${item?.size_ml || ''}" placeholder="e.g. 750">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Quantity</label>
          <input type="number" name="quantity" value="${item?.quantity ?? 0}" min="0" required>
        </div>
        <div class="form-group">
          <label>Expiry Date</label>
          <input type="date" name="expiry_date" value="${item?.expiry_date || ''}">
        </div>
      </div>
      <div class="form-group">
        <label>Ingredient Type</label>
        <select name="ingredient_type_id">
          <option value="">-- None --</option>
          ${ingredientTypes.map(t =>
            `<option value="${t.id}" ${item?.ingredient_type_id === t.id ? 'selected' : ''}>${esc(t.name)}</option>`
          ).join('')}
        </select>
      </div>
      ${editId ? `
        <div class="form-group">
          <label>Photo</label>
          <input type="file" name="photo" accept="image/*">
        </div>
      ` : ''}
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn primary">Save</button>
      </div>
    </form>
  `);
}

async function saveInventoryItem(e, editId) {
  e.preventDefault();
  const form = e.target;
  const body = {
    name: form.name.value,
    category: form.category.value,
    size_ml: form.size_ml.value ? parseInt(form.size_ml.value) : null,
    quantity: parseInt(form.quantity.value) || 0,
    expiry_date: form.expiry_date.value || null,
    ingredient_type_id: form.ingredient_type_id.value ? parseInt(form.ingredient_type_id.value) : null,
  };

  try {
    if (editId) {
      await api(`/inventory/${editId}`, { method: 'PUT', body: JSON.stringify(body) });
      if (form.photo?.files?.[0]) {
        await apiUpload(`/inventory/${editId}/photo`, form.photo.files[0]);
      }
    } else {
      await api('/inventory', { method: 'POST', body: JSON.stringify(body) });
    }
    closeModal();
    loadInventory();
  } catch (err) { toast(err.message, true); }
}

async function editInventoryItem(id) {
  await showInventoryForm(id);
}

// ====================================================================
// INGREDIENT TYPES
// ====================================================================

async function loadIngredientTypes() {
  try {
    const types = await api('/ingredient-types');
    renderIngredientTypes(types);
  } catch (err) {
    document.getElementById('ingredient-types-list').innerHTML = `<p class="error-msg">${esc(err.message)}</p>`;
  }
}

function renderIngredientTypes(types) {
  if (!types.length) {
    document.getElementById('ingredient-types-list').innerHTML = '<p style="color:#555;padding:1rem;">No ingredient types defined yet.</p>';
    return;
  }

  document.getElementById('ingredient-types-list').innerHTML = types.map(t => `
    <div class="item-card">
      <div class="item-info">
        <div class="item-name">${esc(t.name)}</div>
      </div>
      <div class="item-actions">
        <button class="btn secondary small" onclick="editIngredientType(${t.id}, '${esc(t.name)}')">Edit</button>
        <button class="btn danger small" onclick="deleteIngredientType(${t.id})">\u00d7</button>
      </div>
    </div>
  `).join('');
}

function showIngredientTypeForm(editId = null, currentName = '') {
  const title = editId ? 'Edit Ingredient Type' : 'Add Ingredient Type';
  openModal(`
    <h4>${title}</h4>
    <form onsubmit="saveIngredientType(event, ${editId || 'null'})">
      <div class="form-group">
        <label>Name</label>
        <input type="text" name="name" value="${esc(currentName)}" required>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn primary">Save</button>
      </div>
    </form>
  `);
}

async function saveIngredientType(e, editId) {
  e.preventDefault();
  const name = e.target.name.value;
  try {
    if (editId) {
      await api(`/ingredient-types/${editId}`, { method: 'PUT', body: JSON.stringify({ name }) });
    } else {
      await api('/ingredient-types', { method: 'POST', body: JSON.stringify({ name }) });
    }
    closeModal();
    loadIngredientTypes();
  } catch (err) { toast(err.message, true); }
}

function editIngredientType(id, name) {
  showIngredientTypeForm(id, name);
}

async function deleteIngredientType(id) {
  if (!confirm('Delete this ingredient type? This may affect inventory items and cocktails.')) return;
  try {
    await api(`/ingredient-types/${id}`, { method: 'DELETE' });
    toast('Ingredient type deleted');
    loadIngredientTypes();
  } catch (err) { toast(err.message, true); }
}

// ====================================================================
// COCKTAILS
// ====================================================================

async function loadCocktails() {
  try {
    const cocktails = await api('/cocktails');
    renderCocktails(cocktails);
  } catch (err) {
    document.getElementById('cocktails-list').innerHTML = `<p class="error-msg">${esc(err.message)}</p>`;
  }
}

function renderCocktails(cocktails) {
  if (!cocktails.length) {
    document.getElementById('cocktails-list').innerHTML = '<p style="color:#555;padding:1rem;">No cocktails yet.</p>';
    return;
  }

  document.getElementById('cocktails-list').innerHTML = cocktails.map(c => `
    <div class="item-card">
      <div class="item-info">
        <div class="item-name">${esc(c.name)}</div>
        <div class="item-meta">
          ${c.base_spirit ? esc(c.base_spirit) + ' · ' : ''}
          ${c.ingredients ? c.ingredients.length + ' ingredients' : ''}
          ${c.tags && c.tags.length ? ' · ' + c.tags.map(esc).join(', ') : ''}
        </div>
      </div>
      <div class="item-actions">
        <button class="btn secondary small" onclick="editCocktail(${c.id})">Edit</button>
        <button class="btn danger small" onclick="deleteCocktail(${c.id})">\u00d7</button>
      </div>
    </div>
  `).join('');
}

async function showCocktailForm(editId = null) {
  let cocktail = null;
  let ingredientTypes = [];
  let glassItems = [];
  let accessoryItems = [];

  try {
    ingredientTypes = await api('/ingredient-types');
    const inventory = await api('/inventory');
    glassItems = inventory.filter(item => item.category === 'glass');
    accessoryItems = inventory.filter(item => item.category === 'accessory');
    if (editId) cocktail = await api(`/cocktails/${editId}`);
  } catch (err) { toast(err.message, true); return; }

  const title = editId ? 'Edit Cocktail' : 'Add Cocktail';
  const tags = cocktail?.tags?.join(', ') || '';

  let ingredientLines = '';
  if (cocktail?.ingredients && cocktail.ingredients.length) {
    ingredientLines = cocktail.ingredients.map((ing, i) =>
      buildIngredientLine(i, ing, ingredientTypes)
    ).join('');
  } else {
    ingredientLines = buildIngredientLine(0, null, ingredientTypes);
  }

  const glassCheckboxes = glassItems
    .map(item => `
      <label>
        <input type="checkbox" name="glass" value="${item.id}" ${cocktail?.glasses?.some(g => g.inventory_item_id === item.id) ? 'checked' : ''}>
        ${esc(item.name)}
      </label>
    `).join('');

  const accessoryCheckboxes = accessoryItems
    .map(item => `
      <label>
        <input type="checkbox" name="accessory" value="${item.id}" ${cocktail?.accessories?.some(a => a.inventory_item_id === item.id) ? 'checked' : ''}>
        ${esc(item.name)}
      </label>
    `).join('');

  openModal(`
    <h4>${title}</h4>
    <form onsubmit="saveCocktail(event, ${editId || 'null'})">
      <div class="form-group">
        <label>Name</label>
        <input type="text" name="name" value="${esc(cocktail?.name || '')}" required>
      </div>
      <div class="form-group">
        <label>Base Spirit</label>
        <input type="text" name="base_spirit" value="${esc(cocktail?.base_spirit || '')}" placeholder="e.g. Gin">
      </div>
      <div class="form-group">
        <label>Method / Preparation Steps</label>
        <textarea name="method">${esc(cocktail?.method || '')}</textarea>
        <button type="button" class="btn secondary small" style="margin-top:0.4rem" onclick="aiGenerateMethod()">&#x2728; Generate Steps</button>
      </div>
      <div class="form-group">
        <label>Garnish</label>
        <input type="text" name="garnish" value="${esc(cocktail?.garnish || '')}">
      </div>
      <div class="form-group">
        <label>Tags (comma separated)</label>
        <input type="text" name="tags" id="tags-input" value="${tags}">
        <button type="button" class="btn secondary small" style="margin-top:0.4rem" onclick="aiGenerateTags()">&#x2728; Generate Tags</button>
      </div>

      <div class="form-group">
        <label>Ingredients</label>
        <div id="ingredient-lines" class="ingredient-lines">${ingredientLines}</div>
        <button type="button" class="btn secondary small" onclick="addIngredientLine(${JSON.stringify(ingredientTypes.map(t => t.id))})">+ Add Ingredient</button>
      </div>

      <div class="form-group">
        <label>Glasses</label>
        <div class="multi-select" id="glass-checkboxes">
          ${glassCheckboxes || '<p style="color:#555;font-size:0.8rem;">No glass items in inventory. Add glassware first.</p>'}
        </div>
      </div>

      <div class="form-group">
        <label>Accessories</label>
        <div class="multi-select" id="accessory-checkboxes">
          ${accessoryCheckboxes || '<p style="color:#555;font-size:0.8rem;">No accessory items in inventory. Add them first.</p>'}
        </div>
      </div>

      ${editId ? `
        <div class="form-group">
          <label>Add Photo</label>
          <input type="file" name="photo" accept="image/*">
          <label style="margin-top:0.5rem">
            <input type="checkbox" name="is_primary"> Set as primary photo
          </label>
        </div>
      ` : ''}

      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn primary">Save</button>
      </div>
    </form>
  `);

  window.__ingredientTypesCache = ingredientTypes;
}

function buildIngredientLine(index, existingIng, ingredientTypes) {
  const subIds = new Set(existingIng?.substitute_type_ids || []);
  const selectedTypeId = existingIng?.ingredient_type_id;
  const subCount = subIds.size;

  return `
    <div class="ingredient-line" data-index="${index}">
      <select name="ing_type_${index}" class="ing-type-select" onchange="rebuildSubPills(this)">
        <option value="">-- Select --</option>
        ${ingredientTypes.map(t =>
          `<option value="${t.id}" ${t.id === selectedTypeId ? 'selected' : ''}>${esc(t.name)}</option>`
        ).join('')}
      </select>
      <input type="number" name="ing_amt_${index}" value="${existingIng?.amount || ''}" placeholder="Amt" step="any" style="max-width:70px">
      <input type="text" name="ing_unit_${index}" value="${existingIng?.unit || 'ml'}" placeholder="Unit" style="max-width:70px">
      <button type="button" class="btn danger small" onclick="this.closest('.ingredient-line').remove()">\u00d7</button>
      ${selectedTypeId ? `
        <button type="button" class="sub-toggle" onclick="openSubsModal(this)" data-index="${index}">
          ${subCount ? `${subCount} sub${subCount > 1 ? 's' : ''}` : '+ subs'}
        </button>
        <div class="sub-pills hidden" id="sub-pills-${index}">
          ${ingredientTypes.filter(t => t.id !== selectedTypeId).map(t =>
            `<input type="checkbox" name="ing_sub_${index}" value="${t.id}" data-sub-id="${t.id}" ${subIds.has(t.id) ? 'checked' : ''} hidden>`
          ).join('')}
        </div>
      ` : '<div class="sub-pills hidden" id="sub-pills-' + index + '"></div>'}
    </div>
  `;
}

function openSubsModal(btn) {
  const index = btn.dataset.index;
  const line = btn.closest('.ingredient-line');
  const typeSelect = line.querySelector('.ing-type-select');
  const selectedTypeId = typeSelect?.value ? parseInt(typeSelect.value) : null;
  const ingredientTypes = window.__ingredientTypesCache || [];
  const pillsDiv = document.getElementById('sub-pills-' + index);

  const checkedState = {};
  if (pillsDiv) {
    pillsDiv.querySelectorAll('input').forEach(cb => { checkedState[cb.value] = cb.checked; });
  }

  const typeName = ingredientTypes.find(t => t.id === selectedTypeId)?.name || 'this ingredient';

  const checkboxes = ingredientTypes
    .filter(t => t.id !== selectedTypeId)
    .map(t => `
      <label class="sub-pill">
        <input type="checkbox" value="${t.id}" ${checkedState[t.id] ? 'checked' : ''}>
        ${esc(t.name)}
      </label>
    `).join('');

  openSubModal(`
    <h4>Substitutes for ${esc(typeName)}</h4>
    <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem;">Mark which ingredient types can replace ${esc(typeName)} in this recipe:</p>
    <div class="multi-select">${checkboxes}</div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeSubModal()">Cancel</button>
      <button type="button" class="btn primary" onclick="saveSubsModal(${index})">Save</button>
    </div>
  `);
}

function saveSubsModal(index) {
  const subModal = document.getElementById('sub-modal-content');
  const pillsDiv = document.getElementById('sub-pills-' + index);
  const toggleBtn = document.querySelector(`.sub-toggle[data-index="${index}"]`);

  if (!pillsDiv || !subModal) { closeSubModal(); return; }

  const checks = subModal.querySelectorAll('.multi-select input[type="checkbox"]');
  const newIds = [...checks].filter(cb => cb.checked).map(cb => parseInt(cb.value));

  pillsDiv.innerHTML = newIds.map(id =>
    `<input type="checkbox" name="ing_sub_${index}" value="${id}" data-sub-id="${id}" checked hidden>`
  ).join('');

  if (toggleBtn) {
    toggleBtn.textContent = newIds.length ? `${newIds.length} sub${newIds.length > 1 ? 's' : ''}` : '+ subs';
  }

  closeSubModal();
}

async function addIngredientLine(typeIds) {
  const container = document.getElementById('ingredient-lines');
  const ingredientTypes = window.__ingredientTypesCache || [];
  if (!ingredientTypes.length) {
    try { window.__ingredientTypesCache = await api('/ingredient-types'); } catch (_) {}
  }

  const index = container.children.length;
  const div = document.createElement('div');
  div.className = 'ingredient-line';
  div.dataset.index = index;
  div.innerHTML = `
    <select name="ing_type_${index}" class="ing-type-select" onchange="rebuildSubPills(this)">
      <option value="">-- Select --</option>
      ${window.__ingredientTypesCache.map(t => `<option value="${t.id}">${esc(t.name)}</option>`).join('')}
    </select>
    <input type="number" name="ing_amt_${index}" placeholder="Amt" step="any" style="max-width:70px">
    <input type="text" name="ing_unit_${index}" value="ml" placeholder="Unit" style="max-width:70px">
    <button type="button" class="btn danger small" onclick="this.closest('.ingredient-line').remove()">\u00d7</button>
    <button type="button" class="sub-toggle hidden" onclick="openSubsModal(this)" data-index="${index}">+ subs</button>
    <div class="sub-pills hidden" id="sub-pills-${index}"></div>
  `;
  container.appendChild(div);
}

function rebuildSubPills(selectEl) {
  const line = selectEl.closest('.ingredient-line');
  const index = line.dataset.index;
  const pillsDiv = document.getElementById('sub-pills-' + index);
  const toggleBtn = line.querySelector('.sub-toggle');
  if (!pillsDiv || !toggleBtn) return;

  const selectedTypeId = selectEl.value ? parseInt(selectEl.value) : null;

  if (!selectedTypeId) {
    pillsDiv.innerHTML = '';
    toggleBtn.classList.add('hidden');
    return;
  }

  toggleBtn.classList.remove('hidden');

  const savedChecks = {};
  pillsDiv.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    savedChecks[cb.value] = cb.checked;
  });

  const ingredientTypes = window.__ingredientTypesCache || [];
  pillsDiv.innerHTML = ingredientTypes
    .filter(t => t.id !== selectedTypeId)
    .map(t => {
      return `<input type="checkbox" name="ing_sub_${index}" value="${t.id}" data-sub-id="${t.id}" ${savedChecks[t.id] ? 'checked' : ''} hidden>`;
    }).join('');

  updateSubToggle(pillsDiv, toggleBtn);
}

function updateSubToggle(pillsDiv, toggleBtn) {
  const checked = pillsDiv.querySelectorAll('input:checked').length;
  toggleBtn.textContent = checked ? `${checked} sub${checked > 1 ? 's' : ''}` : '+ subs';
}

async function saveCocktail(e, editId) {
  e.preventDefault();
  const form = e.target;

  const ingredientLines = form.querySelectorAll('#ingredient-lines .ingredient-line');
  const ingredients = [];

  ingredientLines.forEach((line) => {
    const typeSelect = line.querySelector('.ing-type-select');
    const amtInput = line.querySelector('[name^="ing_amt_"]');
    const unitInput = line.querySelector('[name^="ing_unit_"]');
    if (!typeSelect || !typeSelect.value) return;

    const index = line.dataset.index;
    const subChecks = line.querySelectorAll('[name^="ing_sub_"]:checked');
    const substituteTypeIds = [...subChecks].map(cb => parseInt(cb.value));

    ingredients.push({
      ingredient_type_id: parseInt(typeSelect.value),
      amount: amtInput && amtInput.value ? parseFloat(amtInput.value) : null,
      unit: unitInput ? unitInput.value : 'ml',
      substitute_type_ids: substituteTypeIds,
    });
  });

  const glasses = [...form.querySelectorAll('input[name="glass"]:checked')]
    .map(cb => ({ inventory_item_id: parseInt(cb.value) }));

  const accessories = [...form.querySelectorAll('input[name="accessory"]:checked')]
    .map(cb => ({ inventory_item_id: parseInt(cb.value) }));

  const body = {
    name: form.name.value,
    method: form.method.value || null,
    garnish: form.garnish.value || null,
    base_spirit: form.base_spirit.value || null,
    tags: form.tags.value ? form.tags.value.split(',').map(s => s.trim()).filter(Boolean) : [],
    ingredients,
    glasses,
    accessories,
  };

  try {
    let resultId = editId;

    if (editId) {
      await api(`/cocktails/${editId}`, { method: 'PUT', body: JSON.stringify(body) });
    } else {
      const result = await api('/cocktails', { method: 'POST', body: JSON.stringify(body) });
      resultId = result.id;
    }

    if (form.photo?.files?.[0]) {
      const isPrimary = form.is_primary?.checked || false;
      await apiUpload(`/cocktails/${resultId}/photo`, form.photo.files[0], { is_primary: String(isPrimary) });
    }

    closeModal();
    loadCocktails();
  } catch (err) { toast(err.message, true); }
}

async function editCocktail(id) {
  await showCocktailForm(id);
}

async function deleteCocktail(id) {
  if (!confirm('Permanently delete this cocktail?')) return;
  try {
    await api(`/cocktails/${id}`, { method: 'DELETE' });
    toast('Cocktail deleted');
    loadCocktails();
  } catch (err) { toast(err.message, true); }
}

async function collectCocktailFormData() {
  const form = document.querySelector('#modal-content form');
  if (!form) return null;

  const ingredientTypes = window.__ingredientTypesCache || [];

  const ingredients = [];
  form.querySelectorAll('.ingredient-line').forEach(line => {
    const typeSelect = line.querySelector('.ing-type-select');
    const amtInput = line.querySelector('[name^="ing_amt_"]');
    const unitInput = line.querySelector('[name^="ing_unit_"]');
    if (!typeSelect?.value) return;

    const typeId = parseInt(typeSelect.value);
    const it = ingredientTypes.find(t => t.id === typeId);

    ingredients.push({
      ingredient_type_name: it?.name || 'unknown',
      amount: amtInput?.value ? parseFloat(amtInput.value) : null,
      unit: unitInput?.value || 'ml',
    });
  });

  const glasses = [];
  form.querySelectorAll('input[name="glass"]:checked').forEach(cb => {
    const label = cb.closest('label');
    glasses.push({ inventory_item_name: label?.textContent?.trim() || 'unknown' });
  });

  return {
    name: form.querySelector('[name="name"]')?.value || '',
    base_spirit: form.querySelector('[name="base_spirit"]')?.value || '',
    garnish: form.querySelector('[name="garnish"]')?.value || '',
    ingredients,
    glasses,
  };
}

async function aiGenerateMethod() {
  const data = await collectCocktailFormData();
  if (!data || !data.name) { toast('Fill in the cocktail name first', true); return; }
  if (!data.ingredients.length) { toast('Add at least one ingredient first', true); return; }

  const btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Generating...';

  try {
    const result = await api('/ai/generate-method', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    const textarea = document.querySelector('#modal-content textarea[name="method"]');
    if (textarea) textarea.value = result.method;
    toast('Method generated');
  } catch (err) { toast(err.message, true); }
  finally { btn.disabled = false; btn.innerHTML = '&#x2728; Generate Steps'; }
}

async function aiGenerateTags() {
  const data = await collectCocktailFormData();
  if (!data || !data.name) { toast('Fill in the cocktail name first', true); return; }
  if (!data.ingredients.length) { toast('Add at least one ingredient first', true); return; }

  const btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Generating...';

  try {
    const result = await api('/ai/generate-tags', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    const input = document.getElementById('tags-input');
    if (input && result.tags) input.value = result.tags.join(', ');
    toast('Tags generated');
  } catch (err) { toast(err.message, true); }
  finally { btn.disabled = false; btn.innerHTML = '&#x2728; Generate Tags'; }
}
