// DOM Elements
const table = document.getElementById('contactsTable');
const tbody = document.getElementById('tableBody');
const searchInput = document.getElementById('searchInput');
const statsDisplay = document.getElementById('statsDisplay');
const statusMessage = document.getElementById('statusMessage');

// Modal Elements
const modal = document.getElementById('helperModal');
const modalTitle = document.getElementById('modalTitle');
const modalCode = document.getElementById('modalCode');
const closeModalBtns = document.querySelectorAll('.modal-close, .btn-secondary');
const actionBtns = document.querySelectorAll('[data-action]');

// State
let allContacts = []; 

// Because this frontend directory serves statically, it needs to find the root json files
const DATA_SOURCES = [
    '../test_addressbook/ex_contacts.json',
    '../user_address_book/contacts.json',
    '../contacts.json',
    'test_addressbook/ex_contacts.json',
    'user_address_book/contacts.json',
    'contacts.json'
];

// --- Initialization ---

async function loadData() {
    for (const url of DATA_SOURCES) {
        try {
            const response = await fetch(url);
            if (!response.ok) continue;
            
            const data = await response.json();
            if (data && typeof data === 'object') {
                allContacts = Object.entries(data).map(([name, info]) => {
                    return {
                        name: name,
                        phones: info.phones || [],
                        email: info.email || '',
                        birthday: info.birthday || '',
                        notes: info.notes || [],
                        tags: info.tags || []
                    };
                });
                
                initUI();
                return; 
            }
        } catch (e) {
            console.warn(`Failed to fetch ${url}`, e);
        }
    }
    
    showError("Could not locate contacts data. Ensure the Python CLI has generated 'contacts.json' and the HTTP server is running.");
}

function showError(msg) {
    statusMessage.innerHTML = `<div style="margin-bottom: 0.5rem;">⚠️</div><div>${msg}</div>`;
    statusMessage.classList.add('error');
    statusMessage.style.display = 'block';
    table.style.display = 'none';
    statsDisplay.textContent = '0 contacts found';
}

function initUI() {
    statusMessage.style.display = 'none';
    table.style.display = 'table';
    
    // Sort
    allContacts.sort((a, b) => a.name.localeCompare(b.name));
    
    renderTable(allContacts);
    
    // Setup Listeners
    searchInput.addEventListener('input', (e) => {
        filterTable(e.target.value.toLowerCase().trim());
    });
    
    setupModals();
}

// --- Formatters ---

function getInitials(name) {
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0].substring(0, 2);
    return (parts[0][0] + parts[parts.length - 1][0]);
}

