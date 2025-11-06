import argparse
import os
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import logging
from tqdm import tqdm
from mutagen.mp4 import MP4
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('audiobook_organizer.log'), logging.StreamHandler()]
)

def print_dir_tree(directory, label):
    logging.info(f"{label}:")
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 4 * level
        logging.info(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logging.info(f"{subindent}{f}")

def count_audio_files(folder):
    mp3_count = len([f for f in os.listdir(folder) if f.lower().endswith('.mp3')])
    m4b_count = len([f for f in os.listdir(folder) if f.lower().endswith('.m4b')])
    return mp3_count, m4b_count

def extract_meta_from_files(folder):
    meta = {'title': None, 'author': None}
    files = os.listdir(folder)
    for file in files:
        file_path = os.path.join(folder, file)
        try:
            if file.lower().endswith('.mp3'):
                audio = EasyID3(file_path)
                if 'title' in audio and not meta['title']:
                    meta['title'] = audio['title'][0]
                if 'artist' in audio and not meta['author']:
                    meta['author'] = audio['artist'][0]
            elif file.lower().endswith('.m4b'):
                audio = MP4(file_path)
                if '\xa9nam' in audio and not meta['title']:
                    meta['title'] = audio['\xa9nam'][0]
                if '\xa9aut' in audio and not meta['author']:
                    meta['author'] = audio['\xa9aut'][0]
            if meta['title'] and meta['author']:
                break
        except (ID3NoHeaderError, Exception):
            pass
    # Fallback to file path or name if meta missing
    if not meta['title'] or not meta['author']:
        rel_path = folder.replace('/opt/sort/', '')
        parts = rel_path.split('/')
        if len(parts) >= 2:
            meta['author'] = meta['author'] or parts[0]
            meta['title'] = meta['title'] or ' '.join(parts[1:])
        elif files:
            first_file = os.path.join(folder, files[0])
            base_name = os.path.basename(first_file).rsplit('.', 1)[0]
            base_parts = base_name.split(' - ')
            if len(base_parts) >= 2:
                meta['author'] = meta['author'] or base_parts[0].strip()
                meta['title'] = meta['title'] or ' - '.join(base_parts[1:]).strip()
    return meta

def find_asin(folder_name, title=None, author=None):
    try:
        if title and (author and author != 'Unknown'):
            query = quote_plus(f"{title} {author} audiobook")
        elif title:
            query = quote_plus(f"{title} audiobook")
        else:
            parts = folder_name.split(' - ')
            if len(parts) < 2: return None
            author = parts[0].strip()
            title = ' - '.join(parts[1:]).strip()
            query = quote_plus(f"{title} {author} audiobook")
        url = f"https://www.audible.com/search?keywords={query}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        first_link = soup.find('a', class_='bc-link', href=lambda h: h and '/pd/' in h)
        if first_link:
            return first_link['href'].split('/')[-1].split('?')[0]
        return None
    except: return None

def fetch_cover_url(title, author):
    try:
        query = quote_plus(f"{title} {author}")
        url = f"https://openlibrary.org/search.json?q={query}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        if data['num_found'] > 0:
            olid = data['docs'][0].get('cover_edition_key')
            if olid: return f"https://covers.openlibrary.org/b/olid/{olid}-L.jpg"
        return None
    except: return None

def embed_cover(m4b_file, cover_url):
    try:
        cover_data = requests.get(cover_url).content
        audio = MP4(m4b_file)
        audio['covr'] = [cover_data]
        audio.save()
    except: pass

def has_cover(m4b_file):
    try:
        audio = MP4(m4b_file)
        return 'covr' in audio and len(audio['covr']) > 0
    except: return False

def pre_process_chapters(folder):
    try:
        mp3_files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp3')])
        for i, file in enumerate(mp3_files, start=1):
            old_path = os.path.join(folder, file)
            chapter_name = f"Chapter {i:02d}.mp3"
            new_path = os.path.join(folder, chapter_name)
            os.rename(old_path, new_path)
            try:
                audio = EasyID3(new_path)
                audio['title'] = f"Chapter {i:02d}"
                audio.save()
            except: pass
    except: pass

def find_audiobook_folders(root_path):
    candidates = []
    for item in sorted(os.listdir(root_path)):
        full_path = os.path.join(root_path, item)
        if os.path.isdir(full_path):
            first_root = full_path
            break
    if first_root:
        logging.info(f"Processing only first root folder: {first_root}")
        for root, dirs, files in os.walk(first_root):
            mp3_count = sum(1 for f in files if f.lower().endswith('.mp3'))
            if mp3_count > 1:
                candidates.append(root)
    logging.info(f"Found subfolders with MP3s: {candidates}")
    return candidates

parser = argparse.ArgumentParser(description='Audiobook Organizer CLI')
parser.add_argument('--m4binder_path', required=True, help='Path to m4binder.py')
args = parser.parse_args()

root_path = '/opt/sort'
output_path = '/opt/done'
m4binder_path = args.m4binder_path
archive_path = os.path.join(root_path, 'processed_archive')
os.makedirs(archive_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

print_dir_tree(root_path, "Before")

folders = find_audiobook_folders(root_path)

for folder in tqdm(folders, desc="Processing folders"):
    folder_name = os.path.basename(folder)
    logging.info(f"Processing folder: {folder}")
    mp3_count, m4b_count = count_audio_files(folder)
    logging.info(f"Original counts: MP3={mp3_count}, M4B={m4b_count}")
    if mp3_count <= 1:
        logging.info("Skipping: Insufficient MP3 files")
        continue
    meta = extract_meta_from_files(folder)
    logging.info(f"Extracted meta: title={meta['title']}, author={meta['author']}")
    parts = folder_name.split(' - ')
    author = meta['author'] or (parts[0].strip() if len(parts) > 1 else 'Unknown')
    title = meta['title'] or (' - '.join(parts[1:]).strip() if len(parts) > 1 else folder_name)
    logging.info(f"Using title={title}, author={author}")
    pre_process_chapters(folder)
    asin = find_asin(folder_name, title, author)
    logging.info(f"Found ASIN: {asin}")
    success = False
    output_file = os.path.join(output_path, f"{author} - {title}.m4b")
    if asin:
        try:
            proc = subprocess.Popen(['m4b-merge', '-i', folder, '-o', output_path], stdin=subprocess.PIPE, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(input=asin + '\n')
            if proc.returncode == 0:
                success = True
            else:
                logging.error(f"m4b-merge failed for {folder_name}: {stderr}")
        except Exception as e:
            logging.error(f"m4b-merge exception for {folder_name}: {str(e)}")
    if not success:
        try:
            result = subprocess.run(['python', m4binder_path, '--mode', 'single', '--input-folder', folder,
                                    '--output-file', output_file, '--metadata-source', 'openlibrary',
                                    '--title', title, '--author', author], capture_output=True, text=True, check=True)
            success = True
        except subprocess.CalledProcessError as e:
            logging.error(f"m4binder failed for {folder_name}: {e.stderr}")
        except Exception as e:
            logging.error(f"m4binder exception for {folder_name}: {str(e)}")
    if success:
        if not has_cover(output_file):
            cover_url = fetch_cover_url(title, author)
            if cover_url: embed_cover(output_file, cover_url)
        logging.info(f"Created M4B: {output_file}")
        archive_folder = os.path.join(archive_path, folder_name)
        shutil.move(folder, archive_folder)
    else:
        logging.warning(f"Failed: {folder_name}")

print_dir_tree(output_path, "After")
