import datetime
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from Notes.utils import render_to_pdf
from .models import Activity, Notebook, Page, StickyNotes, Remainder, SharedNotebook, SubPage
from .forms import NotebookForm, PageForm, StickyNotesForm,RemainderForm,SubPageForm
from Users.models import Profile
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.serializers import serialize, deserialize
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from .models import Notebook, Page, SubPage
import json
import os

# Uncomment when done with lock
# from django.views.decorators.cache import cache_page
# from django.core.cache import cache
# # Create your views here.
# @cache_page(60 * 2)  # Cache the page for 2 minutes (adjust as needed)
# def index(request):
#     if request.user.is_authenticated:
#         logined_profile = Profile.objects.get(user=request.user)

#         # Cache invalidation for notebooks_list
#         notebooks_cache_key = f'notebooks_list_{request.user.id}'
#         notebooks_list = cache.get(notebooks_cache_key)
#         if not notebooks_list:
#             notebooks_list = Notebook.objects.filter(author=logined_profile).order_by('priority')
#             cache.set(notebooks_cache_key, notebooks_list, 60 * 2)  # Cache for 1 minutes
#             print('Notebooks list cached successfully.')

#         # Cache invalidation for pages
#         pages_cache_key = f'pages_{request.user.id}'
#         pages = cache.get(pages_cache_key)
#         if not pages:
#             pages = Page.objects.filter(notebook__in=notebooks_list)
#             cache.set(pages_cache_key, pages, 60 * 2)  # Cache for 1 minutes
#             print('Pages cached successfully.')

#         # Repeat this caching pattern for other queries as needed
#         subpages = SubPage.objects.filter(page__in=pages)
#         activities_list = Activity.objects.filter(author=logined_profile).order_by('-created_at')
#         sticky_notes = StickyNotes.objects.filter(author=logined_profile)
#         remainders = Remainder.objects.filter(author=logined_profile).order_by('alert_time')
#         favouritesNotebooks = notebooks_list.filter(is_favourite=True)
#         favouritesPages = Page.objects.filter(is_favourite=True, notebook__in=favouritesNotebooks)
#         favouritesRemainders = remainders.filter(is_favourite=True)
#         sharedNotebooks = SharedNotebook.objects.filter(owner=logined_profile).order_by('-shared_at')

#         # Set up pagination for activities
#         paginator_activities = Paginator(activities_list, 5)  # Show 5 activities per page
#         page_number_activities = request.GET.get('page')
#         activities = paginator_activities.get_page(page_number_activities)

#         # Set up pagination for notebooks
#         paginator_notebooks = Paginator(notebooks_list, 5)  # Show 5 notebooks per page
#         page_number_notebooks = request.GET.get('notebook_page')
#         notebooks = paginator_notebooks.get_page(page_number_notebooks)
#         check_remainders()
#         check_activities()
#         mark_password_as_not_entered(notebooks_list)

#         context = {'notebooks': notebooks, 'pages': pages, 'logined_profile': logined_profile,
#                    'activities': activities, 'sticky_notes': sticky_notes, 'subpages': subpages,
#                    'remainders': remainders, 'favouritesNotebooks': favouritesNotebooks,
#                    'favouritesPages': favouritesPages, 'favouritesRemainders': favouritesRemainders,
#                    'sharedNotebooks': sharedNotebooks}

