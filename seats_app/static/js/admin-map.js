
// ------------------ Workspace ------------------
function submitWorkspace(action, pk=null) {
    const nameInput = document.getElementById('workspace-name');
    const locationInput = document.getElementById('workspace-location');

    const payload = new FormData();
    payload.append('action', action);
    if (nameInput) payload.append('name', nameInput.value.trim());
    if (locationInput) payload.append('location', locationInput.value.trim());

    let url = `/workspace/${action}/`;
    if (pk) url += pk + '/';

    console.log(pk)
    console.log(url);
    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: payload
    })
    .then(r => r.json())
    .then(data => {
        if(data.ok) { closeModal(); location.reload(); }
        else alert(data.error || 'Error saving workspace');
    })
    .catch(err => alert('Error: ' + err));
}

// ------------------ Space ------------------
function submitSpace(action, id = null) {
    const name = document.getElementById('space-name')?.value || '';
    const width = document.getElementById('space-width')?.value || '';
    const height = document.getElementById('space-height')?.value || '';

    const urlParams = new URLSearchParams(window.location.search);
    const workspace = urlParams.get('workspace');
    if (!workspace) {
        showToast("Workspace not defined.", "error");
        return;
    }

    const formData = new FormData();
    formData.append('action', action);
    formData.append('name', name);
    formData.append('width',width);
    formData.append('height',height);

    const url = id ? `/space/${action}/${id}/` : `/space/create/${workspace}/`;

    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            closeModal();
            location.reload();
        } else {
            showToast(data.error, "error");
        }
    })
    .catch(err => showToast(err, "error"));
}

// ------------------ Seat ------------------
function submitSeat(action, pk=null) {
    const codeInput = document.getElementById('seat-code');
    const rowInput = document.getElementById('seat-row');
    const colInput = document.getElementById('seat-col');

    const urlParams = new URLSearchParams(window.location.search);
    
    const workspace = urlParams.get('workspace');
    
    if (!workspace) {
        showToast("Workspace not defined.", "error");
        return;
    }

    const space = urlParams.get('space');
    
    if (!space) {
        showToast("Space not defined.", "error");
        return;
    }

    const payload = new FormData();
    payload.append('action', action);
    if (codeInput) payload.append('code', codeInput.value.trim());
    if (rowInput) payload.append('row', rowInput.value.trim());
    if (colInput) payload.append('col', colInput.value.trim());

    const url = pk ? `/seat/${action}/${pk}/` : `/seat/create/${space}/`;

    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: payload
    })
    .then(r => r.json())
    .then(data => {
        if(data.ok) { closeModal(); location.reload(); }
        else showToast(data.error, "error");
    })
    .catch(err => showToast(err, "error"));
}

// --- AJAX Form Submission inside Modal ---
document.addEventListener('submit', function(e){
    const form = e.target.closest('#modal form');
    if(!form) return;
    e.preventDefault();

    // Disable submit button during processing
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<svg class="w-4 h-4 mr-1.5 inline animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Processing...';
        submitButton.dataset.originalText = originalText;
    }


    const data = new FormData(form);
    fetch(form.action, {
        method: form.method,
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With':'XMLHttpRequest'},
        body: data
    })
    .then(r => r.json())
    .then(resp => {
        if(resp.ok){ closeModal(); location.reload(); }
        else {
            if(resp.html) { document.getElementById('modal-content').innerHTML = resp.html; }
            else showToast(resp.error, "error");
        }
    })
    .catch(err => showToast(err, "error"))
    .finally(() => {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = submitButton.dataset.originalText;
        }
    });
});

// --- Seat Drag & Save ---
(function(){
    const map = document.getElementById('map');
    const saveBtn = document.getElementById('save-btn');
    const statusText = document.getElementById('status');
    let dragging=null, offset={x:0,y:0}, hasChanges=false;
    if(!map) return;

    // Initial state setup for save button (disabled until a change happens)
    saveBtn.disabled = true;
    saveBtn.classList.add('opacity-50');

    map.querySelectorAll('.seat-admin').forEach(el=>{
        el.addEventListener('pointerdown', e=>{
            dragging=el;
            el.setPointerCapture(e.pointerId);
            const rect=el.getBoundingClientRect();
            // const parentRect=map.getBoundingClientRect(); // Not needed inside this handler
            offset.x=e.clientX-rect.left; offset.y=e.clientY-rect.top;
            el.style.cursor='grabbing'; el.style.zIndex='100';
        });
        el.addEventListener('pointermove', e=>{
            if(!dragging || dragging!==el) return;
            const parentRect=map.getBoundingClientRect();
            let x=e.clientX-parentRect.left-offset.x;
            let y=e.clientY-parentRect.top-offset.y;
            x=Math.max(0,Math.min(parentRect.width-el.offsetWidth,x));
            y=Math.max(0,Math.min(parentRect.height-el.offsetHeight,y));
            el.style.left=x+'px'; el.style.top=y+'px';
        });
        el.addEventListener('pointerup', e=>{
            if(!dragging || dragging!==el) return;
            dragging.releasePointerCapture(e.pointerId);
            el.style.cursor='grab'; el.style.zIndex='';
            
            // Seat code is in the text content
            const seatCode = el.textContent.trim(); 
            
            statusText.innerHTML=`<svg class="w-4 h-4 mr-2 text-yellow-600 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>Seat ${seatCode} moved — Click Save to persist`;
            hasChanges=true; 
            saveBtn.disabled = false;
            saveBtn.classList.remove('opacity-50');
            saveBtn.classList.add('ring-2','ring-blue-400','animate-pulse');
            dragging=null;
        });
    });

    saveBtn?.addEventListener('click', async()=>{
        const payload=[];
        map.querySelectorAll('.seat-admin').forEach(el=>{
            payload.push({id:el.dataset.id, x:Math.round(parseFloat(el.style.left)), y:Math.round(parseFloat(el.style.top))});
        });
        statusText.innerHTML='<svg class="w-4 h-4 mr-2 text-blue-500 inline animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>Saving positions...';
        saveBtn.disabled=true; saveBtn.classList.add('opacity-50');
        try{
            const res = await fetch("{% url 'save_positions' %}", {
                method:'POST',
                headers:{'Content-Type':'application/json','X-CSRFToken':getCookie('csrftoken')},
                body:JSON.stringify(payload)
            });
            const data = await res.json();
            if(data.ok){ 
                statusText.innerHTML=`<svg class="w-4 h-4 mr-2 text-teal-600 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Successfully saved ${data.updated} seat positions`; 
                hasChanges=false; 
                saveBtn.disabled = true;
                saveBtn.classList.remove('ring-2','ring-blue-400','animate-pulse'); 
            }
            else{ 
                statusText.innerHTML='<svg class="w-4 h-4 mr-2 text-red-500 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Failed to save positions'; 
            }
        }catch(err){ 
            statusText.innerHTML=`<svg class="w-4 h-4 mr-2 text-red-500 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Error: ${err.message}`; 
        }
        finally{ 
            if (!hasChanges) {
                 saveBtn.disabled=true; 
                 saveBtn.classList.add('opacity-50');
            } else {
                 saveBtn.disabled=false;
                 saveBtn.classList.remove('opacity-50');
            }
        }
    });

    window.addEventListener('beforeunload', e=>{
        if(hasChanges){ e.preventDefault(); e.returnValue=''; return ''; }
    });
})();
