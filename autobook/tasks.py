from celery import shared_task
from organizer.utils import scan_audiobook_folders, process_audiobook_folder
from organizer.models import Job, Log
from channels.layers import get_channel_layer
from asgi_ref import application  # For WS

@shared_task(bind=True, max_retries=3)
def process_job(self, job_id, input_path, output_path):
    channel_layer = get_channel_layer()
    job = Job.objects.get(id=job_id)
    job.status = 'processing'
    job.save()
    
    try:
        folders = scan_audiobook_folders(input_path)  # Enhanced scan
        total = len(folders)
        for i, folder in enumerate(folders):
            success = process_audiobook_folder(folder, output_path)
            Log.objects.create(job=job, message=f"{os.path.basename(folder)}: {'Success' if success else 'Failed'}")
            async_to_sync(channel_layer.group_send)(f"job_{job_id}", {
                "type": "job.update",
                "progress": (i + 1) / total * 100,
                "message": Log.objects.latest('id').message
            })
        job.status = 'completed'
    except Exception as exc:
        job.status = 'failed'
        Log.objects.create(job=job, message=str(exc))
        self.retry(exc=exc)
    job.save()
    return job.status