#         return render(request, "index.html", context)
#     else:
#         return redirect('login')
# Create your views here.
def index(request):
    if request.user.is_authenticated:
        start_time = datetime.datetime.now()

        logined_profile = Profile.objects.get(user=request.user)
        notebooks_list = Notebook.objects.filter(author=logined_profile).order_by('-is_accessed_recently')
        notebooks_list_priority = Notebook.objects.filter(author=logined_profile).order_by('priority')
        pages = Page.objects.filter(notebook__in=notebooks_list)
        subpages = SubPage.objects.filter(page__in=pages)
        activities_list = Activity.objects.filter(author=logined_profile).order_by('-created_at')
        sticky_notes = StickyNotes.objects.filter(author=logined_profile)
        remainders = Remainder.objects.filter(author=logined_profile).order_by('alert_time')
        favouritesNotebooks = notebooks_list.filter(is_favourite=True)
        favouritesPages = Page.objects.filter(is_favourite=True, notebook__in=favouritesNotebooks)
        favouritesRemainders = remainders.filter(is_favourite=True)
        sharedNotebooks = SharedNotebook.objects.filter(owner=logined_profile).order_by('-shared_at')
        
        # Set up pagination
        paginator = Paginator(activities_list, 5)  # Show 10 activities per page
        page_number = request.GET.get('page')
        activities = paginator.get_page(page_number)
        paginator_notebook = Paginator(notebooks_list, 5)  # Show 10 activities per page
        page_number = request.GET.get('notebook_page')
        notebooks = paginator_notebook.get_page(page_number)
        check_remainders()
        # check_activities()
        mark_password_as_not_entered(notebooks_list)
        mark_recently_accessed_as_false(pages,notebooks_list)

        end_time = datetime.datetime.now()

        print(f"Time taken: {end_time - start_time}")
        context = {'notebooks': notebooks,'notebooks_list_priority': notebooks_list_priority, 'pages': pages, 'logined_profile': logined_profile,
                   'activities': activities, 'sticky_notes': sticky_notes, 'subpages': subpages,
                   'remainders': remainders, 'favouritesNotebooks': favouritesNotebooks, 
                   'favouritesPages': favouritesPages, 'favouritesRemainders': favouritesRemainders,'sharedNotebooks': sharedNotebooks}
    else:
        context = {}
        redirect('login')
    return render(request, "index.html", context)
    
def mark_password_as_not_entered(notebook_list):
    for notebook in notebook_list:
        if notebook.is_password_entered == True:
            notebook.is_password_entered = False
            notebook.save()
        else:
            pass

def mark_recently_accessed_as_false(page_list,notebooks):
    recently_accessed_notebook = []
    for notebook in notebooks:
        if notebook.is_accessed_recently == True:
            recently_accessed_notebook.append(notebook)

    if len(recently_accessed_notebook) >= 3:
        for page in recently_accessed_notebook.page_set.all():
            if page.updated_at < timezone.now() + datetime.timedelta(hours=6, minutes=30):
                related_notebook = Notebook.objects.get(id=page.notebook_id)
                related_notebook.is_accessed_recently = False
                related_notebook.save()

def check_activities():
    for activity in Activity.objects.all():
        if activity.created_at < timezone.now() + datetime.timedelta(days=2):
            activity.delete()
        else:
            pass

def check_remainders():
    for remainder in Remainder.objects.all():
        if remainder.alert_time < timezone.now() + datetime.timedelta(hours=5, minutes=30):
            remainder.is_over = True
            remainder.delete()
        else:
            remainder.is_over = False
            remainder.save()

def update_notebook_modal(request, pk):
    notebook = Notebook.objects.get(id=pk)
    if request.method == 'POST':
        form = NotebookForm(request.POST, instance=notebook)
        if form.is_valid():
            priority = form.cleaned_data['priority']
            if priority < 1:
                form.add_error('priority', 'Priority cannot be less than 1')
                return render(request, 'update_notebook_modal.html', {'form': form, 'notebook': notebook})
            if priority > 5:
                form.add_error('priority', 'Priority cannot be greater than 5')
                return render(request, 'update_notebook_modal.html', {'form': form, 'notebook': notebook})
            form.save()
            Activity.objects.create(author=notebook.author, title='Updated Notebook', body=f'Updated notebook with title of: {notebook.title}')
            messages.success(request, 'Notebook updated successfully!')
            return redirect('home')  # Redirect to appropriate page
    else:
        form = NotebookForm(instance=notebook)
    return render(request, 'update_notebook_modal.html', {'form': form, 'notebook': notebook})

def update_page_modal(request, pk):
    page = Page.objects.get(id=pk)
    if request.method == 'POST':
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            Activity.objects.create(author=page.notebook.author, title='Updated Page', body=f'Updated page with title of: {page.title}')
            messages.success(request, 'Page updated successfully!')
            return redirect('home')  # Redirect to appropriate page
    else:
        form = PageForm(instance=page)
    return render(request, 'update_page_modal.html', {'form': form, 'page': page})

def update_sub_page_modal(request, pk):
    subpage = SubPage.objects.get(id=pk)
    if request.method == 'POST':
        form = SubPageForm(request.POST, instance=subpage)
        if form.is_valid():
            form.save()
            Activity.objects.create(author=subpage.notebook.author, title='Updated Page', body=f'Updated sub-page with title of: {subpage.title}')
            messages.success(request, 'Page updated successfully!')
            return redirect('home')  # Redirect to appropriate page
    else:
        form = SubPageForm(instance=subpage)
    return render(request, 'update_sub_page_modal.html', {'form': form, 'subpage': subpage})

