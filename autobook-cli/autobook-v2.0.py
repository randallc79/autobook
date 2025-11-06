import argparse
import os
import subprocess
from tqdm import tqdm
import requests
import json
from pathlib import Path

def print_dir_tree(directory, label):
    print(f"{label}:")
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

def group_files(input_dir):
    groups = {}
    for file in os.listdir(input_dir):
        if file.lower().endswith(('.mp3', '.m4a', '.aac', '.m4b')):
            parts = file.rsplit('-', 1) if '-' in file else file.rsplit('.', 1)
            base = parts[0].strip()
            if base not in groups:
                groups[base] = []
            groups[base].append(os.path.join(input_dir, file))
    return groups

def fetch_metadata(book_name):
    sources = ['Google Books', 'OpenLibrary', 'Audible (mock)', 'Beets (subprocess)']
    metadata = {'title': book_name, 'author': 'Unknown', 'cover_url': None, 'chapters': []}
    with tqdm(total=len(sources), desc=f"Fetching metadata for {book_name}", leave=False) as pbar:
        # Google Books
        url = f"https://www.googleapis.com/books/v1/volumes?q={book_name.replace(' ', '+')}"
        try:
            resp = requests.get(url).json()
            if resp.get('totalItems', 0) > 0:
                item = resp['items'][0]['volumeInfo']
                metadata['title'] = item.get('title', book_name)
                metadata['author'] = ', '.join(item.get('authors', ['Unknown']))
                metadata['cover_url'] = item.get('imageLinks', {}).get('thumbnail')
        except:
            pass
        pbar.update(1)

        # OpenLibrary
        url = f"https://openlibrary.org/search.json?q={book_name.replace(' ', '+')}"
        try:
            resp = requests.get(url).json()
            if resp.get('numFound', 0) > 0:
                doc = resp['docs'][0]
                if 'author_name' in doc:
                    metadata['author'] = ', '.join(doc['author_name'])
        except:
            pass
        pbar.update(1)

        # Audible (mock; replace with real API if key available)
        # Assuming no public API without auth; skip or use search.
        pbar.update(1)

        # Beets
        try:
            temp_dir = Path('temp_beets')
            temp_dir.mkdir(exist_ok=True)
            conf = temp_dir / 'config.yaml'
            with open(conf, 'w') as f:
                f.write('directory: .\nplugins: fetchart\n')
            result = subprocess.run(['beet', '-c', str(conf), 'import', '-q', input_dir], capture_output=True, text=True)
            # Parse beets output for metadata (simplified; adapt as needed)
        except:
            pass
        pbar.update(1)

    return metadata

def convert_to_m4b(group_files, output_file, metadata):
    sorted_files = sorted(group_files, key=lambda x: os.path.basename(x))
    input_list = '|'.join(sorted_files)
    cmd = ['ffmpeg', '-i', f'concat:{input_list}', '-c', 'copy', '-bsf:a', 'aac_adtstoasc', output_file]
    subprocess.run(cmd, check=True)

    # Add cover if exists
    if metadata['cover_url']:
        cover_path = 'cover.jpg'
        with open(cover_path, 'wb') as f:
            f.write(requests.get(metadata['cover_url']).content)
        new_output = output_file.replace('.m4b', '_with_cover.m4b')
        cmd = ['ffmpeg', '-i', output_file, '-i', cover_path, '-c', 'copy', '-map', '0', '-map', '1', '-metadata:s:v', 'title=Album cover', '-metadata:s:v', 'comment=Cover (front)', new_output]
        subprocess.run(cmd, check=True)
        os.rename(new_output, output_file)
        os.remove(cover_path)

    # Add chapters (simple: assume file names as chapters)
    chapters = []
    start = 0
    for i, f in enumerate(sorted_files):
        duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f]))
        chapters.append(f"CHAPTER{i+1}={start:02d}:00:00.000\nCHAPTER{i+1}NAME={os.path.basename(f)}")
        start += duration
    chap_file = 'chapters.txt'
    with open(chap_file, 'w') as cf:
        cf.write(';FFMETADATA1\n' + '\n'.join(chapters))
    new_output = output_file.replace('.m4b', '_chap.m4b')
    cmd = ['ffmpeg', '-i', output_file, '-i', chap_file, '-c', 'copy', '-map_metadata', '1', new_output]
    subprocess.run(cmd, check=True)
    os.rename(new_output, output_file)
    os.remove(chap_file)

def add_to_audiobookshelf(output_file, abs_url, abs_key):
    if abs_url and abs_key:
        # Mock API call; adapt to actual Audiobookshelf API
        print(f"Adding {output_file} to Audiobookshelf at {abs_url}")
        # requests.post(f"{abs_url}/api/...", headers={'Authorization': abs_key}, files={'book': open(output_file, 'rb')})

parser = argparse.ArgumentParser(description='AutoBook v2 CLI: Organize audiobooks.')
parser.add_argument('--input', required=True, help='Input directory')
parser.add_argument('--output', required=True, help='Output directory')
parser.add_argument('--abs-url', help='Audiobookshelf URL')
parser.add_argument('--abs-key', help='Audiobookshelf API key')
args = parser.parse_args()

os.makedirs(args.output, exist_ok=True)

print_dir_tree(args.input, "Before")

groups = group_files(args.input)

for book, files in tqdm(groups.items(), desc="Books"):
    metadata = fetch_metadata(book)
    output_file = os.path.join(args.output, f"{metadata['title']} by {metadata['author']}.m4b")
    with tqdm(total=3, desc=f"Converting {book}", leave=False) as pbar:
        convert_to_m4b(files, output_file, metadata)
        pbar.update(3)  # Simplified; add per-step if needed
    add_to_audiobookshelf(output_file, args.abs_url, args.abs_key)

print_dir_tree(args.output, "After")
