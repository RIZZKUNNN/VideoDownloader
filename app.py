from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

# --- TAHAP 1: AMBIL INFO VIDEO (JUDUL, THUMBNAIL, PLATFORM) ---
@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'status': 'error', 'message': 'URL kosong'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ambil data tanpa download dulu
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Video')
            thumbnail = info.get('thumbnail', '')
            uploader = info.get('uploader', '')
            
            # Deteksi apakah ini YouTube
            # yt-dlp biasanya mengisi 'extractor' dengan 'youtube', 'youtube:tab', dll.
            extractor = info.get('extractor', '').lower()
            is_youtube = 'youtube' in extractor

            return jsonify({
                'status': 'success',
                'title': title,
                'thumbnail': thumbnail,
                'uploader': uploader,
                'is_youtube': is_youtube
            })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# --- TAHAP 2: PROSES DOWNLOAD SESUAI RESOLUSI ---
@app.route('/download-video', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality') # 'best', '1080', '720', '480'

    if not url:
        return jsonify({'error': 'URL kosong'}), 400

    filename = f"video_{int(time.time())}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    # Logika Format yt-dlp
    if quality == '1080':
        # Download Video Max 1080p + Audio Terbaik -> Digabung jadi MP4
        format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
    elif quality == '720':
        format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
    elif quality == '480':
        format_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
    else:
        # Default / TikTok (Best Quality)
        format_str = 'best'

    ydl_opts = {
        'format': format_str,
        'outtmpl': filepath,
        'merge_output_format': 'mp4', # Wajib untuk YouTube agar Video+Audio nyatu
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            return jsonify({
                'status': 'success',
                'download_url': f"/download_file/{filename}"
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- TAHAP 3: AUDIO ONLY (MP3) ---
@app.route('/download-audio', methods=['POST'])
def download_audio():
    data = request.json
    url = data.get('url')
    
    filename_base = f"audio_{int(time.time())}"
    filepath_base = os.path.join(DOWNLOAD_FOLDER, filename_base)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filepath_base,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            final_filename = filename_base + ".mp3"
            return jsonify({'status': 'success', 'download_url': f"/download_file/{final_filename}"})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ROUTE PENGIRIMAN FILE
@app.route('/download_file/<name>')
def download_file(name):
    try:
        return send_file(os.path.join(DOWNLOAD_FOLDER, name), as_attachment=True)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
