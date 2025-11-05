from django.shortcuts import render, redirect
from .forms import InputForm
from .models import Job
from autobook.tasks import process_job

def index(request):
    if request.method == 'POST':
        form = InputForm(request.POST, request.FILES)
        if form.is_valid():
            job = Job.objects.create(
                input_path=form.cleaned_data['input_path'],  # Or handle upload
                output_path=form.cleaned_data['output_path']
            )
            process_job.delay(job.id, job.input_path, job.output_path)
            return redirect('results', job_id=job.id)
    else:
        form = InputForm()
    return render(request, 'organizer/index.html', {'form': form})

def results(request, job_id):
    job = Job.objects.get(id=job_id)
    # Poll status or use channels for real-time
    return render(request, 'organizer/results.html', {'job': job})
