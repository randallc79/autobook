import os
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from mutagen.mp4 import MP4
from mutagen.easyid3 import EasyID3
import shutil
import logging
import beets.library  # For beets integration

logging.basicConfig(level=logging.INFO)

def find_asin(title, author):
    # Scrape Audible like previous
    try:
        query = quote_plus(f"{title} {author} audiobook")
        url = f"https://www.audible.com/search?keywords={query}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        first_link = soup.find('a', class_='bc-link', href=lambda h: h and '/pd/' in h)
        if first_link:
            return first_link['href'].split('/')[-1].split('?')[0]
    except:
        return None

def fetch_metadata_beets(path):
    # Integrate beets-audible
    lib = beets.library.Library(':memory:')  # Temp lib
    item = lib.add(path)  # Simplified; in practice, use import
    # Run audible plugin logic (fetch from Audnex/Audible)
    # Return dict with title, author, series, etc.
    return {'title': item['title'], 'author': item['artist'], 'series': item.get('series', '')}

def process_audiobook_folder(folder, output_path):
    folder_name = os.path.basename(folder)
    parts = folder_name.split(' - ')
    author = parts[0].strip() if len(parts) > 1 else 'Unknown'
    title = ' - '.join(parts[1:]).strip() if len(parts) > 1 else folder_name
    
    # Pre-process chapters (from previous)
    mp3_files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp3')])
    for i, file in enumerate(mp3_files, start=1):
        old_path = os.path.join(folder, file)
        new_path = os.path.join(folder, f"Chapter {i:02d}.mp3")
        os.rename(old_path, new_path)
        audio = EasyID3(new_path)
        audio['title'] = f"Chapter {i:02d}"
        audio.save()
    
    # Metadata multi-source
    metadata = fetch_metadata_beets(folder)  # Try beets first
    if not metadata.get('title'):
        asin = find_asin(title, author)
        if asin:
            # Use m4b-merge with ASIN
            subprocess.run(['m4b-merge', '-i', folder, '-o', output_path], input=asin + '\n')
            return True
        else:
            # Fallback OpenLibrary like m4binder
            output_file = os.path.join(output_path, f"{author} - {title}.m4b")
            subprocess.run(['python', '/opt/m4binder/m4binder.py',
                            '--mode', 'single', '--input-folder', folder, '--output-file', output_file,
                            '--metadata-source', 'openlibrary', '--title', title, '--author', author])
            return True
    
    # Embed cover if missing (from OpenLibrary or Audible)
    cover_url = # Fetch like previous
    if cover_url:
        # Embed
    
    # Organize like jeeftor: author/series/title
    final_dir = os.path.join(output_path, author, metadata.get('series', ''), title)
    os.makedirs(final_dir, exist_ok=True)
    shutil.move(output_file, final_dir)  # Or all files
    
    # Archive original
    archive_path = os.path.join(output_path, 'archive', folder_name)
    shutil.move(folder, archive_path)
    
    return True
