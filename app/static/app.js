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
let activeFileHandle = null;
let lastKnownTitle = 'video';

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

function buildSuggestedFileName() {
  const extension = formatSelect.value === 'audio' ? 'mp3' : 'mp4';
  return `${lastKnownTitle}.${extension}`;
}

async function promptForSaveLocation() {
  if (!window.showSaveFilePicker) {
    return null;
  }

  const isAudio = formatSelect.value === 'audio';
  return window.showSaveFilePicker({
    suggestedName: buildSuggestedFileName(),
    types: [
      {
        description: isAudio ? 'MP3 audio file' : 'MP4 video file',
        accept: {
          [isAudio ? 'audio/mpeg' : 'video/mp4']: [isAudio ? '.mp3' : '.mp4'],
        },
      },
    ],
  });
}

async function saveResponseToHandle(response, handle) {
  const blob = await response.blob();
  const writable = await handle.createWritable();
  try {
    await writable.write(blob);
  } finally {
    await writable.close();
  }
}

function resetResult() {
  setProgress(0);
  hideDownloadLink();
  activeJobId = null;
  activeFileHandle = null;
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

    lastKnownTitle = data.title || 'video';
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
    setProgress(100);

    const downloadUrl = `/api/download/${jobId}/file`;
    if (activeFileHandle && window.showSaveFilePicker) {
      try {
        const downloadResponse = await fetch(downloadUrl);
        if (!downloadResponse.ok) {
          const errorData = await downloadResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Could not fetch the file');
        }
        await saveResponseToHandle(downloadResponse, activeFileHandle);
        setStatus(`Saved as ${data.file_name}.`);
      } catch (error) {
        setStatus(error.message || 'Download ready, but saving failed.', true);
        showDownloadLink(downloadUrl);
      }
    } else {
      setStatus('Download ready.');
      showDownloadLink(downloadUrl);
      downloadLink.click();
    }
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

  try {
    activeFileHandle = await promptForSaveLocation();
  } catch (error) {
    if (error && error.name === 'AbortError') {
      setStatus('Save canceled.', true);
    } else {
      setStatus(error.message || 'Could not open the save dialog.', true);
    }
    setLoading(false);
    return;
  }

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
