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

def find_asin(folder_name):
    try:
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
    for root, dirs, files in os.walk(root_path):
        if 'processed_archive' in root:
            continue
        mp3_count = sum(1 for f in files if f.lower().endswith('.mp3'))
        if mp3_count > 1:
            candidates.append(root)
    logging.info(f"Found {len(candidates)} folders: {candidates}")
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
    parts = folder_name.split(' - ')
    author = parts[0].strip() if len(parts) > 1 else 'Unknown'
    title = ' - '.join(parts[1:]).strip() if len(parts) > 1 else folder_name
    pre_process_chapters(folder)
    asin = find_asin(folder_name)
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
        archive_folder = os.path.join(archive_path, folder_name)
        shutil.move(folder, archive_folder)
    else:
        logging.warning(f"Failed: {folder_name}")

print_dir_tree(output_path, "After")
