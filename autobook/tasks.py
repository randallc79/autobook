from celery import shared_task
from organizer.utils import process_audiobook_folder

@shared_task
def process_job(job_id, input_path, output_path):
    # Logic to process all folders in input_path
    from organizer.models import Job
    job = Job.objects.get(id=job_id)
    job.status = 'processing'
    job.save()
    
    folders = []  # Scan input_path for audiobook folders (implement scan logic)
    results = []
    for folder in folders:
        success = process_audiobook_folder(folder, output_path)
        results.append((folder, success))
    
    job.status = 'completed' if all(success for _, success in results) else 'failed'
    job.save()
    return results
