// static/script.js

const urlInput = document.getElementById('urlInput');
const qualitySelect = document.getElementById('qualitySelect');
const downloadBtn = document.getElementById('downloadBtn');
const statusDiv = document.getElementById('status');

urlInput.addEventListener('change', async () => {
  const url = urlInput.value.trim();
  qualitySelect.innerHTML = '<option value="" disabled selected>Loading qualities...</option>';
  qualitySelect.disabled = true;
  downloadBtn.disabled = true;
  statusDiv.textContent = '';

  if(!url) {
    qualitySelect.innerHTML = '<option value="" disabled selected>Select quality</option>';
    qualitySelect.disabled = true;
    return;
  }

  try {
    const res = await fetch('/api/get_qualities', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
    const data = await res.json();
    if(data.error) {
      statusDiv.textContent = 'Error: ' + data.error;
      qualitySelect.innerHTML = '<option value="" disabled selected>Select quality</option>';
      qualitySelect.disabled = true;
      return;
    }
    qualitySelect.innerHTML = '';
    data.qualities.forEach(q => {
      const option = document.createElement('option');
      option.value = q.itag;
      option.textContent = q.quality_label + ' ' + q.extension + (q.has_audio && q.has_video ? ' (audio+video)' : (q.has_audio ? ' (audio only)' : (q.has_video ? ' (video only)' : '')));
      qualitySelect.appendChild(option);
    });
    qualitySelect.disabled = false;
    downloadBtn.disabled = false;
    statusDiv.textContent = '';
  } catch(err) {
    qualitySelect.innerHTML = '<option value="" disabled selected>Select quality</option>';
    qualitySelect.disabled = true;
    statusDiv.textContent = 'Error fetching qualities.';
  }
});

downloadBtn.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  const itag = qualitySelect.value;
  if(!url || !itag) {
    statusDiv.textContent = 'Please enter URL and select quality.';
    return;
  }
  statusDiv.textContent = 'Preparing download...';
  downloadBtn.disabled = true;
  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, itag})
    });
    if (!res.ok) {
      const errJson = await res.json();
      throw new Error(errJson.error || 'Unknown error');
    }
    const blob = await res.blob();
    const disposition = res.headers.get('Content-Disposition');
    let filename = 'youtube_video.mp4';
    if(disposition) {
      const match = disposition.match(/filename="(.+)"/);
      if(match && match.length > 1) filename = match[1];
    }
    const a = document.createElement('a');
    const urlObject = URL.createObjectURL(blob);
    a.href = urlObject;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(urlObject);
    statusDiv.textContent = 'Download started!';
  } catch(err) {
    statusDiv.textContent = 'Error: ' + err.message;
  } finally {
    downloadBtn.disabled = false;
  }
});
