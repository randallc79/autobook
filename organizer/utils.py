import os
import subprocess
import requests
import re
import zipfile
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from mutagen.mp4 import MP4
from mutagen.easyid3 import EasyID3
import shutil
import logging
import beets.library
import beetsplug.audible as audible  # Assume configured

logging.basicConfig(level=logging.INFO)

def handle_uploaded_file(f):
    temp_dir = '/tmp/upload'
    os.makedirs(temp_dir, exist_ok=True)
    path = os.path.join(temp_dir, f.name)
    with open(path, 'wb+') as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        os.remove(path)
    return temp_dir

def scan_audiobook_folders(input_path):
    candidates = []
    all_audio = [os.path.join(root, f) for root, _, files in os.walk(input_path) for f in files if f.lower().endswith(('.mp3', '.m4a', '.m4b'))]
    # Group flat files by common metadata or name prefix
    groups = {}  # Key: (author, title), Value: list of files
    for file in all_audio:
        try:
            audio = EasyID3(file) if file.endswith('.mp3') else MP4(file)
            author = audio.get('artist', 'Unknown')[0]
            title = audio.get('album', os.path.basename(file))[0]
            key = (author, title)
            groups.setdefault(key, []).append(file)
        except:
            # Fallback to filename grouping
            prefix = re.match(r'^(.*? - .*?)\d+', os.path.basename(file))
            key = prefix.group(1) if prefix else os.path.basename(file)
            groups.setdefault(key, []).append(file)
    
    for key, files in groups.items():
        if len(files) > 1:  # Likely a book
            group_dir = os.path.join(input_path, str(hash(key)))  # Temp dir
            os.makedirs(group_dir, exist_ok=True)
            for f in files:
                shutil.move(f, group_dir)
            candidates.append(group_dir)
        else:
            # Single file: treat as is
            candidates.append(os.path.dirname(files[0]))
    
    # Clean junk
    for root, dirs, files in os.walk(input_path):
        for f in files:
            if not f.lower().endswith(('.mp3', '.m4a', '.m4b')):
                os.remove(os.path.join(root, f))
    
    return candidates

def fetch_metadata_google_books(title, author):
    try:
        query = quote_plus(f"{title} {author}")
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
        response = requests.get(url)
        data = response.json()
        if data['totalItems'] > 0:
            item = data['items'][0]['volumeInfo']
            return {
                'title': item.get('title'),
                'author': item.get('authors', ['Unknown'])[0],
                'series': item.get('seriesInfo', {}).get('bookDisplayNumber', ''),  # Basic series
                'cover': item.get('imageLinks', {}).get('thumbnail')
            }
    except:
        return {}

def process_audiobook_folder(folder, output_path):
    folder_name = os.path.basename(folder)
    parts = folder_name.split(' - ')
    author = parts[0].strip() if len(parts) > 1 else 'Unknown'
    title = ' - '.join(parts[1:]).strip() if len(parts) > 1 else folder_name
    
    # Enhanced chapter detection with regex
    mp3_files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp3')])
    for i, file in enumerate(mp3_files, start=1):
        old_path = os.path.join(folder, file)
        match = re.match(r'(\d+) - (.*)\.mp3', file, re.I)
        chapter_name = f"Chapter {match.group(1) if match else i:02d} - {match.group(2) if match else 'Unknown'}.mp3"
        new_path = os.path.join(folder, chapter_name)
        os.rename(old_path, new_path)
        audio = EasyID3(new_path)
        audio['title'] = chapter_name.replace('.mp3', '')
        audio.save()
    
    # Metadata: Priority - Embedded > beets-audible > Audible scrape > Google Books > OpenLibrary
    metadata = {}
    try:
        lib = beets.library.Library(':memory:')
        item = lib.add(folder)  # Simplified
        audible.fetch_db(item)  # From beets-audible
        metadata = {'title': item.title, 'author': item.artist, 'series': item.series, 'asin': item.asin}
    except:
        pass
    
    if not metadata.get('title'):
        metadata = fetch_metadata_google_books(title, author)
    
    if not metadata.get('title'):
        asin = find_asin(title, author)  # From previous
        if asin:
            metadata['asin'] = asin
    
    success = False
    output_file = os.path.join(output_path, f"{metadata.get('author', author)} - {metadata.get('title', title)}.m4b")
    
    if metadata.get('asin'):
        proc = subprocess.Popen(['m4b-merge', '-i', folder, '-o', os.path.dirname(output_file)], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=metadata['asin'] + '\n')
        success = proc.returncode == 0
    
    if not success:
        result = subprocess.run(['python', '/opt/m4binder/m4binder.py',
                                 '--mode', 'single', '--input-folder', folder, '--output-file', output_file,
                                 '--metadata-source', 'openlibrary', '--title', metadata.get('title', title), '--author', metadata.get('author', author)])
        success = result.returncode == 0
    
    if success:
        # Embed cover from metadata or fallback
        cover_url = metadata.get('cover') or fetch_cover_url(metadata.get('title', title), metadata.get('author', author))
        if cover_url:
            embed_cover(output_file, cover_url)
        
        # Organize with series
        series = metadata.get('series', '')
        final_dir = os.path.join(output_path, metadata.get('author', author), series, metadata.get('title', title))
        os.makedirs(final_dir, exist_ok=True)
        shutil.move(output_file, final_dir)
        
        # Optional: Trigger Audiobookshelf scan (if API configured in env)
        if os.environ.get('ABS_URL') and os.environ.get('ABS_API_KEY'):
            requests.post(f"{os.environ['ABS_URL']}/api/libraries/scan", headers={'Authorization': os.environ['ABS_API_KEY']})
    
    # Archive with undo log
    archive_path = os.path.join(output_path, 'archive', folder_name)
    shutil.move(folder, archive_path)
    with open(os.path.join(archive_path, 'undo.log'), 'w') as log:
        log.write(f"Original files moved from {folder}\nOutput: {final_dir}")
    
    return success