/**
 * Robust date formatter. Converts DD-MM-YYYY or similar to 'D MMM YYYY'
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    // Attempt to handle DD-MM-YYYY which is standard for this particular CLI bot
    const parts = dateStr.split(/[-/.\s]/);
    
    let d, m, y;
    if (parts.length === 3) {
        // Assume DD-MM-YYYY format
        d = parseInt(parts[0], 10);
        m = parseInt(parts[1], 10) - 1; // 0-indexed month
        y = parseInt(parts[2], 10);
        
        // Sanity check
        if (y < 100) y += 2000; // handle 2-digit years
        
        const dateObj = new Date(y, m, d);
        if (!isNaN(dateObj.getTime())) {
            const opts = { day: 'numeric', month: 'short', year: 'numeric' };
            return dateObj.toLocaleDateString('en-GB', opts);
        }
    }
    
    // Fallback if parsing fails
    return dateStr;
}

// --- Render Logic ---

function renderTable(contacts) {
    tbody.innerHTML = ''; 
    
    if (contacts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-muted); font-style: italic;">No contacts match your search.</td></tr>`;
        statsDisplay.textContent = `0 of ${allContacts.length} contacts`;
        return;
    }

    statsDisplay.textContent = `${contacts.length} ${contacts.length === 1 ? 'contact' : 'contacts'}`;
    const fragment = document.createDocumentFragment();

    contacts.forEach(c => {
        const tr = document.createElement('tr');
        
        // Name & Avatar
        const tdName = document.createElement('td');
        tdName.innerHTML = `
            <div class="contact-name">
                <div class="avatar">${getInitials(c.name)}</div>
                <span>${c.name}</span>
            </div>
        `;
        
        // Phones
        const tdPhones = document.createElement('td');
        tdPhones.className = 'contact-phones';
        tdPhones.innerHTML = c.phones.length > 0 
            ? c.phones.join('<br>') 
            : '<span class="empty-cell">—</span>';
            
        // Email
        const tdEmail = document.createElement('td');
        tdEmail.className = 'contact-email';
        if (c.email) {
            tdEmail.innerHTML = `<a href="mailto:${c.email}">${c.email}</a>`;
        } else {
            tdEmail.innerHTML = '<span class="empty-cell">—</span>';
        }
        
        // Birthday (Formatted)
        const tdBirthday = document.createElement('td');
        tdBirthday.className = 'contact-birthday';
        tdBirthday.innerHTML = c.birthday ? formatDate(c.birthday) : '<span class="empty-cell">—</span>';
        
        // Tags
        const tdTags = document.createElement('td');
        const tagList = document.createElement('div');
        tagList.className = 'badge-list';
        if (c.tags.length > 0) {
            c.tags.forEach(tag => {
                const span = document.createElement('span');
                span.className = 'badge';
                span.textContent = tag;
                tagList.appendChild(span);
            });
        } else {
            tagList.innerHTML = '<span class="empty-cell">—</span>';
        }
        tdTags.appendChild(tagList);
        
        // Notes (Expandable)
        const tdNotes = document.createElement('td');
        tdNotes.className = 'contact-notes';
        if (c.notes.length > 0) {
            c.notes.forEach(n => {
                const noteDiv = document.createElement('div');
                noteDiv.className = 'note-item';
                
                const textSpan = document.createElement('span');
                textSpan.className = 'note-text';
                textSpan.textContent = n;
                noteDiv.appendChild(textSpan);
                
                // Add expand button if text is long
                if (n.length > 80) {
                    const btn = document.createElement('button');
                    btn.className = 'read-more-btn';
                    btn.textContent = 'Read more';
                    btn.onclick = () => {
                        textSpan.classList.toggle('expanded');
                        btn.textContent = textSpan.classList.contains('expanded') ? 'Show less' : 'Read more';
                    };
                    noteDiv.appendChild(btn);
                }
                
                tdNotes.appendChild(noteDiv);
            });
        } else {
            tdNotes.innerHTML = '<span class="empty-cell">—</span>';
        }

        // Actions
        const tdActions = document.createElement('td');
        tdActions.innerHTML = `
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn" style="padding: 0.25rem 0.5rem;" data-action="edit" data-name="${c.name}">Edit</button>
            </div>
        `;

        tr.appendChild(tdName);
        tr.appendChild(tdPhones);
        tr.appendChild(tdEmail);
        tr.appendChild(tdBirthday);
        tr.appendChild(tdTags);
        tr.appendChild(tdNotes);
        tr.appendChild(tdActions);
        
        fragment.appendChild(tr);
    });
    
    tbody.appendChild(fragment);
}

function filterTable(query) {
    if (!query) {
        renderTable(allContacts);
        return;
    }
    
    const filtered = allContacts.filter(c => {
        if (c.name.toLowerCase().includes(query)) return true;
        if (c.email && c.email.toLowerCase().includes(query)) return true;
        if (c.birthday && c.birthday.includes(query)) return true;
        if (c.phones.some(p => p.includes(query))) return true;
        if (c.tags.some(t => t.toLowerCase().includes(query))) return true;
        if (c.notes.some(n => n.toLowerCase().includes(query))) return true;
        return false;
    });
    
    renderTable(filtered);
}

// --- Modals (Helper Prompts) ---

function setupModals() {
    // Top bar buttons
    actionBtns.forEach(btn => {
         btn.addEventListener('click', (e) => {
             const action = e.currentTarget.getAttribute('data-action');
             openHelperModal(action);
         });
    });

    // Row-level delegated events
    tbody.addEventListener('click', (e) => {
        if (e.target.matches('button[data-action]')) {
            const action = e.target.getAttribute('data-action');
            const name = e.target.getAttribute('data-name');
            openHelperModal(action, name);
        }
    });

    // Close Modals
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', closeHelperModal);
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeHelperModal();
    });
}

function openHelperModal(action, targetName = '') {
    let title = '';
    let code = '';
    
    const styledName = targetName ? `"${targetName}"` : '&lt;name&gt;';

    switch (action) {
        case 'add':
            title = 'Add Contact';
            code = `bot> add &lt;name&gt; [phone] [email] [birthday]`;
            break;
        case 'delete':
            title = 'Delete Contact';
            code = `bot> delete &lt;name&gt;`;
            break;
        case 'edit':
            title = `Edit Contact ${styledName}`;
            code = `bot> change ${styledName} &lt;old_phone&gt; &lt;new_phone&gt;\nbot> add_email ${styledName} &lt;email&gt;\nbot> add_birthday ${styledName} &lt;date&gt;\nbot> add_tag ${styledName} &lt;tag&gt;`;
            break;
    }

    modalTitle.textContent = title;
    modalCode.innerHTML = code;
    modal.classList.add('active');
}

function closeHelperModal() {
    modal.classList.remove('active');
}

// Boot
document.addEventListener('DOMContentLoaded', loadData);
