# app.py

from flask import Flask, request, jsonify, send_file, render_template, abort
import yt_dlp
import os
import re
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

YOUTUBE_URL_REGEX = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_qualities', methods=['POST'])
def get_qualities():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url or not YOUTUBE_URL_REGEX.match(url):
        return jsonify({'error': 'Invalid YouTube URL.'}), 400
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            qualities = []
            seen_itags = set()
            for f in formats:
                itag = f.get('format_id')
                if itag in seen_itags:
                    continue
                ext = f.get('ext')
                if ext not in ['mp4', 'webm']:
                    continue
                qualities.append({
                    'itag': itag,
                    'quality_label': f.get('format_note') or (str(f['height']) + "p" if f.get('height') else "unknown"),
                    'extension': ext,
                    'has_audio': f.get('acodec') != 'none',
                    'has_video': f.get('vcodec') != 'none'
                })
                seen_itags.add(itag)
            if not qualities:
                return jsonify({'error': 'No downloadable formats found.'}), 404
            return jsonify({'qualities': qualities})
    except Exception as e:
        return jsonify({'error': 'Could not extract info from URL: ' + str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url', '').strip()
    itag = data.get('itag', '').strip()
    if not url or not YOUTUBE_URL_REGEX.match(url):
        return jsonify({'error': 'Invalid YouTube URL.'}), 400
    if not itag:
        return jsonify({'error': 'Quality (itag) must be selected.'}), 400

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    ydl_opts = {
        'quiet': True,
        'outtmpl': filepath,
        'format': itag,
        'noplaylist': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(
            filepath,
            as_attachment=True,
            download_name='youtube_video.mp4',
            mimetype='video/mp4',
            conditional=True
        )
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': 'Download failed: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