def update_reminder(request, pk):
    reminder = Remainder.objects.get(id=pk)
    if request.method == 'POST':
        form = RemainderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            Activity.objects.create(author=reminder.notebook.author, title='Updated Reminder', body=f'Updated reminder with title of: {reminder.title}')
            messages.success(request, 'Reminder updated successfully!')
            return redirect('home')  # Redirect to appropriate page
    else:
        form = RemainderForm(instance=reminder)
    return render(request, 'update_reminder.html', {'form': form, 'reminder': reminder})

# def exportNotebookToJson(request, pk):
#     # Get the Notebook object or return 404 if not found
#     notebook = get_object_or_404(Notebook, id=pk)
    
#     # Collect pages related to the notebook
#     pages = Page.objects.filter(notebook=notebook)
    
#     # Collect subpages for each page
#     subpages = SubPage.objects.filter(page__in=pages)
    
#     # Serialize the notebook, pages, and subpages
#     notebook_data = serialize('json', [notebook], indent=4)
#     pages_data = serialize('json', pages, indent=4)
#     subpages_data = serialize('json', subpages, indent=4)
    
#     # Combine all serialized data into one dictionary
#     complete_data = {
#         'notebook': json.loads(notebook_data),
#         'pages': json.loads(pages_data),
#         'subpages': json.loads(subpages_data)
#     }
    
#     # Ensure the directory exists
#     json_directory = os.path.join(settings.BASE_DIR, 'JSONFiles')
#     os.makedirs(json_directory, exist_ok=True)
    
#     # Define file path
#     file_path = os.path.join(json_directory, f'{notebook.title.replace("/", "-")}.json')  # Avoiding directory traversal issues
    
#     # Write the JSON data to a file
#     with open(file_path, 'w') as file:
#         json.dump(complete_data, file, indent=4)
    
#     messages.success(request, 'Notebook exported successfully!')

#     # Redirect to home page
#     return redirect('home')

