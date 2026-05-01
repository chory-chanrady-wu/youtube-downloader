const urlInput = document.getElementById('urlInput');
const formatSelect = document.getElementById('formatSelect');
const qualitySelect = document.getElementById('qualitySelect');
const checkButton = document.getElementById('checkButton');
const downloadButton = document.getElementById('downloadButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const statusText = document.getElementById('statusText');
const progressBar = document.getElementById('progressBar');
const formatInfo = document.getElementById('formatInfo');
const downloadLink = document.getElementById('downloadLink');

let activeJobId = null;
let progressTimer = null;

function setLoading(isLoading) {
  loadingIndicator.classList.toggle('hidden', !isLoading);
  checkButton.disabled = isLoading;
  downloadButton.disabled = isLoading;
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.classList.toggle('error', isError);
}

function setProgress(percent) {
  progressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
}

function showDownloadLink(url) {
  downloadLink.href = url;
  downloadLink.classList.remove('hidden');
}

function hideDownloadLink() {
  downloadLink.classList.add('hidden');
  downloadLink.removeAttribute('href');
}

function resetResult() {
  setProgress(0);
  hideDownloadLink();
  activeJobId = null;
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
}

async function fetchFormats() {
  const url = urlInput.value.trim();
  if (!url) {
    setStatus('Paste a YouTube URL first.');
    return;
  }

  setLoading(true);
  setStatus('Inspecting available formats...');
  formatInfo.textContent = '';

  try {
    const response = await fetch('/api/formats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Could not load formats');
    }

    formatInfo.textContent = `Title: ${data.title} | Available quality: ${data.available_qualities.join(', ')} | Audio: ${data.audio_available ? 'yes' : 'no'}`;
    if (data.available_qualities.length) {
      const current = qualitySelect.value;
      qualitySelect.innerHTML = data.available_qualities.map((quality) => `<option value="${quality}">${quality}</option>`).join('');
      if (data.available_qualities.includes(current)) {
        qualitySelect.value = current;
      }
    }
    setStatus('Formats loaded.', false);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setLoading(false);
  }
}

async function pollProgress(jobId) {
  const response = await fetch(`/api/progress/${jobId}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Could not read progress');
  }

  setProgress(data.progress * 100);
  setStatus(`${data.status} — ${(data.progress * 100).toFixed(0)}%`);

  if (data.status === 'ready' && data.file_name) {
    clearInterval(progressTimer);
    progressTimer = null;
    setStatus('Download ready.');
    showDownloadLink(`/api/download/${jobId}/file`);
    setProgress(100);
  }

  if (data.status === 'failed') {
    clearInterval(progressTimer);
    progressTimer = null;
    setStatus(data.error || 'Download failed.', true);
  }
}

async function startDownload() {
  const url = urlInput.value.trim();
  if (!url) {
    setStatus('Paste a YouTube URL first.');
    return;
  }

  resetResult();
  setLoading(true);
  setStatus('Starting download...');

  try {
    const response = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        format_type: formatSelect.value,
        quality: qualitySelect.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Could not start download');
    }

    activeJobId = data.job_id;
    setStatus('Download queued.', false);
    progressTimer = setInterval(() => {
      if (activeJobId) {
        pollProgress(activeJobId).catch((error) => setStatus(error.message, true));
      }
    }, 1000);
    await pollProgress(activeJobId);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setLoading(false);
  }
}

checkButton.addEventListener('click', fetchFormats);
downloadButton.addEventListener('click', startDownload);
urlInput.addEventListener('blur', () => {
  if (urlInput.value.trim()) {
    fetchFormats().catch(() => {});
  }
});

