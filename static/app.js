/**
 * Universal Document Merger — Frontend Logic
 * Handles drag-and-drop, file management, merge requests, and UI state.
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
    const outputFormat = document.getElementById('output-format');
    const mergeBtn = document.getElementById('merge-btn');
    const mergeBtnText = mergeBtn.querySelector('.btn-merge-text');
    const mergeBtnLoading = mergeBtn.querySelector('.btn-merge-loading');
    const resultCard = document.getElementById('result-card');
    const resultContent = document.getElementById('result-content');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const officeBadge = document.getElementById('office-badge');
    const toastContainer = document.getElementById('toast-container');

    // ═══ State ════════════════════════════════════════════
    let selectedFiles = [];
    let officeAvailable = false;

    // ═══ Init ═════════════════════════════════════════════
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
            const dot = officeBadge.querySelector('.badge-dot');
            const text = officeBadge.querySelector('.badge-text');
            dot.className = 'badge-dot inactive';
            text.textContent = 'Status Unknown';
        }
    }

    // ═══ Drag & Drop ══════════════════════════════════════
    function setupDragAndDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
            dropZone.addEventListener(event, e => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        dropZone.addEventListener('dragenter', () => dropZone.classList.add('drag-over'));
        dropZone.addEventListener('dragover', () => dropZone.classList.add('drag-over'));
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

        dropZone.addEventListener('drop', e => {
            dropZone.classList.remove('drag-over');
            const files = Array.from(e.dataTransfer.files);
            addFiles(files);
        });

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', () => {
            const files = Array.from(fileInput.files);
            addFiles(files);
            fileInput.value = '';
        });
    }

    // ═══ Event Listeners ══════════════════════════════════
    function setupEventListeners() {
        clearAllBtn.addEventListener('click', clearAllFiles);
        mergeBtn.addEventListener('click', handleMerge);
    }

    // ═══ File Management ══════════════════════════════════
    const ALLOWED_EXT = ['.pdf', '.docx', '.pptx', '.doc', '.ppt'];

    function addFiles(files) {
        let addedCount = 0;

        files.forEach(file => {
            const ext = getExtension(file.name);
            if (!ALLOWED_EXT.includes(ext)) {
                showToast(`Skipped "${file.name}" — unsupported format`, 'error');
                return;
            }
            // Prevent exact duplicates
            const isDuplicate = selectedFiles.some(f =>
                f.name === file.name && f.size === file.size
            );
            if (isDuplicate) {
                showToast(`"${file.name}" already added`, 'info');
                return;
            }
            selectedFiles.push(file);
            addedCount++;
        });

        if (addedCount > 0) {
            showToast(`Added ${addedCount} file${addedCount > 1 ? 's' : ''}`, 'success');
        }

        renderFileList();
        updateUI();
    }

    function removeFile(index) {
        const removed = selectedFiles.splice(index, 1);
        showToast(`Removed "${removed[0].name}"`, 'info');
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

    function renderFileList() {
        fileList.innerHTML = '';

        selectedFiles.forEach((file, idx) => {
            const ext = getExtension(file.name).replace('.', '');
            const li = document.createElement('li');
            li.className = 'file-item';
            li.style.animationDelay = `${idx * 0.05}s`;
            li.innerHTML = `
                <div class="file-type-badge ${ext}">${ext}</div>
                <div class="file-info">
                    <div class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
                    <div class="file-size">${formatSize(file.size)}</div>
                </div>
                <button class="file-remove" data-index="${idx}" title="Remove file">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            `;

            const removeBtn = li.querySelector('.file-remove');
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeFile(idx);
            });

            fileList.appendChild(li);
        });
    }

    function updateUI() {
        const hasFiles = selectedFiles.length > 0;

        fileListCard.style.display = hasFiles ? 'block' : 'none';
        controlsCard.style.display = hasFiles ? 'block' : 'none';

        fileCount.textContent = selectedFiles.length;
        mergeBtn.disabled = selectedFiles.length < 2;

        // Auto-select best output format
        const types = new Set(selectedFiles.map(f => {
            const ext = getExtension(f.name).replace('.', '');
            if (ext === 'doc') return 'docx';
            if (ext === 'ppt') return 'pptx';
            return ext;
        }));

        if (types.size === 1) {
            outputFormat.value = types.values().next().value;
        } else if (types.size > 1) {
            outputFormat.value = 'pdf';
        }
    }

    // ═══ Merge ════════════════════════════════════════════
    let progressInterval = null;

    async function handleMerge() {
        if (selectedFiles.length < 2) return;

        const format = outputFormat.value;

        // Check cross-format requirements
        const types = new Set(selectedFiles.map(f => {
            const ext = getExtension(f.name).replace('.', '');
            if (ext === 'doc') return 'docx';
            if (ext === 'ppt') return 'pptx';
            return ext;
        }));

        if (types.size > 1 && !officeAvailable && format !== 'pdf') {
            showToast('Cross-format merge requires Microsoft Office', 'error');
            return;
        }

        // Show progress
        setMerging(true);
        showProgress(true);
        resultCard.style.display = 'none';

        const formData = new FormData();
        selectedFiles.forEach(f => formData.append('files[]', f));
        formData.append('output_format', format);

        try {
            // Use XMLHttpRequest for upload progress
            const result = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                // Upload progress (0-50%)
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const uploadPct = Math.round((e.loaded / e.total) * 50);
                        updateProgress(uploadPct, 'Uploading files…');
                    }
                });

                xhr.upload.addEventListener('loadend', () => {
                    updateProgress(50, 'Processing & merging…');
                    // Simulate processing progress (50-90%)
                    let processPct = 50;
                    progressInterval = setInterval(() => {
                        processPct += Math.random() * 4 + 1;
                        if (processPct > 90) processPct = 90;
                        updateProgress(Math.round(processPct), 'Merging documents…');
                    }, 300);
                });

                xhr.addEventListener('load', () => {
                    clearInterval(progressInterval);
                    if (xhr.status >= 200 && xhr.status < 300) {
                        updateProgress(100, 'Complete!');
                        const blob = xhr.response;
                        const contentDisposition = xhr.getResponseHeader('Content-Disposition') || '';
                        const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
                        const filename = filenameMatch ? filenameMatch[1] : `merged.${format === 'auto' ? 'pdf' : format}`;
                        setTimeout(() => {
                            showProgress(false);
                            resolve({ blob, filename });
                        }, 600);
                    } else {
                        try {
                            const reader = new FileReader();
                            reader.onload = () => {
                                const err = JSON.parse(reader.result);
                                reject(new Error(err.error || 'Merge failed'));
                            };
                            reader.readAsText(xhr.response);
                        } catch {
                            reject(new Error('Merge failed'));
                        }
                    }
                });

                xhr.addEventListener('error', () => {
                    clearInterval(progressInterval);
                    reject(new Error('Network error during merge'));
                });

                xhr.open('POST', '/api/merge');
                xhr.responseType = 'blob';
                xhr.send(formData);
            });

            showSuccess(result.blob, result.filename);
            showToast('Documents merged successfully!', 'success');

        } catch (err) {
            clearInterval(progressInterval);
            showProgress(false);
            showError(err.message);
            showToast(err.message, 'error');
        } finally {
            setMerging(false);
        }
    }

    function setMerging(loading) {
        mergeBtn.disabled = loading;
        mergeBtnText.style.display = loading ? 'none' : 'inline';
        mergeBtnLoading.style.display = loading ? 'flex' : 'none';
    }

    // ═══ Progress Bar ═════════════════════════════════════
    const progressCard = document.getElementById('progress-card');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressRingFill = document.getElementById('progress-ring-fill');
    const progressPercent = document.getElementById('progress-percent');
    const progressTitle = document.getElementById('progress-title');
    const progressSubtitle = document.getElementById('progress-subtitle');
    const RING_CIRCUMFERENCE = 125.66; // 2 * π * 20

    function showProgress(visible) {
        progressCard.style.display = visible ? 'block' : 'none';
        if (visible) {
            updateProgress(0, 'Preparing files');
            progressCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function updateProgress(percent, stage) {
        progressBarFill.style.width = percent + '%';
        progressPercent.textContent = percent + '%';
        const offset = RING_CIRCUMFERENCE - (percent / 100) * RING_CIRCUMFERENCE;
        progressRingFill.style.strokeDashoffset = offset;
        progressTitle.textContent = percent >= 100 ? 'Merge complete!' : 'Merging documents…';
        progressSubtitle.textContent = stage || '';
    }

    // ═══ Results ══════════════════════════════════════════
    function showSuccess(blob, filename) {
        const url = URL.createObjectURL(blob);

        resultCard.style.display = 'block';
        resultContent.innerHTML = `
            <div class="result-success-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                    <path d="M7 14l5 5L21 9" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="result-title" style="color: var(--accent-emerald);">Merge Complete!</div>
            <div class="result-subtitle">${selectedFiles.length} files merged into <strong>${escapeHtml(filename)}</strong> (${formatSize(blob.size)})</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;">
                <button class="btn-download" id="download-btn">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M8 2v9M4 8l4 4 4-4M2 13h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Download
                </button>
                <button class="btn-new-merge" id="new-merge-btn">New Merge</button>
            </div>
        `;

        document.getElementById('download-btn').addEventListener('click', () => {
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
        });

        document.getElementById('new-merge-btn').addEventListener('click', () => {
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
            <div class="result-title" style="color: #f87171;">Merge Failed</div>
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
})();
