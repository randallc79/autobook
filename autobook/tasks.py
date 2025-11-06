import os
import logging

from celery import shared_task

from organizer.utils import scan_audiobook_folders, process_audiobook_folder
from organizer.models import Job, Log

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_job(self, job_id, input_path, output_path):
    """
    Background job that scans the input path, processes each audiobook folder,
    and records basic logs in the database.

    WebSocket / Channels integration is intentionally disabled for now to
    avoid import/version issues during migrations.
    """

    job = Job.objects.get(id=job_id)
    job.status = "processing"
    job.save()

    try:
        folders = scan_audiobook_folders(input_path)
        total = len(folders) or 1

        for i, folder in enumerate(folders):
            success = process_audiobook_folder(folder, output_path)

            msg = f"{os.path.basename(folder)}: {'Success' if success else 'Failed'}"
            logger.info("[job %s] %s", job_id, msg)

            Log.objects.create(
                job=job,
                message=msg,
            )

        job.status = "completed"
        job.save()
        return job.status

    except Exception as exc:
        logger.exception("Job %s failed: %s", job_id, exc)
        job.status = "failed"
        job.save()
        Log.objects.create(job=job, message=str(exc))
        raise self.retry(exc=exc)
