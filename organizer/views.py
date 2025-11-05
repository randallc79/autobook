from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import InputForm
from .models import Job, Log
from autobook.tasks import process_job
from organizer.utils import handle_uploaded_file  # Add this function

def index(request):
    if request.method == 'POST':
        form = InputForm(request.POST, request.FILES)
        if form.is_valid():
            input_path = form.cleaned_data['input_path']
            if 'upload' in request.FILES:
                input_path = handle_uploaded_file(request.FILES['upload'])  # Extract to temp dir
            job = Job.objects.create(input_path=input_path, output_path=form.cleaned_data['output_path'])
            process_job.delay(job.id, job.input_path, job.output_path)
            return redirect('results', job_id=job.id)
    else:
        form = InputForm()
    return render(request, 'organizer/index.html', {'form': form})

def results(request, job_id):
    job = Job.objects.get(id=job_id)
    return render(request, 'organizer/results.html', {'job': job})

def logs(request, job_id):
    logs = Log.objects.filter(job_id=job_id).values('message', 'timestamp')
    return JsonResponse(list(logs), safe=False)
