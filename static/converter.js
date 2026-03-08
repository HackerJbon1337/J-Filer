/**
 * J-Filer — Document Converter Frontend
 * Handles drag-and-drop, file management, conversion requests, and UI state.
 * Mirrors app.js patterns; wired to /api/convert instead of /api/merge.
 */

(function () {
    'use strict';

    // ═══ DOM References ═══════════════════════════════════
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileListCard = document.getElementById('file-list-card');
    const fileList = document.getElementById('file-list');
    const fileCount = document.getElementById('file-count');
    const controlsCard = document.getElementById('controls-card');
    const targetFormat = document.getElementById('target-format');
    const convertBtn = document.getElementById('convert-btn');
    const convertText = convertBtn.querySelector('.btn-merge-text');
    const convertLoad = convertBtn.querySelector('.btn-merge-loading');
    const resultCard = document.getElementById('result-card');
    const resultContent = document.getElementById('result-content');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const officeBadge = document.getElementById('office-badge');
    const toastContainer = document.getElementById('toast-container');
    const convNotice = document.getElementById('conv-notice');
    const convNoticeText = document.getElementById('conv-notice-text');

    // ═══ State ════════════════════════════════════════════
    let selectedFiles = [];
    let officeAvailable = false;

    // Conversions that require Microsoft Office (involve COM PDF export)
    const OFFICE_REQUIRED = new Set([
        'docx→pdf', 'pptx→pdf', 'docx→pptx', 'pptx→docx'
    ]);

    // ═══ Init ════════════════════════════════════════════
    checkOfficeStatus();
    setupDragAndDrop();
    setupEventListeners();

    // ═══ Office Status ════════════════════════════════════
    async function checkOfficeStatus() {
        try {
            const res = await fetch('/api/info');
            const data = await res.json();
            officeAvailable = data.office_available;

            const dot = officeBadge.querySelector('.badge-dot');
            const text = officeBadge.querySelector('.badge-text');

            if (officeAvailable) {
                dot.className = 'badge-dot active';
                text.textContent = 'Office Ready';
            } else {
                dot.className = 'badge-dot inactive';
                text.textContent = 'Office Not Found';
            }
        } catch {
            officeBadge.querySelector('.badge-dot').className = 'badge-dot inactive';
            officeBadge.querySelector('.badge-text').textContent = 'Status Unknown';
        }
        updateNotice();
    }

    // ═══ Drag & Drop ══════════════════════════════════════
    function setupDragAndDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
            dropZone.addEventListener(event, e => { e.preventDefault(); e.stopPropagation(); });
        });

        dropZone.addEventListener('dragenter', () => dropZone.classList.add('drag-over'));
        dropZone.addEventListener('dragover', () => dropZone.classList.add('drag-over'));
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

        dropZone.addEventListener('drop', e => {
            dropZone.classList.remove('drag-over');
            addFiles(Array.from(e.dataTransfer.files));
        });

        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            addFiles(Array.from(fileInput.files));
            fileInput.value = '';
        });
    }

    // ═══ Event Listeners ══════════════════════════════════
    function setupEventListeners() {
        clearAllBtn.addEventListener('click', clearAllFiles);
        convertBtn.addEventListener('click', handleConvert);
        targetFormat.addEventListener('change', updateNotice);
    }

    // ═══ File Management ══════════════════════════════════
    const ALLOWED_EXT = ['.pdf', '.docx', '.pptx', '.doc', '.ppt'];

    function addFiles(files) {
        let added = 0;
        files.forEach(file => {
            const ext = getExtension(file.name);
            if (!ALLOWED_EXT.includes(ext)) {
                showToast(`Skipped "${file.name}" — unsupported format`, 'error');
                return;
            }
            const isDup = selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (isDup) { showToast(`"${file.name}" already added`, 'info'); return; }
            selectedFiles.push(file);
            added++;
        });
        if (added > 0) showToast(`Added ${added} file${added > 1 ? 's' : ''}`, 'success');
        renderFileList();
        updateUI();
    }

    function removeFile(index) {
        const [removed] = selectedFiles.splice(index, 1);
        showToast(`Removed "${removed.name}"`, 'info');
        renderFileList();
        updateUI();
    }

    function clearAllFiles() {
        selectedFiles = [];
        renderFileList();
        updateUI();
        resultCard.style.display = 'none';
        showToast('All files cleared', 'info');
    }

    function normalizeExt(rawExt) {
        const e = rawExt.replace('.', '');
        if (e === 'doc') return 'docx';
        if (e === 'ppt') return 'pptx';
        return e;
    }

    function renderFileList() {
        fileList.innerHTML = '';
        selectedFiles.forEach((file, idx) => {
            const rawExt = getExtension(file.name).replace('.', '');
            const fmt = normalizeExt(getExtension(file.name));
            const li = document.createElement('li');
            li.className = 'file-item';
            li.style.animationDelay = `${idx * 0.05}s`;
            li.innerHTML = `
                <div class="file-type-badge ${rawExt}">${rawExt}</div>
                <div class="file-info">
                    <div class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
                    <div class="file-size">${formatSize(file.size)}</div>
                </div>
                <div class="conv-arrow-inline">
                    <svg width="18" height="8" viewBox="0 0 18 8" fill="none">
                        <path d="M0 4h15M11 1l4 3-4 3" stroke="url(#cai${idx})" stroke-width="1.3"
                            stroke-linecap="round" stroke-linejoin="round"/>
                        <defs>
                            <linearGradient id="cai${idx}" x1="0" y1="0" x2="18" y2="0">
                                <stop stop-color="#60a5fa"/><stop offset="1" stop-color="#a78bfa"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <span class="target-fmt-preview" data-src="${fmt}"></span>
                </div>
                <button class="file-remove" data-index="${idx}" title="Remove file">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            `;
            li.querySelector('.file-remove').addEventListener('click', e => {
                e.stopPropagation();
                removeFile(idx);
            });
            fileList.appendChild(li);
        });
        refreshTargetPreviews();
    }

    function refreshTargetPreviews() {
        const tgt = targetFormat.value;
        document.querySelectorAll('.target-fmt-preview').forEach(el => {
            const src = el.dataset.src;
            if (src === tgt) {
                el.textContent = '(same format)';
                el.className = 'target-fmt-preview same';
            } else {
                el.textContent = tgt.toUpperCase();
                el.className = `target-fmt-preview fmt-pill ${tgt}`;
            }
        });
    }

    function updateUI() {
        const hasFiles = selectedFiles.length > 0;
        fileListCard.style.display = hasFiles ? 'block' : 'none';
        controlsCard.style.display = hasFiles ? 'block' : 'none';
        fileCount.textContent = selectedFiles.length;
        updateConvertBtn();
        updateNotice();
    }

    function updateConvertBtn() {
        const tgt = targetFormat.value;
        // Disable if no files OR all files are already in target format
        const allSame = selectedFiles.length > 0 &&
            selectedFiles.every(f => normalizeExt(getExtension(f.name)) === tgt);
        convertBtn.disabled = selectedFiles.length === 0 || allSame;
    }

    function updateNotice() {
        if (selectedFiles.length === 0) { convNotice.style.display = 'none'; return; }

        const tgt = targetFormat.value;
        const needsOffice = selectedFiles.some(f => {
            const src = normalizeExt(getExtension(f.name));
            return OFFICE_REQUIRED.has(`${src}→${tgt}`);
        });

        if (needsOffice && !officeAvailable) {
            convNoticeText.textContent =
                'This conversion requires Microsoft Office (not detected on this machine).';
            convNotice.style.display = 'flex';
        } else if (needsOffice && officeAvailable) {
            convNoticeText.textContent = 'Microsoft Office will be used for this conversion.';
            convNotice.style.display = 'flex';
        } else {
            convNotice.style.display = 'none';
        }
        refreshTargetPreviews();
        updateConvertBtn();
    }

    // ═══ Conversion ═══════════════════════════════════════
    let progressInterval = null;

    async function handleConvert() {
        if (selectedFiles.length === 0) return;

        const tgt = targetFormat.value;

        // Filter out same-format files
        const filesToConvert = selectedFiles.filter(
            f => normalizeExt(getExtension(f.name)) !== tgt
        );

        if (filesToConvert.length === 0) {
            showToast('All selected files are already in the target format.', 'info');
            return;
        }

        setConverting(true);
        showProgress(true);
        resultCard.style.display = 'none';

        const formData = new FormData();
        filesToConvert.forEach(f => formData.append('files[]', f));
        formData.append('target_format', tgt);

        try {
            const result = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                // Upload progress (0–50%)
                xhr.upload.addEventListener('progress', e => {
                    if (e.lengthComputable) {
                        updateProgress(Math.round((e.loaded / e.total) * 50), 'Uploading files…');
                    }
                });

                xhr.upload.addEventListener('loadend', () => {
                    updateProgress(50, 'Converting documents…');
                    let pct = 50;
                    progressInterval = setInterval(() => {
                        pct += Math.random() * 5 + 1;
                        if (pct > 90) pct = 90;
                        updateProgress(Math.round(pct), 'Converting…');
                    }, 350);
                });

                xhr.addEventListener('load', () => {
                    clearInterval(progressInterval);
                    if (xhr.status >= 200 && xhr.status < 300) {
                        updateProgress(100, 'Complete!');
                        const blob = xhr.response;
                        const cd = xhr.getResponseHeader('Content-Disposition') || '';
                        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                        const filename = match
                            ? match[1].replace(/['"]/g, '')
                            : `converted.${tgt}`;
                        setTimeout(() => { showProgress(false); resolve({ blob, filename }); }, 600);
                    } else {
                        const reader = new FileReader();
                        reader.onload = () => {
                            try { reject(new Error(JSON.parse(reader.result).error || 'Conversion failed')); }
                            catch { reject(new Error('Conversion failed')); }
                        };
                        reader.readAsText(xhr.response);
                    }
                });

                xhr.addEventListener('error', () => {
                    clearInterval(progressInterval);
                    reject(new Error('Network error during conversion'));
                });

                xhr.open('POST', '/api/convert');
                xhr.responseType = 'blob';
                xhr.send(formData);
            });

            const isBatch = filesToConvert.length > 1;
            showSuccess(result.blob, result.filename, filesToConvert.length, isBatch);
            showToast(
                isBatch
                    ? `${filesToConvert.length} files converted and zipped!`
                    : 'File converted successfully!',
                'success'
            );
        } catch (err) {
            clearInterval(progressInterval);
            showProgress(false);
            showError(err.message);
            showToast(err.message, 'error');
        } finally {
            setConverting(false);
        }
    }

    function setConverting(loading) {
        convertBtn.disabled = loading;
        convertText.style.display = loading ? 'none' : 'inline';
        convertLoad.style.display = loading ? 'flex' : 'none';
    }

    // ═══ Progress ═════════════════════════════════════════
    const progressCard = document.getElementById('progress-card');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressRingFill = document.getElementById('progress-ring-fill');
    const progressPercent = document.getElementById('progress-percent');
    const progressTitle = document.getElementById('progress-title');
    const progressSubtitle = document.getElementById('progress-subtitle');
    const RING_CIRC = 125.66;

    function showProgress(visible) {
        progressCard.style.display = visible ? 'block' : 'none';
        if (visible) {
            updateProgress(0, 'Preparing files');
            progressCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function updateProgress(pct, stage) {
        progressBarFill.style.width = pct + '%';
        progressPercent.textContent = pct + '%';
        progressRingFill.style.strokeDashoffset = RING_CIRC - (pct / 100) * RING_CIRC;
        progressTitle.textContent = pct >= 100 ? 'Conversion complete!' : 'Converting…';
        progressSubtitle.textContent = stage || '';
    }

    // ═══ Results ══════════════════════════════════════════
    function showSuccess(blob, filename, fileCount, isBatch) {
        const url = URL.createObjectURL(blob);
        resultCard.style.display = 'block';

        const subtitle = isBatch
            ? `${fileCount} files converted — packed into <strong>${escapeHtml(filename)}</strong> (${formatSize(blob.size)})`
            : `Converted to <strong>${escapeHtml(filename)}</strong> (${formatSize(blob.size)})`;

        resultContent.innerHTML = `
            <div class="result-success-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                    <path d="M7 14l5 5L21 9" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="result-title" style="color: var(--accent-emerald);">Conversion Complete!</div>
            <div class="result-subtitle">${subtitle}</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;">
                <button class="btn-download" id="download-btn">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M8 2v9M4 8l4 4 4-4M2 13h12" stroke="currentColor" stroke-width="1.5"
                            stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Download${isBatch ? ' ZIP' : ''}
                </button>
                <button class="btn-new-merge" id="new-conv-btn">New Conversion</button>
            </div>
        `;

        document.getElementById('download-btn').addEventListener('click', () => {
            const a = document.createElement('a');
            a.href = url; a.download = filename; a.click();
        });
        document.getElementById('new-conv-btn').addEventListener('click', () => {
            clearAllFiles();
            resultCard.style.display = 'none';
        });
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function showError(message) {
        resultCard.style.display = 'block';
        resultContent.innerHTML = `
            <div class="result-error-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                    <path d="M9 9l10 10M19 9L9 19" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
            </div>
            <div class="result-title" style="color:#f87171;">Conversion Failed</div>
            <div class="result-subtitle">${escapeHtml(message)}</div>
            <button class="btn-new-merge" id="retry-btn">Try Again</button>
        `;
        document.getElementById('retry-btn').addEventListener('click', () => {
            resultCard.style.display = 'none';
        });
    }

    // ═══ Toasts ═══════════════════════════════════════════
    function showToast(message, type = 'info') {
        const icons = {
            success: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#34d399" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#34d399" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            error: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#ef4444" stroke-width="1.5"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round"/></svg>',
            info: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#60a5fa" stroke-width="1.5"/><path d="M8 5v0M8 7v4" stroke="#60a5fa" stroke-width="1.5" stroke-linecap="round"/></svg>'
        };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span>${escapeHtml(message)}`;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // ═══ Helpers ══════════════════════════════════════════
    function getExtension(filename) {
        return ('.' + filename.split('.').pop()).toLowerCase();
    }
    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ═══════════════════════════════════════════════════════
    // ═══ IMAGE MODE ════════════════════════════════════════
    // ═══════════════════════════════════════════════════════

    const modeDocBtn    = document.getElementById('mode-doc-btn');
    const modeImgBtn    = document.getElementById('mode-img-btn');
    const docModeDiv    = document.getElementById('doc-mode');
    const imgModeDiv    = document.getElementById('img-mode');

    // DOM refs for image mode
    const imgDropZone      = document.getElementById('img-drop-zone');
    const imgFileInput     = document.getElementById('img-file-input');
    const imgFileListCard  = document.getElementById('img-file-list-card');
    const imgFileList      = document.getElementById('img-file-list');
    const imgFileCount     = document.getElementById('img-file-count');
    const imgControlsCard  = document.getElementById('img-controls-card');
    const imgConvertBtn    = document.getElementById('img-convert-btn');
    const imgConvertText   = imgConvertBtn.querySelector('.btn-merge-text');
    const imgConvertLoad   = imgConvertBtn.querySelector('.btn-merge-loading');
    const imgClearBtn      = document.getElementById('img-clear-btn');

    const IMAGE_ALLOWED = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.gif'];
    let imgFiles = [];

    // ─── Mode Switching ────────────────────────────────────
    function switchToDocMode() {
        modeDocBtn.classList.add('active');
        modeImgBtn.classList.remove('active');
        modeDocBtn.setAttribute('aria-selected', 'true');
        modeImgBtn.setAttribute('aria-selected', 'false');
        docModeDiv.style.display = 'block';
        imgModeDiv.style.display = 'none';
        resultCard.style.display = 'none';
    }
    function switchToImgMode() {
        modeImgBtn.classList.add('active');
        modeDocBtn.classList.remove('active');
        modeImgBtn.setAttribute('aria-selected', 'true');
        modeDocBtn.setAttribute('aria-selected', 'false');
        imgModeDiv.style.display = 'block';
        docModeDiv.style.display = 'none';
        resultCard.style.display = 'none';
    }

    modeDocBtn.addEventListener('click', switchToDocMode);
    modeImgBtn.addEventListener('click', switchToImgMode);

    // ─── Drag & Drop (Images) ──────────────────────────────
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
        imgDropZone.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); });
    });
    imgDropZone.addEventListener('dragenter', () => imgDropZone.classList.add('drag-over'));
    imgDropZone.addEventListener('dragover',  () => imgDropZone.classList.add('drag-over'));
    imgDropZone.addEventListener('dragleave', () => imgDropZone.classList.remove('drag-over'));
    imgDropZone.addEventListener('drop', e => {
        imgDropZone.classList.remove('drag-over');
        addImgFiles(Array.from(e.dataTransfer.files));
    });
    imgDropZone.addEventListener('click', () => imgFileInput.click());
    imgFileInput.addEventListener('change', () => {
        addImgFiles(Array.from(imgFileInput.files));
        imgFileInput.value = '';
    });

    imgClearBtn.addEventListener('click', () => {
        imgFiles = [];
        renderImgList();
        updateImgUI();
        resultCard.style.display = 'none';
        showToast('All images cleared', 'info');
    });
    imgConvertBtn.addEventListener('click', handleImgConvert);

    // ─── File Management (Images) ──────────────────────────
    function addImgFiles(files) {
        let added = 0;
        files.forEach(file => {
            const ext = getExtension(file.name);
            if (!IMAGE_ALLOWED.includes(ext)) {
                showToast(`Skipped "${file.name}" — not an image`, 'error');
                return;
            }
            const isDup = imgFiles.some(f => f.name === file.name && f.size === file.size);
            if (isDup) { showToast(`"${file.name}" already added`, 'info'); return; }
            imgFiles.push(file);
            added++;
        });
        if (added > 0) showToast(`Added ${added} image${added > 1 ? 's' : ''}`, 'success');
        renderImgList();
        updateImgUI();
    }

    function removeImgFile(index) {
        const [r] = imgFiles.splice(index, 1);
        showToast(`Removed "${r.name}"`, 'info');
        renderImgList();
        updateImgUI();
    }

    function renderImgList() {
        imgFileList.innerHTML = '';
        imgFiles.forEach((file, idx) => {
            const li = document.createElement('li');
            li.className = 'file-item';
            li.style.animationDelay = `${idx * 0.05}s`;

            // Create thumbnail using object URL
            const thumbUrl = URL.createObjectURL(file);
            li.innerHTML = `
                <img class="img-thumb" src="${thumbUrl}" alt="${escapeHtml(file.name)}">
                <div class="file-info">
                    <div class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
                    <div class="file-size">${formatSize(file.size)}</div>
                </div>
                <span class="file-type-badge" style="background:rgba(251,146,60,0.15);color:#fb923c;border:1px solid rgba(251,146,60,0.25);font-size:0.68rem;">Page ${idx + 1}</span>
                <button class="file-remove" data-index="${idx}" title="Remove image">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            `;
            li.querySelector('.file-remove').addEventListener('click', e => {
                e.stopPropagation();
                URL.revokeObjectURL(thumbUrl);
                removeImgFile(idx);
            });
            imgFileList.appendChild(li);
        });
    }

    function updateImgUI() {
        const has = imgFiles.length > 0;
        imgFileListCard.style.display = has ? 'block' : 'none';
        imgControlsCard.style.display = has ? 'block' : 'none';
        imgFileCount.textContent = imgFiles.length;
        imgConvertBtn.disabled = !has;
    }

    // ─── Conversion (Images → PDF/PPTX) ─────────────────────────
    async function handleImgConvert() {
        if (imgFiles.length === 0) return;

        const tgtFormatSelect = document.getElementById('img-target-format');
        const tgtFormat = tgtFormatSelect ? tgtFormatSelect.value : 'pdf';
        const isPdf = tgtFormat === 'pdf';
        
        const endpoint = isPdf ? '/api/images-to-pdf' : '/api/images-to-pptx';
        const ext = isPdf ? 'pdf' : 'pptx';
        const formatName = isPdf ? 'PDF' : 'PowerPoint';

        setImgConverting(true);
        showProgress(true);
        resultCard.style.display = 'none';

        const formData = new FormData();
        imgFiles.forEach(f => formData.append('files[]', f));

        try {
            const result = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.upload.addEventListener('progress', e => {
                    if (e.lengthComputable)
                        updateProgress(Math.round((e.loaded / e.total) * 50), 'Uploading images…');
                });
                xhr.upload.addEventListener('loadend', () => {
                    updateProgress(50, `Building ${formatName}…`);
                    let pct = 50;
                    progressInterval = setInterval(() => {
                        pct += Math.random() * 6 + 2;
                        if (pct > 90) pct = 90;
                        updateProgress(Math.round(pct), 'Rendering pages…');
                    }, 300);
                });
                xhr.addEventListener('load', () => {
                    clearInterval(progressInterval);
                    if (xhr.status >= 200 && xhr.status < 300) {
                        updateProgress(100, 'Complete!');
                        const blob = xhr.response;
                        setTimeout(() => { showProgress(false); resolve({ blob, filename: `images.${ext}` }); }, 600);
                    } else {
                        const reader = new FileReader();
                        reader.onload = () => {
                            try { reject(new Error(JSON.parse(reader.result).error || 'Conversion failed')); }
                            catch { reject(new Error('Conversion failed')); }
                        };
                        reader.readAsText(xhr.response);
                    }
                });
                xhr.addEventListener('error', () => {
                    clearInterval(progressInterval);
                    reject(new Error('Network error'));
                });

                xhr.open('POST', endpoint);
                xhr.responseType = 'blob';
                xhr.send(formData);
            });

            showSuccess(result.blob, result.filename, imgFiles.length, false);
            showToast(`${imgFiles.length} image${imgFiles.length > 1 ? 's' : ''} converted to ${formatName}!`, 'success');
        } catch (err) {
            clearInterval(progressInterval);
            showProgress(false);
            showError(err.message);
            showToast(err.message, 'error');
        } finally {
            setImgConverting(false);
        }
    }

    function setImgConverting(loading) {
        imgConvertBtn.disabled = loading;
        imgConvertText.style.display = loading ? 'none' : 'inline';
        imgConvertLoad.style.display = loading ? 'flex' : 'none';
    }

})();

