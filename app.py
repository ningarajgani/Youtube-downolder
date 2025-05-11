from flask import Flask, request, jsonify, send_file, render_template, after_this_request
import yt_dlp
import os
import re
import uuid
import logging
from io import BytesIO

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube regex pattern
YOUTUBE_URL_REGEX = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+')

# Custom headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_qualities', methods=['POST'])
def get_qualities():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url or not YOUTUBE_URL_REGEX.match(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'headers': HEADERS,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({'error': 'Could not extract video info'}), 404

            formats = info.get('formats', [])
            qualities = []
            seen = set()

            for f in formats:
                itag = f.get('format_id')
                if not itag or itag in seen:
                    continue
                
                if f.get('vcodec') != 'none':  # Only video formats
                    qualities.append({
                        'itag': itag,
                        'quality_label': f.get('format_note') or f'{f.get("height", "?")}p',
                        'ext': f.get('ext', 'mp4'),
                        'has_audio': f.get('acodec') != 'none',
                        'has_video': f.get('vcodec') != 'none'
                    })
                    seen.add(itag)

            if not qualities:
                return jsonify({'error': 'No downloadable formats found'}), 404

            return jsonify({'qualities': qualities})

    except Exception as e:
        logger.error(f"Error in get_qualities: {str(e)}")
        return jsonify({'error': 'Failed to fetch video info. Try another video.'}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        itag = data.get('itag', '').strip()

        if not url or not YOUTUBE_URL_REGEX.match(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        if not itag:
            return jsonify({'error': 'Quality (itag) must be selected'}), 400

        # Generate unique filename
        filename = f"yt_download_{uuid.uuid4().hex}.mp4"
        
        ydl_opts = {
            'format': itag,
            'outtmpl': filename,
            'quiet': True,
            'no_warnings': True,
            'headers': HEADERS,
            'noplaylist': True,
            'merge_output_format': 'mp4',
        }

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                logger.error(f"Error cleaning up file: {str(e)}")
            return response

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({'error': 'Could not extract video info'}), 404
            
            ydl.download([url])
            
            if not os.path.exists(filename):
                return jsonify({'error': 'Download failed - file not created'}), 500

            return send_file(
                filename,
                as_attachment=True,
                download_name=f'youtube_video_{itag}.mp4',
                mimetype='video/mp4'
            )

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