def exportNotebookToJson(request, pk):
    # Get the Notebook object or return 404 if not found
    notebook = get_object_or_404(Notebook, id=pk)
    
    # Collect pages related to the notebook
    pages = Page.objects.filter(notebook=notebook)
    
    # Collect subpages for each page
    subpages = SubPage.objects.filter(page__in=pages)
    
    # Serialize the notebook, pages, and subpages
    notebook_data = serialize('json', [notebook])
    pages_data = serialize('json', pages)
    subpages_data = serialize('json', subpages)
    
    # Combine all serialized data into one dictionary
    complete_data = {
        'notebook': json.loads(notebook_data),
        'pages': json.loads(pages_data),
        'subpages': json.loads(subpages_data)
    }
    
    # Convert the combined data to a JSON string
    json_data = json.dumps(complete_data, indent=4)
    
    # Create the HTTP response with the JSON string as an attachment
    response = HttpResponse(json_data, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{notebook.title.replace("/", "-")}.json"'  # Avoiding directory traversal issues
    
    messages.success(request, 'Notebook exported successfully!')

    return response


@login_required
def loadJsonToModels(request):
    if request.method == 'POST':
        # Assuming the JSON file is uploaded via a form
        json_file = request.FILES.get('json_file')
        
        if json_file:
            try:
                # Read the uploaded JSON file
                json_data = json.loads(json_file.read().decode('utf-8'))

                # Get the current logged-in user as the author
                author = Profile.objects.get(user=request.user)

                print('JSON data loaded successfully.')

                # Deserialize and save Notebook data
                notebook_data = json_data['notebook']
                for obj in notebook_data:
                    title = obj['fields']['title']
                    body = obj['fields']['body']
                    priority = obj['fields']['priority']
                    is_favourite = obj['fields']['is_favourite']
                    is_shared = obj['fields']['is_shared']
                    created_at = obj['fields']['created_at']
                    updated_at = obj['fields']['updated_at']
                    if not Notebook.objects.filter(title=title).exists():
                        notebook = Notebook.objects.create(
                            title=title,
                            body=body,
                            priority=priority,
                            is_favourite=is_favourite,
                            is_shared=is_shared,
                            created_at=created_at,
                            updated_at=updated_at,
                            author=author
                        )
                        print('Notebook saved:', title )
                        # print(notebook.pk)

                # Deserialize and save Page data
                pages_data = json_data['pages']
                for obj in pages_data:
                    title = obj['fields']['title']
                    body = obj['fields']['body']
                    # notebook_title = obj['fields']['notebook']
                    is_favourite = obj['fields']['is_favourite']
                    created_at = obj['fields']['created_at']
                    updated_at = obj['fields']['updated_at']
                    if Notebook.objects.filter(id=notebook.pk).exists():
                        notebook = Notebook.objects.get(id=notebook.pk)
                        page = Page.objects.create(
                            title=title,
                            body=body,
                            notebook=notebook,
                            is_favourite=is_favourite,
                            created_at=created_at,
                            updated_at=updated_at,
                            author=author
                        )
                        print('Page saved:', title)
                    else:
                        print('Notebook not found for page:', title)

                # Deserialize and save SubPage data
                subpages_data = json_data['subpages']
                for obj in subpages_data:
                    title = obj['fields']['title']
                    body = obj['fields']['body']
                    # page_title = obj['fields']['page']
                    created_at = obj['fields']['created_at']
                    updated_at = obj['fields']['updated_at']
                    if Page.objects.filter(id=page.pk).exists():
                        page = Page.objects.get(id=page.pk)
                        SubPage.objects.create(
                            title=title,
                            body=body,
                            page=page,
                            created_at=created_at,
                            updated_at=updated_at,
                            author=author
                        )
                        print('Subpage saved:', title)
                    else:
                        print('Page not found for subpage:', title)

                # return JsonResponse({'message': 'JSON data loaded successfully.'}, status=200)
                Activity.objects.create(author=author, title='Loaded JSON Data', body='Loaded JSON Data')
                messages.success(request, 'JSON data loaded successfully!')
                return redirect('home')
            except Exception as e:
                print('Error loading JSON data:', str(e))
                messages.error(request, 'Error loading JSON data: ' + str(e))
                return redirect('home')
                # return JsonResponse({'error': f'Error loading JSON data: {str(e)}'}, status=400)
        else:
            print('No JSON file uploaded.')
            messages.error(request, 'No JSON file uploaded.')
            return redirect('home')
            # return JsonResponse({'error': 'No JSON file uploaded.'}, status=400)

    return render(request, 'load_json.html')

def incrementPriority(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.priority -= 2
    notebook.save()
    messages.success(request, 'Priority incremented successfully!')
    return redirect('home')

def markReminderComplete(request, pk): 
    remainder = Remainder.objects.get(id=pk)
    remainder.is_completed = True
    remainder.is_over = True
    remainder.save()
    messages.success(request, 'Reminder marked as completed successfully!')
    return redirect('home')

def markReminderFavourite(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_favourite = True
    remainder.save()
    messages.success(request, 'Reminder marked as favourite successfully!')
    return redirect('home')

def markReminderUnComplete(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_completed = False
    remainder.is_over = False
    remainder.save()
    messages.success(request, 'Reminder marked as uncompleted successfully!')
    return redirect('home')

def markReminderUnFavourite(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_favourite = False
    remainder.save()
    messages.success(request, 'Reminder marked as unfavourite successfully!')
    return redirect('home')

def decrementPriority(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.priority += 2
    notebook.save()
    messages.success(request, 'Priority decremented successfully!')
    return redirect('home')

def stopSharingNotebook(request, pk):
    shared_notebook = SharedNotebook.objects.get(id=pk)
    shared_notebook.notebook.is_shared = False
    shared_notebook.notebook.save()
    Activity.objects.create(author=shared_notebook.owner, title='Stopped Sharing', body=f'Stopped sharing notebook with title of: {shared_notebook.notebook.title}')
    shared_notebook.delete()
    messages.success(request, 'Notebook stopped sharing successfully!')
    return redirect('home')

def startSharingNotebook(request, pk):
    notebook = Notebook.objects.get(id=pk)
    shared_notebook = SharedNotebook.objects.create(notebook=notebook, owner=notebook.author)
    if shared_notebook.notebook.is_password_protected:
        messages.error(request, 'Remove Password to Share it!')
    else:
        shared_notebook.notebook.is_shared = True
        shared_notebook.notebook.save()
        shared_notebook.save()
        Activity.objects.create(author=notebook.author, title='Started Sharing', body=f'Started sharing notebook with title of: {notebook.title}')
        messages.success(request, 'Notebook started sharing successfully! Here is the link to view it: ' + shared_notebook.shareable_link)
    return redirect('home')


def shared_notebooks_view(request, pk):
    shared_notebook = Notebook.objects.filter(id=pk)
    pages = Page.objects.filter(notebook__in=shared_notebook)
    subpages = SubPage.objects.filter(page__in=pages)
    return render(request, 'shared_notebook.html', {'shared_notebook': shared_notebook,'pages': pages, 'subpages': subpages})

def addToFavourites(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.is_favourite = True
    notebook.save()
    Activity.objects.create(author=notebook.author, title='Added to Favourites', body=f'Added notebook with title of: {notebook.title} to favourites')
    messages.success(request, 'Notebook added to favourites successfully!')
    return redirect('home')

# def removeToFavourites
def removeToFavourites(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.is_favourite = False
    notebook.save()
    Activity.objects.create(author=notebook.author, title='Removed to Favourites', body=f'Removed notebook with title of: {notebook.title} to favourites')
    messages.success(request, 'Notebook removed from favourites successfully!')
    return redirect('home')


def deleteNotebook(request, pk):
    notebook = Notebook.objects.get(id=pk)
    title = notebook.title
    notebook.delete()
    Activity.objects.create(author=notebook.author, title='Deleted Notebook', body=f'Deleted Notebook with title of: {notebook.title}')
    messages.success(request, title + 'Notebook deleted successfully!')
    return redirect('home')

def deletePage(request, pk):
    page = Page.objects.get(id=pk)
    title = page.title
    page.delete()
    Activity.objects.create(author=page.notebook.author, title='Deleted Page', body=f'Deleted Page with title of: {page.title}')
    messages.success(request,  title + ' Page deleted successfully!')
    return redirect('home')

def deleteSubPage(request, pk):
    subpage = SubPage.objects.get(id=pk)
    title = subpage.title
    subpage.delete()
    Activity.objects.create(author=subpage.notebook.author, title='Deleted SubPage', body=f'Deleted SubPage with title of: {subpage.title}')
    messages.success(request,  title + ' SubPage deleted successfully!')
    return redirect('home')

def deleteAllActivities(request):
    logined_profile = Profile.objects.get(user=request.user)
    activities = Activity.objects.filter(author=logined_profile)
    activities.delete()
    messages.success(request, 'All activities deleted successfully!')
    return redirect('home')

def updateStickyNotes(request, pk):
    stickynote = StickyNotes.objects.get(id=pk)
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = StickyNotesForm(request.POST, instance=stickynote)
        if form.is_valid():
            form.save()
            Activity.objects.create(author=logined_profile, title='Updated Sticky Note', body=f'Updated Sticky Note with title of: {stickynote.title}')
            messages.success(request, 'Sticky note updated successfully!')
            return redirect('home')
    else:
        form = StickyNotesForm(instance=stickynote)
    return render(request, 'update_sticky_notes.html', {'form': form, 'stickynote': stickynote})

def create_remainder(request):
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = RemainderForm(request.POST)
        if form.is_valid():
            remainder = form.save(commit=False)
            remainder.author = logined_profile
            remainder.save()
            Activity.objects.create(author=logined_profile, title='Created New Remainder', body=f'Created new Remainder with title of: {remainder.title}')
            messages.success(request, 'Remainder created successfully!')
            return redirect('home')
    else:
        form = RemainderForm()
    return render(request, 'remainder_create.html', {'form': form})

def deleteRemainder(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.delete()
    Activity.objects.create(author=remainder.author, title='Deleted Remainder', body=f'Deleted Remainder with title of: {remainder.title}')
    messages.success(request, 'Remainder deleted successfully!')
    return redirect('home')

def create_notebook(request):
    logged_in_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        print("POST")
        form = NotebookForm(request.POST)
        if form.is_valid():
            try:
                notebook = form.save(commit=False)
                notebook.author = logged_in_profile
                notebook.save()
                # Create new activity 
                Activity.objects.create(author=logged_in_profile, title='Created New Notebook', body=f'Created new Notebook with title of: {notebook.title}')
                messages.success(request, 'Notebook created successfully!')
                return redirect('create_page', pk=notebook.pk)  # Redirect to create page with the new notebook's pk
            except IntegrityError:
                # Handle IntegrityError if needed
                pass
    else:
        form = NotebookForm()
    return render(request, 'notebook_create.html', {'form': form})

def create_page(request, pk):
    notebook = Notebook.objects.get(id=pk)
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.notebook = notebook
            page.author = logined_profile
            page.save()
            # Create new activity
            Activity.objects.create(author=logined_profile, title='Created New Page', body=f'Created new Page for notebook with title of: {notebook.title}')
            messages.success(request, 'Page created successfully!')
            return redirect('home')  # Redirect to home or any other page
    else:
        form = PageForm()
    return render(request, 'page_create.html', {'form': form})

def create_subpage(request, notebook_pk:int,page_pk:int):
    notebook = Notebook.objects.get(id=notebook_pk)
    page = Page.objects.get(id=page_pk)
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = SubPageForm(request.POST)
        if form.is_valid():
            subpage = form.save(commit=False)
            subpage.notebook = notebook
            subpage.author = logined_profile
            subpage.page = page
            subpage.save()
            # Create new activity
            Activity.objects.create(author=logined_profile, title='Created New Subpage', body=f'Created new Subpage for page with title of: {page.title}')
            messages.success(request, 'Sub-Page created successfully!')
            return redirect('home')  # Redirect to home or any other page
    else:
        form = SubPageForm()
    return render(request, 'sub_page_create.html', {'form': form})

@login_required
def search(request):
    user = Profile.objects.get(user=request.user)  # Get the logged-in user

    query = request.GET.get('query', '')  # Get the query parameter from the URL
    results = {}

    if query:
        # Search Notebooks created by the logged-in user
        notebook_results = Notebook.objects.filter(
            Q(title__icontains=query) | Q(body__icontains=query) | Q(priority__icontains=query) | Q(is_favourite__icontains=query),
            author=user
        )
        
        # Search Pages created by the logged-in user and include the related Notebook for breadcrumbs
        page_results = Page.objects.filter(
            Q(title__icontains=query) | Q(body__icontains=query),
            notebook__author=user
        ).select_related('notebook')

        # Adjusting results to include breadcrumb style output and subpage searching
        pages_with_breadcrumbs = []
        for page in page_results:
            page_data = {'breadcrumb': f"{page.notebook.title} > {page.title}", 'detail': page, 'subpages': []}  # Initialize 'subpages' as an empty list
            subpage_results = SubPage.objects.filter(
                Q(title__icontains=query) | Q(body__icontains=query),
                page=page
            )
            for subpage in subpage_results:
                page_data['subpages'].append(subpage)
            pages_with_breadcrumbs.append(page_data)

        # Search Remainders created by the logged-in user
        remainder_results = Remainder.objects.filter(
            Q(title__icontains=query) | Q(body__icontains=query) | Q(is_favourite__icontains=query),
            author=user
        )

        results = {
            'notebooks': notebook_results,
            'pages': pages_with_breadcrumbs,
            'remainders': remainder_results,
        }
    else:
        results = {}

    return render(request, 'search.html', {'query': query, 'results': results})


def GeneratePdf(request,pk):
    context ={}
    # add the dictionary during initialization
    notebook = Notebook.objects.get(pk = pk)
    page = Page.objects.filter(notebook = notebook)
    subpage = SubPage.objects.filter(page__in = page)
    context["notebook"] = notebook
    context["pages"] = page
    context["subpages"] = subpage
    #getting the template
    pdf = render_to_pdf('pdf_template.html',context)
        
    #rendering the template
    return HttpResponse(pdf, content_type='application/pdf')

def verify_password(request, pk):
    if request.method == 'POST':
        password = request.POST.get('notebook_password')
        notebook = Notebook.objects.get(pk = pk)
        print(str(notebook.password)+" "+str(password))
        if notebook.password == password:
            notebook.is_password_entered = True
            print(notebook.is_password_entered)
            notebook.save()
            return redirect('password_protected_notebook', pk=pk)
        else:
            return redirect('home')
    else:
        context = {}            
    return render(request, 'verify.html', context)

def password_protected_notebook(request, pk):
    notebook = Notebook.objects.get(pk = pk)
    pages = Page.objects.filter(notebook=notebook)
    if notebook.is_password_entered == True and notebook.is_password_protected == True:
        notebook.is_accessed_recently = True
        notebook.save()
        context = {}
        context["notebook"] = Notebook.objects.get(pk = pk) 
        context['pages'] = Page.objects.filter(notebook=notebook)
        context['subpages'] = SubPage.objects.filter(page__in=pages)
        context['logined_profile'] = Profile.objects.get(user=request.user)
    else:
        context = {}
    return render(request, 'password_protected_notebook.html', context)

def notebook_password_reset_page(request, pk):
    notebook = Notebook.objects.get(pk = pk)
    context = {}
    context['notebook'] = notebook
    return render(request, 'notebook_password_reset_page.html', context)