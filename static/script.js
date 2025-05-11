const urlInput = document.getElementById('urlInput');
const qualitySelect = document.getElementById('qualitySelect');
const downloadBtn = document.getElementById('downloadBtn');
const statusDiv = document.getElementById('status');

// Debounce function to prevent rapid API calls
function debounce(func, timeout = 500) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

const fetchQualities = async (url) => {
    qualitySelect.innerHTML = '<option value="" disabled selected>Loading qualities...</option>';
    qualitySelect.disabled = true;
    downloadBtn.disabled = true;
    statusDiv.textContent = '';
    statusDiv.style.color = '#3D52A0';

    try {
        const res = await fetch('/api/get_qualities', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url})
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || 'Failed to fetch qualities');
        }

        const data = await res.json();
        
        if (data.error) {
            throw new Error(data.error);
        }

        qualitySelect.innerHTML = '';
        data.qualities.forEach(q => {
            const option = document.createElement('option');
            option.value = q.itag;
            let label = `${q.quality_label} (${q.ext})`;
            if (q.has_audio && q.has_video) label += ' - Audio+Video';
            else if (q.has_audio) label += ' - Audio Only';
            else if (q.has_video) label += ' - Video Only';
            option.textContent = label;
            qualitySelect.appendChild(option);
        });

        qualitySelect.disabled = false;
        downloadBtn.disabled = false;
        statusDiv.textContent = 'Select quality and click download';
        
    } catch(err) {
        qualitySelect.innerHTML = '<option value="" disabled selected>Select quality</option>';
        qualitySelect.disabled = true;
        statusDiv.textContent = err.message;
        statusDiv.style.color = '#ff6b6b';
    }
};

// Use debounced version for input changes
urlInput.addEventListener('input', debounce(() => {
    const url = urlInput.value.trim();
    if (!url) {
        qualitySelect.innerHTML = '<option value="" disabled selected>Select quality</option>';
        qualitySelect.disabled = true;
        downloadBtn.disabled = true;
        statusDiv.textContent = '';
        return;
    }
    fetchQualities(url);
}));

downloadBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    const itag = qualitySelect.value;
    
    if (!url || !itag) {
        statusDiv.textContent = 'Please enter URL and select quality';
        statusDiv.style.color = '#ff6b6b';
        return;
    }

    statusDiv.textContent = 'Preparing download...';
    statusDiv.style.color = '#3D52A0';
    downloadBtn.disabled = true;
    
    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url, itag})
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || 'Download failed');
        }

        const blob = await res.blob();
        const filename = res.headers.get('content-disposition')?.split('filename=')[1] || 'youtube_video.mp4';
        
        // Create download link
        const a = document.createElement('a');
        const urlObject = URL.createObjectURL(blob);
        a.href = urlObject;
        a.download = filename.replace(/"/g, '');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(urlObject);
        
        statusDiv.textContent = 'Download started!';
        statusDiv.style.color = '#4BB543';
        
    } catch(err) {
        statusDiv.textContent = err.message;
        statusDiv.style.color = '#ff6b6b';
    } finally {
        downloadBtn.disabled = false;
    }
});
