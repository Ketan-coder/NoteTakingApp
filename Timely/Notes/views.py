import datetime
import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers import deserialize, serialize
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
# Uncomment when done with lock
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from Notes.utils import render_to_pdf, send_email
from Users.models import Profile

from Timely import settings as project_settings

from .forms import (NotebookForm, PageForm, RemainderForm, StickyNotesForm,
                    SubPageForm)
from .models import (Activity, Notebook, Page, Remainder, SharedNotebook,
                     StickyNotes, SubPage, Todo)

# # Create your views here.
# Cache duration (in seconds)
# CACHE_TIMEOUT = 120  # 2 minutes

# @login_required
# def index(request):
#     if request.user.is_authenticated:
#         start_time = datetime.datetime.now()

#         logined_profile = Profile.objects.get(user=request.user)

#         # Cache Key Definitions
#         notebooks_cache_key = f'notebooks_list_{request.user.id}'
#         pages_cache_key = f'pages_{request.user.id}'
#         subpages_cache_key = f'subpages_{request.user.id}'

#         # Fetch Notebooks (Use Cache)
#         notebooks_list = cache.get(notebooks_cache_key)
#         if notebooks_list is None:  # Check for None, not empty list
#             notebooks_list = Notebook.objects.filter(author=logined_profile).only(
#                 'id', 'title', 'is_accessed_recently', 'priority', 'is_favourite',
#                 'is_shared', 'is_password_protected', 'is_password_entered', 'password',
#                 'author', 'created_at', 'updated_at'
#             ).defer('body').order_by('-is_accessed_recently')
#             cache.set(notebooks_cache_key, notebooks_list, CACHE_TIMEOUT)
#             print('Notebooks list cached successfully.')

#         notebooks_list_priority = notebooks_list.order_by('priority')

#         # Fetch Pages (Use Cache)
#         pages = cache.get(pages_cache_key)
#         if not pages:
#             pages = Page.objects.filter(notebook__in=notebooks_list).select_related('notebook').order_by('-updated_at')
#             cache.set(pages_cache_key, list(pages), CACHE_TIMEOUT)
#             print('Pages cached successfully.')

#         # Fetch SubPages (Use Cache)
#         subpages = cache.get(subpages_cache_key)
#         if not subpages:
#             subpages = SubPage.objects.filter(page__in=pages)
#             cache.set(subpages_cache_key, list(subpages), CACHE_TIMEOUT)
#             print('SubPages cached successfully.')

#         # Real-time Queries (No Caching)
#         activities_list = Activity.objects.filter(author=logined_profile).order_by('-created_at')
#         sticky_notes = StickyNotes.objects.filter(author=logined_profile)
#         remainders = Remainder.objects.filter(author=logined_profile).order_by('alert_time')

#         # Favorites
#         favouritesNotebooks = notebooks_list.filter(is_favourite=True)
#         favouritesPages = Page.objects.filter(is_favourite=True, notebook__in=favouritesNotebooks)
#         favouritesRemainders = remainders.filter(is_favourite=True)

#         # Shared Notebooks
#         sharedNotebooks = SharedNotebook.objects.filter(owner=logined_profile).order_by('-shared_at')

#         # Pagination Setup
#         paginator_activities = Paginator(activities_list, 5)
#         page_number_activities = request.GET.get('page')
#         activities = paginator_activities.get_page(page_number_activities)

#         paginator_notebooks = Paginator(notebooks_list, 5)
#         page_number_notebooks = request.GET.get('notebook_page')
#         notebooks = paginator_notebooks.get_page(page_number_notebooks)

#         # Background Updates
#         check_remainders()
#         mark_password_as_not_entered(notebooks_list)
#         mark_recently_accessed_as_false(pages, notebooks_list)

#         end_time = datetime.datetime.now()
#         print(f"Time taken: {end_time - start_time}")

#         context = {
#             'notebooks': notebooks, 'notebooks_list_priority': notebooks_list_priority,
#             'logined_profile': logined_profile, 'activities': activities, 'sticky_notes': sticky_notes,
#             "pages": pages, "subpages": subpages, 'remainders': remainders,
#             'favouritesNotebooks': favouritesNotebooks, 'favouritesPages': favouritesPages,
#             'favouritesRemainders': favouritesRemainders, 'sharedNotebooks': sharedNotebooks
#         }

#         return render(request, "index.html", context)
#     else:
#         return redirect('login')


# Create your views here.
def index(request):
    if request.user.is_authenticated:
        start_time = datetime.datetime.now()
        request.session["page"] = "home"
        logined_profile = Profile.objects.get(user=request.user)
        notebooks_list = (
            Notebook.objects.filter(author=logined_profile)
            .only(
                "id",
                "title",
                "is_accessed_recently",
                "priority",
                "is_favourite",
                "is_shared",
                "is_password_protected",
                "is_password_entered",
                "password",
                "author",
                "created_at",
                "updated_at",
            )
            .defer("body")
            .order_by("-is_accessed_recently")
        )

        notebooks_list_priority = notebooks_list.order_by("priority")
        pages = (
            Page.objects.filter(notebook__in=notebooks_list)
            .select_related("notebook")
            .order_by("-order")
        )
        subpages = SubPage.objects.filter(page__in=pages)
        # activities_list = Activity.objects.filter(author=logined_profile).order_by('-created_at')
        sticky_notes = StickyNotes.objects.filter(author=logined_profile)
        remainders = Remainder.objects.filter(author=logined_profile).order_by(
            "alert_time"
        )
        favouritesNotebooks = notebooks_list.filter(is_favourite=True)
        favouritesPages = Page.objects.filter(notebook__in=favouritesNotebooks)
        favouritesRemainders = remainders.filter(is_favourite=True)
        sharedNotebooks = SharedNotebook.objects.filter(owner=logined_profile).order_by(
            "-shared_at"
        )
        # todos = Todo.objects.filter(author=logined_profile).order_by("-is_completed")
        from django.db.models import Count

        todos = Todo.objects.filter(author=logined_profile).annotate(
            group_count=Count("todo_groups")
        ).filter(group_count=0).order_by("-is_completed")

        todogroups = TodoGroup.objects.filter(author=logined_profile).annotate(
                        not_viewed_count=Count(
                            'todos',
                            filter=Q(todos__extra_fields__is_viewed=False)
                        )
                    ).order_by('-created_at')
 
        # Set up pagination
        # paginator = Paginator(activities_list, 5)  # Show 10 activities per page
        # page_number = request.GET.get('page')
        # activities = paginator.get_page(page_number)
        paginator_notebook = Paginator(notebooks_list, 5)  # Show 10 activities per page
        page_number = request.GET.get("notebook_page")
        notebooks = paginator_notebook.get_page(page_number)
        check_remainders()
        # check_activities()
        mark_password_as_not_entered(notebooks_list)
        mark_recently_accessed_as_false(pages, notebooks_list)

        end_time = datetime.datetime.now()

        print(f"Time taken: {end_time - start_time}")
        context = {
            "notebooks": notebooks,
            "notebooks_list_priority": notebooks_list_priority,
            "logined_profile": logined_profile,
            "sticky_notes": sticky_notes,
            "pages": pages,
            "subpages": subpages,
            "remainders": remainders,
            "favouritesNotebooks": favouritesNotebooks,
            "todos": todos,
            "favouritesPages": favouritesPages,
            "favouritesRemainders": favouritesRemainders,
            "sharedNotebooks": sharedNotebooks,
            "todogroup": todogroups,
        }
    else:
        context = {}
        redirect("login")
    return render(request, "index.html", context)


def add_todo(request):
    """Add a new todo"""
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        title = request.POST.get("todo_title")
        if title:
            todo = Todo.objects.create(title=title, author=logined_profile)
            return render(request, "partials/todo_item.html", {"todo": todo})
    return HttpResponse(status=400)


def toggle_todo(request, todo_id):
    """Toggle todo completion"""
    logined_profile = Profile.objects.get(user=request.user)
    todo = get_object_or_404(Todo, id=todo_id, author=logined_profile)
    todo.is_completed = not todo.is_completed
    todo.save()
    return render(request, "partials/todo_item.html", {"todo": todo})


# def delete_todo(request, todo_id):
#     """ Delete a todo item """
#     logined_profile = Profile.objects.get(user=request.user)
#     todo = get_object_or_404(Todo, id=todo_id, author=logined_profile)
#     todo.delete()
#     return HttpResponse(status=204)
def delete_todo(request, todo_id):
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        try:
            todo = get_object_or_404(Todo, id=todo_id, author=logined_profile)
            todo.delete()
            messages.success(request, "Todo Deleted Sucessfully!")
            return HttpResponse("Deleted successfully")
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)


# def fetch_notebook_contents(request, notebook_id, page_id=None, subpage_id=None):
#     """Fetch the body content of a notebook, page, or subpage dynamically for HTMX."""

#     if subpage_id:
#         content = get_object_or_404(SubPage, id=subpage_id).body
#     elif page_id:
#         content = get_object_or_404(Page, id=page_id).body
#     else:
#         notebook = get_object_or_404(Notebook, id=notebook_id, author=request.user.profile)
#         content = notebook.body  # Ensure we fetch the correct body

#     return render(request, "components/notebook_body.html", {"body": content})


def fetch_notebook_contents(request, notebook_id=None, page_id=None, subpage_id=None, notebook_uuid=None, subpage_uuid=None, page_uuid=None):
    """Fetch the body content of a notebook, page, or subpage dynamically for HTMX as JSON."""

    content = None  # Default empty content

    if subpage_id:
        content = get_object_or_404(SubPage, id=subpage_id).body
    elif subpage_uuid:
        content = get_object_or_404(SubPage, subpage_uuid=subpage_uuid).body
    elif page_id:
        content = get_object_or_404(Page, id=page_id).body
    elif page_uuid:
        content = get_object_or_404(Page, page_uuid=page_uuid).body
    elif notebook_id:
        notebook = get_object_or_404(Notebook, id=notebook_id)
        content = notebook.body  # Ensure we fetch the correct body
    elif notebook_uuid:
        notebook = get_object_or_404(Notebook, notebook_uuid=notebook_uuid)
        content = notebook.body
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)

    return JsonResponse({"body": content})


def mark_password_as_not_entered(notebook_list):
    for notebook in notebook_list:
        if notebook.is_password_entered == True:
            notebook.is_password_entered = False
            notebook.save()
        else:
            pass


# def mark_recently_accessed_as_false(page_list,notebooks):
#     recently_accessed_notebook = []
#     for notebook in notebooks:
#         if notebook.is_accessed_recently == True:
#             recently_accessed_notebook.append(notebook)


#     if len(recently_accessed_notebook) >= 3:
#         for page in recently_accessed_notebook.page_set.all():
#             if page.updated_at < timezone.now() + datetime.timedelta(hours=6, minutes=30):
#                 related_notebook = Notebook.objects.get(id=page.notebook_id)
#                 related_notebook.is_accessed_recently = False
#                 related_notebook.save()
def mark_recently_accessed_as_false(page_list, notebooks):
    recently_accessed_notebooks = [
        notebook for notebook in notebooks if notebook.is_accessed_recently
    ]

    if len(recently_accessed_notebooks) >= 3:
        for notebook in recently_accessed_notebooks:  # Iterate over each notebook
            for page in notebook.page_set.all():  # Access `page_set` for each notebook
                if page.updated_at < timezone.now() + datetime.timedelta(
                    hours=6, minutes=30
                ):
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
        if remainder.alert_time < timezone.now() + datetime.timedelta(
            hours=5, minutes=30
        ):
            remainder.is_over = True
            remainder.delete()
        else:
            remainder.is_over = False
            remainder.save()


def update_notebook_modal(request, pk):
    notebook = Notebook.objects.get(id=pk)
    if request.method == "POST":
        form = NotebookForm(request.POST, instance=notebook)
        if form.is_valid():
            priority = form.cleaned_data["priority"]
            if priority < 1:
                form.add_error("priority", "Priority cannot be less than 1")
                return render(
                    request,
                    "update_notebook_modal.html",
                    {"form": form, "notebook": notebook},
                )
            if priority > 5:
                form.add_error("priority", "Priority cannot be greater than 5")
                return render(
                    request,
                    "update_notebook_modal.html",
                    {"form": form, "notebook": notebook},
                )
            form.save()
            Activity.objects.create(
                author=notebook.author,
                title="Updated Notebook",
                body=f"Updated notebook with title of: {notebook.title}",
            )
            messages.success(request, "Notebook updated successfully!")
            return redirect("home")  # Redirect to appropriate page
    else:
        form = NotebookForm(instance=notebook)
    return render(
        request, "update_notebook_modal.html", {"form": form, "notebook": notebook}
    )


def update_page_modal(request, pk):
    page = Page.objects.get(id=pk)
    if request.method == "POST":
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            Activity.objects.create(
                author=page.notebook.author,
                title="Updated Page",
                body=f"Updated page with title of: {page.title}",
            )
            messages.success(request, "Page updated successfully!")
            return redirect("home")  # Redirect to appropriate page
    else:
        form = PageForm(instance=page)
    return render(request, "update_page_modal.html", {"form": form, "page": page})


def update_sub_page_modal(request, pk):
    subpage = SubPage.objects.get(id=pk)
    if request.method == "POST":
        form = SubPageForm(request.POST, instance=subpage)
        if form.is_valid():
            form.save()
            Activity.objects.create(
                author=subpage.notebook.author,
                title="Updated Page",
                body=f"Updated sub-page with title of: {subpage.title}",
            )
            messages.success(request, "Page updated successfully!")
            return redirect("home")  # Redirect to appropriate page
    else:
        form = SubPageForm(instance=subpage)
    return render(
        request, "update_sub_page_modal.html", {"form": form, "subpage": subpage}
    )


def update_reminder(request, pk):
    reminder = Remainder.objects.get(id=pk)
    if request.method == "POST":
        form = RemainderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            Activity.objects.create(
                author=reminder.notebook.author,
                title="Updated Reminder",
                body=f"Updated reminder with title of: {reminder.title}",
            )
            messages.success(request, "Reminder updated successfully!")
            return redirect("home")  # Redirect to appropriate page
    else:
        form = RemainderForm(instance=reminder)
    return render(request, "update_reminder.html", {"form": form, "reminder": reminder})


def exportNotebookToJson(request, pk):
    # Get the Notebook object or return 404 if not found
    notebook = get_object_or_404(Notebook, id=pk)

    # Collect pages related to the notebook
    pages = Page.objects.filter(notebook=notebook)

    # Collect subpages for each page
    subpages = SubPage.objects.filter(page__in=pages)

    # Serialize the notebook, pages, and subpages
    notebook_data = serialize("json", [notebook])
    pages_data = serialize("json", pages)
    subpages_data = serialize("json", subpages)

    # Combine all serialized data into one dictionary
    complete_data = {
        "notebook": json.loads(notebook_data),
        "pages": json.loads(pages_data),
        "subpages": json.loads(subpages_data),
    }

    # Convert the combined data to a JSON string
    json_data = json.dumps(complete_data, indent=4)

    # Create the HTTP response with the JSON string as an attachment
    response = HttpResponse(json_data, content_type="application/json")
    response["Content-Disposition"] = (
        f'attachment; filename="{notebook.title.replace("/", "-")}.json"'  # Avoiding directory traversal issues
    )

    messages.success(request, "Notebook exported successfully!")

    return response


@login_required
def loadJsonToModels(request):
    request.session["page"] = "load_json"
    if request.method == "POST":
        json_file = request.FILES.get("json_file")

        if json_file:
            try:
                json_data = json.loads(json_file.read().decode("utf-8"))
                user_profile = Profile.objects.get(user=request.user)
                local_now = timezone.localtime(timezone.now())
                notebook_map = {}
                page_map = {}
                is_edited = False

                with transaction.atomic():  # Ensures atomicity
                    # Create Notebooks
                    for obj in json_data.get("notebook", []):
                        fields = obj["fields"]
                        author_id = fields.get("author", None)

                        # Find the real author, fallback to None (We don't want to change ownership)
                        real_author = Profile.objects.filter(id=author_id).first()
                        author = user_profile  # Always assign request.user

                        # Check if notebook already exists for the logged-in user
                        notebook, created = Notebook.objects.update_or_create(
                            title=fields["title"],  # Use title as unique identifier
                            author=author,  # Ensure it's the logged-in user's notebook
                            defaults={
                                "body": fields["body"],
                                "priority": 0,
                                "is_favourite": False,
                                "is_shared": False,
                            },
                        )

                        # Manually set timestamps
                        notebook.created_at = (
                            local_now if created else notebook.created_at
                        )
                        notebook.updated_at = local_now
                        notebook.save()

                        notebook_map[obj["pk"]] = notebook  # Store reference

                        if not created:
                            is_edited = True

                    # Create Pages
                    for obj in json_data.get("pages", []):
                        fields = obj["fields"]
                        notebook_id = fields["notebook"]
                        notebook = notebook_map.get(notebook_id)

                        if notebook:
                            # Create new page, no update, only creation
                            page, created = Page.objects.update_or_create(
                                title=fields["title"],
                                notebook=notebook,
                                author=notebook.author,
                                defaults={
                                    "body": fields["body"],
                                    "order": fields["order"],
                                    "created_at": local_now,
                                    "updated_at": local_now,
                                },
                            )
                            page_map[obj["pk"]] = page

                            if not created:
                                is_edited = True

                    # Create SubPages
                    for obj in json_data.get("subpages", []):
                        fields = obj["fields"]
                        page_id = fields["page"]
                        page = page_map.get(page_id)

                        if page:
                            subpage, created = SubPage.objects.update_or_create(
                                title=fields["title"],
                                page=page,
                                author=page.author,
                                notebook=page.notebook,
                                defaults={
                                    "body": fields["body"],
                                    "created_at": local_now,
                                    "updated_at": local_now,
                                },
                            )

                            if not created:
                                is_edited = True
                    # Format the time as "12 December, 2024 - 01:50"
                    formatted_time = local_now.strftime("%d %B, %Y - %H:%M")

                    # Log activity in the **real author's profile** if they exist
                    if not is_edited:
                        if real_author and real_author != user_profile:
                            Activity.objects.create(
                                author=real_author,
                                title="Notebook Added",
                                body=f"'{notebook.title}' Notebook was added by {user_profile.user.username} on {formatted_time}.",
                            )

                        # Log activity
                        Activity.objects.create(
                            author=user_profile,
                            title="Created Notebook from JSON",
                            body="Notebook and its pages were created",
                        )
                        messages.success(
                            request,
                            "Notebook created successfully from uploaded document!",
                        )
                    else:
                        # Log activity
                        Activity.objects.create(
                            author=user_profile,
                            title=f"{notebook.title} Notebook Updated from JSON",
                            body=f"{notebook.title} Notebook and its pages were Updated",
                        )
                        messages.success(
                            request,
                            f"{notebook.title} Notebook updated successfully from uploaded document!",
                        )
                    return redirect("home")

            except Exception as e:
                messages.error(request, f"Error processing JSON: {str(e)}")
                return redirect("home")

        else:
            messages.error(request, "No JSON file uploaded.")
            return redirect("home")

    return render(request, "load_json.html")


def incrementPriority(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.priority -= 2
    notebook.save()
    messages.success(request, "Priority incremented successfully!")
    return redirect("home")


def markReminderComplete(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_completed = True
    remainder.is_over = True
    remainder.save()
    messages.success(request, "Reminder marked as completed successfully!")
    return redirect("home")


def markReminderFavourite(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_favourite = True
    remainder.save()
    messages.success(request, "Reminder marked as favourite successfully!")
    return redirect("home")


def markReminderUnComplete(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_completed = False
    remainder.is_over = False
    remainder.save()
    messages.success(request, "Reminder marked as uncompleted successfully!")
    return redirect("home")


def markReminderUnFavourite(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.is_favourite = False
    remainder.save()
    messages.success(request, "Reminder marked as unfavourite successfully!")
    return redirect("home")


def decrementPriority(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.priority += 2
    notebook.save()
    messages.success(request, "Priority decremented successfully!")
    return redirect("home")


from django.db import transaction


def stopSharingNotebook(request, pk):
    with transaction.atomic():  # Ensures everything commits or rolls back
        shared_notebook = get_object_or_404(SharedNotebook, id=pk)
        notebook = shared_notebook.notebook  # Direct reference

        # Update Notebook fields
        notebook.is_shared = False
        notebook.is_public = False
        notebook.save(update_fields=["is_shared", "is_public"])

        # Force refresh from DB
        notebook.refresh_from_db()

        # Clear shared users
        shared_notebook.sharedTo.clear()
        shared_notebook.can_edit = False
        shared_notebook.save()

        # Log Activity
        Activity.objects.create(
            author=shared_notebook.owner,
            title="Stopped Sharing",
            body=f"Stopped sharing notebook with title: {notebook.title}",
        )

        # Delete the SharedNotebook entry
        shared_notebook.delete()

        # Ensure notebook object is properly updated
        Notebook.objects.filter(id=notebook.id).update(is_shared=False, is_public=False)

    messages.success(request, "Notebook sharing has been stopped successfully!")
    return redirect("home")


def startSharingNotebook(request, pk):
    notebook = get_object_or_404(Notebook, id=pk)
    logined_profile = get_object_or_404(Profile, user=request.user)

    if notebook.author != logined_profile:
        messages.error(request, "You do not have permission to share this notebook.")
        return redirect("home")

    if notebook.is_password_protected:
        messages.error(request, "Remove the password before sharing!")
        return redirect("home")

    if request.method == "POST":
        shared_emails = request.POST.get("shared_to_emails", "").strip()
        can_edit = "can_edit" in request.POST

        shared_notebook, created = SharedNotebook.objects.get_or_create(
            notebook=notebook, defaults={"owner": logined_profile}
        )

        if shared_emails:
            email_list = [
                email.strip() for email in shared_emails.split(",") if email.strip()
            ]
            valid_users = []
            invalid_emails = []

            for email in email_list:
                shared_to_user = Profile.objects.filter(email=email).first()
                if shared_to_user:
                    valid_users.append(shared_to_user)
                else:
                    invalid_emails.append(email)

            if valid_users:
                shared_notebook.sharedTo.add(*valid_users)
                shared_notebook.can_edit = can_edit
                notebook.shared_with.add(*valid_users)
                notebook.is_shared = True
                shared_notebook.shareable_link = "sharedNotebooks/"
                notebook.save()
                shared_notebook.save()
                messages.success(
                    request,
                    f"Notebook shared successfully with {', '.join([user.email for user in valid_users])}!",
                )

            if invalid_emails:
                messages.warning(
                    request, f"These emails are invalid: {', '.join(invalid_emails)}"
                )

        else:
            shared_notebook.sharedTo.clear()
            shared_notebook.can_edit = False
            notebook.is_public = True
            notebook.is_shared = True
            notebook.shared_with.clear()
            shared_notebook.shareable_link = "publicNotebooks/"
            notebook.save()
            shared_notebook.save()
            messages.success(request, "Notebook has been made public!")

        return redirect("home")

    return redirect("home")


def fetch_profile_details(request):
    emails = request.GET.get("shared_to_emails", "").strip()
    if not emails:
        return HttpResponse(
            "<div class='alert alert-warning'>Please enter at least one email.</div>"
        )

    email_list = [email.strip() for email in emails.split(",") if email.strip()]
    profile_info = []

    for email in email_list:
        profile = Profile.objects.filter(email=email).first()
        if profile:
            profile_info.append(
                f"<strong>{profile.firstName} {profile.lastName}</strong> ({email})"
            )
        else:
            profile_info.append(
                f"<span class='text-danger'>User not found: {email}</span>"
            )

    return HttpResponse(
        f"<div class='alert alert-success'>Sharing with: {', '.join(profile_info)}</div>"
    )


# def fetch_profile_details(request):
#     email = request.GET.get("shared_to_email", "").strip()

#     if not email:
#         return HttpResponse("<div class='alert alert-warning'>Please enter an email.</div>")

#     profile = Profile.objects.filter(email=email).first()

#     if profile:
#         return HttpResponse(f"<div class='alert alert-success'>You are going to share this notebook with <strong>{profile.firstName} {profile.lastName}</strong>.</div>")
#     else:
#         return HttpResponse("<div class='alert alert-danger'>User not found. Please check the email.</div>")

# def shared_notebooks_view(request, pk):
#     logined_profile = Profile.objects.filter(user=request.user)
#     shared_notebook = Notebook.objects.filter(id=pk,shared_with=logined_profile)
#     public_notebooks = Notebook.objects.filter
#     pages = Page.objects.filter(notebook__in=shared_notebook)
#     subpages = SubPage.objects.filter(page__in=pages)
#     return render(request, 'shared_notebook.html', {'shared_notebook': shared_notebook,'pages': pages, 'subpages': subpages})

# def shared_notebooks_view(request, pk):
#     logined_profile = get_object_or_404(Profile, user=request.user)

#     # Fetch shared and public notebooks
#     notebooks = Notebook.objects.filter(
#         id=pk,
#         shared_with=logined_profile
#     ).prefetch_related('page_set__subpage_set')

#     shared_notebooks = SharedNotebook.objects.filter(notebook=notebooks).select_related('notebook')

#     pages = []
#     subpages = []

#     for notebook in notebooks:
#         pages.extend(notebook.page_set.all())  # Fetch all pages for the notebook
#         for page in notebook.page_set.all():
#             subpages.extend(page.subpage_set.all())  # Fetch all subpages for each page

#     return render(request, 'shared_notebook.html', {
#         'notebooks': notebooks,
#         'shared_notebooks':shared_notebooks,
#         'pages': pages,
#         'subpages': subpages,
#         'logined_profile': logined_profile,
#     })


def shared_notebooks_view(request):
    logined_profile = get_object_or_404(Profile, user=request.user)

    # Fetch all notebooks shared with the logged-in profile
    notebooks = Notebook.objects.filter(shared_with=logined_profile).prefetch_related(
        "page_set__subpage_set"
    )

    # Fetch shared notebook permissions
    shared_notebooks = SharedNotebook.objects.filter(
        notebook__in=notebooks
    ).select_related("notebook")

    pages = []
    subpages = []

    for notebook in notebooks:
        pages.extend(notebook.page_set.all())  # Fetch all pages
        for page in notebook.page_set.all():
            subpages.extend(page.subpage_set.all())  # Fetch subpages

    return render(
        request,
        "shared_notebook.html",
        {
            "notebooks": notebooks,
            "shared_notebooks": shared_notebooks,
            "pages": pages,
            "subpages": subpages,
            "logined_profile": logined_profile,
        },
    )


def public_notebooks_view(request):
    # Fetch all public notebooks with related pages and subpages in one query
    request.session['page'] = 'public_notebooks'
    public_notebooks = Notebook.objects.filter(is_public=True).prefetch_related(
        "page_set__subpage_set"
    )

    # Use list comprehensions for efficiency
    pages = [page for notebook in public_notebooks for page in notebook.page_set.all()]
    subpages = [subpage for page in pages for subpage in page.subpage_set.all()]

    return render(
        request,
        "public_notebooks.html",
        {
            "notebooks": public_notebooks,
            "pages": pages,
            "subpages": subpages,
        },
    )


def addToFavourites(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.is_favourite = True
    notebook.save()
    Activity.objects.create(
        author=notebook.author,
        title="Added to Favourites",
        body=f"Added notebook with title of: {notebook.title} to favourites",
    )
    messages.success(request, "Notebook added to favourites successfully!")
    return redirect("home")


# def removeToFavourites
def removeToFavourites(request, pk):
    notebook = Notebook.objects.get(id=pk)
    notebook.is_favourite = False
    notebook.save()
    Activity.objects.create(
        author=notebook.author,
        title="Removed to Favourites",
        body=f"Removed notebook with title of: {notebook.title} to favourites",
    )
    messages.success(request, "Notebook removed from favourites successfully!")
    return redirect("home")


def deleteNotebook(request, pk):
    notebook = Notebook.objects.get(id=pk)
    title = notebook.title
    notebook.delete()
    Activity.objects.create(
        author=notebook.author,
        title="Deleted Notebook",
        body=f"Deleted Notebook with title of: {notebook.title}",
    )
    messages.success(request, title + "Notebook deleted successfully!")
    return redirect("home")


def deletePage(request, pk):
    page = Page.objects.get(id=pk)
    title = page.title
    page.delete()
    Activity.objects.create(
        author=page.notebook.author,
        title="Deleted Page",
        body=f"Deleted Page with title of: {page.title}",
    )
    messages.success(request, title + " Page deleted successfully!")
    return redirect("home")


def deleteSubPage(request, pk):
    subpage = SubPage.objects.get(id=pk)
    title = subpage.title
    subpage.delete()
    Activity.objects.create(
        author=subpage.notebook.author,
        title="Deleted SubPage",
        body=f"Deleted SubPage with title of: {subpage.title}",
    )
    messages.success(request, title + " SubPage deleted successfully!")
    return redirect("home")


def deleteAllActivities(request):
    logined_profile = Profile.objects.get(user=request.user)
    activities = Activity.objects.filter(author=logined_profile)
    activities.delete()
    messages.success(request, "All activities deleted successfully!")
    return redirect("home")


# def updateStickyNotes(request, pk):
#     stickynote = StickyNotes.objects.get(id=pk)
#     logined_profile = Profile.objects.get(user=request.user)
#     if request.method == 'POST':
#         form = StickyNotesForm(request.POST, instance=stickynote)
#         if form.is_valid():
#             form.save()
#             Activity.objects.create(author=logined_profile, title='Updated Sticky Note', body=f'Updated Sticky Note with title of: {stickynote.title}')
#             messages.success(request, 'Sticky note updated successfully!')
#             return redirect('home')
#     else:
#         form = StickyNotesForm(instance=stickynote)
#     return render(request, 'update_sticky_notes.html', {'form': form, 'stickynote': stickynote})
def updateStickyNotes(request, pk):
    """Handles updating sticky notes with autosave support."""
    logined_profile = Profile.objects.get(user=request.user)
    stickynote = get_object_or_404(StickyNotes, id=pk, author=logined_profile)

    if request.method == "POST":
        title = request.POST.get("title", stickynote.title)
        body = request.POST.get("body", stickynote.body)

        updated = False
        if stickynote.title != title:
            stickynote.title = title
            updated = True
        if stickynote.body != body:
            stickynote.body = body
            updated = True

        if updated:
            stickynote.save()
            Activity.objects.create(
                author=logined_profile,
                title="Updated Sticky Note",
                body=f"Updated Sticky Note with title: {stickynote.title}",
            )
            messages.success(request, "Sticky note updated successfully!")
            return HttpResponse("Saved")

        return HttpResponse("")  # No changes, return empty response

    return render(request, "update_sticky_notes.html", {"stickynote": stickynote})


def create_remainder(request):
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = RemainderForm(request.POST)
        if form.is_valid():
            remainder = form.save(commit=False)
            remainder.author = logined_profile
            remainder.save()
            Activity.objects.create(
                author=logined_profile,
                title="Created New Remainder",
                body=f"Created new Remainder with title of: {remainder.title}",
            )
            messages.success(request, "Remainder created successfully!")
            return redirect("home")
    else:
        form = RemainderForm()
    return render(request, "remainder_create.html", {"form": form})


def deleteRemainder(request, pk):
    remainder = Remainder.objects.get(id=pk)
    remainder.delete()
    Activity.objects.create(
        author=remainder.author,
        title="Deleted Remainder",
        body=f"Deleted Remainder with title of: {remainder.title}",
    )
    messages.success(request, "Remainder deleted successfully!")
    return redirect("home")


def create_notebook(request):
    logged_in_profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        print("POST")
        form = NotebookForm(request.POST)
        if form.is_valid():
            try:
                notebook = form.save(commit=False)
                notebook.author = logged_in_profile
                notebook.save()
                # Create new activity
                Activity.objects.create(
                    author=logged_in_profile,
                    title="Created New Notebook",
                    body=f"Created new Notebook with title of: {notebook.title}",
                )
                messages.success(request, "Notebook created successfully!")
                return redirect(
                    "create_page", pk=notebook.pk
                )  # Redirect to create page with the new notebook's pk
            except IntegrityError:
                # Handle IntegrityError if needed
                pass
    else:
        form = NotebookForm()
    return render(request, "create_notebook.html", {"form": form})


def notebook_form(request, notebook_uuid=None, notebook_id=None):
    """Handles both creating and updating a notebook in a single template."""
    notebook = None
    logged_in_profile = Profile.objects.get(user=request.user)
    if notebook_id:
        notebook = get_object_or_404(Notebook, id=notebook_id)

    if notebook_uuid:
        notebook = get_object_or_404(Notebook, notebook_uuid=notebook_uuid)

    if request.method == "POST":
        if notebook:
            # Update notebook
            notebook.title = request.POST.get("title", notebook.title)
            notebook.body = request.POST.get("body", notebook.body)
            notebook.priority = int(request.POST.get("priority", notebook.priority))
            notebook.is_password_protected = (
                request.POST.get("is_password_protected") == "on"
            )
            notebook.author = logged_in_profile
            if notebook.is_password_protected:
                _password = request.POST.get("password")
                if _password:
                    notebook.password = make_password(_password)
            else:
                notebook.password = ""  # Clear password if checkbox is unchecked

            notebook.save()
            return JsonResponse({"status": "saved", "title": notebook.title})

        else:
            # Create new notebook
            title = request.POST.get("title", "Untitled")
            body = request.POST.get("body", "")
            priority = request.POST.get("priority", 1)
            is_password_protected = request.POST.get("is_password_protected") == "on"
            password = request.POST.get("password", "") if is_password_protected else ""
            

            new_notebook = Notebook.objects.create(
                title=title,
                body=body,
                priority=priority,
                is_password_protected=is_password_protected,
                password=make_password(password),
                author=logged_in_profile,
            )
            # Do not remove this
            # new_page = Page.objects.create(title="Page", body="Dummy Body", notebook=new_notebook, author=logged_in_profile)
            # Do not remove this ^
            return JsonResponse({"redirect": f"/notebook/{new_notebook.notebook_uuid}/"})

    return render(request, "notebook_form.html", {"notebook": notebook})


def page_form(request, page_pk=None, notebook_pk=None, page_uuid=None, notebook_uuid=None):
    """Handles both creating and updating a notebook in a single template."""
    page = None
    notebook = None
    logged_in_profile = Profile.objects.get(user=request.user)
    if notebook_pk:
        notebook = get_object_or_404(Notebook, id=notebook_pk)
    if page_pk:
        page = get_object_or_404(Page, id=page_pk)
    if notebook_uuid:
        notebook = get_object_or_404(Notebook, notebook_uuid=notebook_uuid)
    if page_uuid:
        page = get_object_or_404(Page, page_uuid=page_uuid)

    if request.method == "POST":
        if page:
            # Update notebook
            page.title = request.POST.get("title", page.title)
            page.body = request.POST.get("body", page.body)
            page.order = request.POST.get("order", page.order)

            page.save()
            return JsonResponse(
                {"status": "saved", "title": page.title, "body": page.body}
            )

        elif notebook:
            # Create new notebook
            title = request.POST.get("title", "Untitled")
            body = request.POST.get("body", "")
            order = request.POST.get("order", 1)

            new_page = Page.objects.create(
                title=title,
                body=body,
                notebook=notebook,
                order=order,
                author=logged_in_profile,
            )
            return JsonResponse({"redirect": f"/page/{new_page.page_uuid}/"})

    return render(request, "page_form.html", {"page": page, "notebook": notebook})


def autosave_notebook(request, notebook_uuid):
    """Handles autosaving the notebook fields."""
    if request.method == "POST":
        # notebook_id = request.POST.get("notebook_id")
        notebook = get_object_or_404(Notebook, notebook_uuid=notebook_uuid)

        # Update fields
        notebook.title = request.POST.get("title", notebook.title)
        notebook.priority = request.POST.get("priority", notebook.priority)
        notebook.body = request.POST.get("body", notebook.body)
        notebook.is_password_protected = (
            request.POST.get("is_password_protected", "off") == "on"
        )
        notebook.password = request.POST.get("password", notebook.password)

        # Save the updated notebook
        notebook.save()
        return JsonResponse(
            {"message": "Saved!"},
            status=200,
            safe=False,
            headers={"HX-Trigger": "noteSaved"},
        )

    return JsonResponse({"message": "Error"}, status=400)


def autosave_page(request, page_uuid):
    """Handles autosaving the page fields."""
    if request.method == "POST":
        # notebook_id = request.POST.get("notebook_id")
        page = get_object_or_404(Page, page_uuid=page_uuid)

        # Update fields
        page.title = request.POST.get("title", page.title)
        page.body = request.POST.get("body", page.body)
        page.order = request.POST.get("order", page.order)

        # Save the updated notebook
        page.save()
        return JsonResponse(
            {"message": "Saved!"},
            status=200,
            safe=False,
            headers={"HX-Trigger": "noteSaved"},
        )

    return JsonResponse({"message": "Error"}, status=400)


@csrf_exempt
def update_page_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        notebook_id = data.get("notebook_id")

        if not notebook_id:
            return JsonResponse(
                {"status": "error", "message": "Notebook ID missing"}, status=400
            )

        for page_data in data["pages"]:
            Page.objects.filter(id=page_data["id"], notebook_id=notebook_id).update(
                order=page_data["order"]
            )

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


def create_page(request, pk):
    notebook = Notebook.objects.get(id=pk)
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.notebook = notebook
            page.author = logined_profile
            page.save()
            # Create new activity
            Activity.objects.create(
                author=logined_profile,
                title="Created New Page",
                body=f"Created new Page for notebook with title of: {notebook.title}",
            )
            messages.success(request, "Page created successfully!")
            return redirect("home")  # Redirect to home or any other page
    else:
        form = PageForm()
    return render(request, "page_create.html", {"form": form})


def create_subpage(request, notebook_pk: int, page_pk: int):
    notebook = Notebook.objects.get(id=notebook_pk)
    page = Page.objects.get(id=page_pk)
    logined_profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = SubPageForm(request.POST)
        if form.is_valid():
            subpage = form.save(commit=False)
            subpage.notebook = notebook
            subpage.author = logined_profile
            subpage.page = page
            subpage.save()
            # Create new activity
            Activity.objects.create(
                author=logined_profile,
                title="Created New Subpage",
                body=f"Created new Subpage for page with title of: {page.title}",
            )
            messages.success(request, "Sub-Page created successfully!")
            return redirect("home")  # Redirect to home or any other page
    else:
        form = SubPageForm()
    return render(request, "sub_page_create.html", {"form": form})


def subpage_form(request, subpage_pk=None, notebook_pk=None, page_pk=None, subpage_uuid=None, page_uuid=None, notebook_uuid=None):
    """Handles both creating and updating a subpage, allowing updates with just subpage_pk."""

    subpage = None
    notebook = None
    page = None
    logined_profile = get_object_or_404(Profile, user=request.user)

    # If subpage_pk is provided, fetch its related notebook and page automatically
    if subpage_pk:
        subpage = get_object_or_404(SubPage, id=subpage_pk)
        notebook = subpage.notebook
        page = subpage.page
    elif subpage_uuid:
        subpage = get_object_or_404(SubPage, subpage_uuid=subpage_uuid)
        notebook = subpage.notebook
        page = subpage.page
    else:
        if (not notebook_pk and not notebook_uuid) or (not page_pk and not page_uuid):
            return redirect("home")
        
        # print("Notebook uuid: ", notebook_uuid)
        # notebook = get_object_or_404(Notebook, notebook_uuid=notebook_uuid)
        # page = get_object_or_404(Page, page_uuid=page_uuid)
        notebook = get_object_or_404(Notebook, notebook_uuid=notebook_uuid) if notebook_uuid else get_object_or_404(Notebook, id=notebook_pk)
        page = get_object_or_404(Page, page_uuid=page_uuid) if page_uuid else get_object_or_404(Page, id=page_pk)

    if not notebook or not page:
        return redirect("home")

    if request.method == "POST":
        if subpage:
            # Update existing subpage
            subpage.title = request.POST.get("title", subpage.title)
            subpage.body = request.POST.get("body", subpage.body)
            subpage.save()

            if request.headers.get("HX-Request"):
                return JsonResponse({"status": "saved", "title": subpage.title})
            return redirect("update_sub_page_by_uuid", subpage_uuid=subpage.subpage_uuid)

        else:
            # Create new subpage
            title = request.POST.get("title", "Untitled")
            body = request.POST.get("body", "")

            new_subpage = SubPage.objects.create(
                title=title,
                body=body,
                notebook=notebook,
                page=page,
                author=logined_profile,
            )

            # Save last created subpage in session for redirection

            Activity.objects.create(
                author=logined_profile,
                title="Created New Subpage",
                body=f"Created a new subpage under {new_subpage.title}",
            )

            if request.headers.get("HX-Request"):
                return JsonResponse(
                    {
                        "redirect": reverse(
                            "update_sub_page_by_uuid", kwargs={"subpage_uuid": new_subpage.subpage_uuid}
                        )
                    }
                )
            return redirect("update_sub_page_by_uuid", subpage_uuid=new_subpage.subpage_uuid)

    return render(
        request,
        "subpage_form.html",
        {"subpage": subpage, "page": page, "notebook": notebook},
    )


def autosave_subpage(request, subpage_uuid):
    """Handles autosaving the Subpage fields."""
    if request.method == "POST":
        # notebook_id = request.POST.get("notebook_id")
        subPage = get_object_or_404(SubPage, subpage_uuid=subpage_uuid)

        # Update fields
        subPage.title = request.POST.get("title", subPage.title)
        subPage.body = request.POST.get("body", subPage.body)

        # Save the updated notebook
        subPage.save()
        return JsonResponse(
            {"message": "Saved!"},
            status=200,
            safe=False,
            headers={"HX-Trigger": "noteSaved"},
        )

    return JsonResponse({"message": "Error"}, status=400)


def remainder_form(request, remainder_pk=None):
    """Handles both creating and updating a reminder in a single template."""
    logined_profile = Profile.objects.get(user=request.user)
    remainder = None

    # If editing, fetch the existing remainder
    if remainder_pk:
        remainder = get_object_or_404(
            Remainder, id=remainder_pk, author=logined_profile
        )

    if request.method == "POST":
        title = request.POST.get("title", remainder.title if remainder else "Untitled")
        body = request.POST.get("body", remainder.body if remainder else "")
        is_favourite = request.POST.get("is_favourite", "false") == "true"
        is_completed = request.POST.get("is_completed", "false") == "true"

        # Convert alert_time from string to datetime (Handle empty value)
        alert_time_str = request.POST.get("alert_time", "")
        try:
            # alert_time = (
            #     datetime.datetime.strptime(alert_time_str, "%Y-%m-%dT%H:%M")
            #     if alert_time_str
            #     else timezone.now()
            # )
            alert_time = (
                datetime.datetime.strptime(alert_time_str, "%Y-%m-%dT%H:%M")
                if alert_time_str
                else timezone.now()
            )
            if timezone.is_naive(alert_time):
                alert_time = timezone.make_aware(alert_time, timezone.get_current_timezone())
        except ValueError:
            alert_time = timezone.now()  # Fallback to current time if invalid

        if remainder:
            # Update existing remainder
            remainder.title = title
            remainder.body = body
            remainder.alert_time = alert_time
            remainder.is_favourite = is_favourite
            remainder.is_completed = is_completed
            remainder.save()
            messages.success(request, "Reminder updated successfully!")
            return JsonResponse(
                {
                    "status": "saved",
                    "title": remainder.title,
                    "body": remainder.body,
                    "alert_time": remainder.alert_time,
                }
            )

        else:
            # Create new remainder
            new_remainder = Remainder(
                title=title,
                body=body,
                alert_time=alert_time,
                is_favourite=is_favourite,
                is_completed=is_completed,
                author=logined_profile,
            )
            new_remainder.save()
            messages.success(request, "Reminder created successfully!")
            # return JsonResponse({"redirect": f"/remainder/{new_remainder.id}/"})
            # ✅ Conditional redirect based on HTMX/AJAX header
            if request.headers.get("HX-Request"):
                return JsonResponse({
                    "redirect": reverse("update_reminder", kwargs={"remainder_pk": new_remainder.pk})
                })

            # ✅ Standard redirect
            return redirect("update_reminder", remainder_pk=new_remainder.pk)

    return render(request, "remainder_form.html", {"remainder": remainder})


def autosave_reminder(request, remainder_pk):
    """Autosaves a reminder's title, body, alert time, and status."""
    if request.method == "POST":
        logined_profile = Profile.objects.get(user=request.user)
        remainder = get_object_or_404(
            Remainder, id=remainder_pk, author=logined_profile
        )

        # Get updated fields from request
        title = request.POST.get("title", remainder.title)
        body = request.POST.get("body", remainder.body)
        is_favourite = request.POST.get("is_favourite", "false") == "true"
        is_completed = request.POST.get("is_completed", "false") == "true"

        # Convert alert_time from string to datetime
        alert_time_str = request.POST.get("alert_time", None)
        try:
            alert_time = (
                datetime.datetime.strptime(alert_time_str, "%Y-%m-%dT%H:%M")
                if alert_time_str
                else remainder.alert_time
            )
            alert_time = timezone.make_aware(
                alert_time, timezone.get_current_timezone()
            )  # Make it timezone-aware
        except (ValueError, TypeError):
            alert_time = remainder.alert_time  # Fallback if invalid format

        # Update only if values have changed
        updated = False
        if remainder.title != title:
            remainder.title = title
            updated = True
        if remainder.body != body:
            remainder.body = body
            updated = True
        if remainder.alert_time != alert_time:
            remainder.alert_time = alert_time
            updated = True
        if remainder.is_favourite != is_favourite:
            remainder.is_favourite = is_favourite
            updated = True
        if remainder.is_completed != is_completed:
            remainder.is_completed = is_completed
            updated = True

        if updated:
            remainder.save()
            return HttpResponse("Saved")
        else:
            return HttpResponse("")  # No updates needed

    return HttpResponse("Invalid request", status=400)


def autosave_sticky_notes(request, stickynote_id):
    """Autosaves a user's sticky note when updated."""
    if request.method == "POST":
        logined_profile = Profile.objects.get(user=request.user)
        stickynote = get_object_or_404(
            StickyNotes, id=stickynote_id, author=logined_profile
        )

        # Redirect if user visits this URL directly
        if not request.headers.get("HX-Request"):
            return HttpResponseRedirect(
                f"/stickynote/{stickynote.id}/"
            )  # Redirect to correct page

        title = request.POST.get("title", stickynote.title)
        body = request.POST.get("body", stickynote.body)

        updated = False
        if stickynote.title != title:
            stickynote.title = title
            updated = True
        if stickynote.body != body:
            stickynote.body = body
            updated = True

        if updated:
            stickynote.save()
            return HttpResponse("Saved")
        else:
            return HttpResponse("")  # No updates needed

    return HttpResponse("Invalid request", status=400)


@login_required
def search(request):
    user = Profile.objects.get(user=request.user)  # Get the logged-in user

    query = request.GET.get("query", "")  # Get the query parameter from the URL
    results = {}

    if query:
        # Search Notebooks created by the logged-in user
        notebook_results = Notebook.objects.filter(
            Q(title__icontains=query)
            | Q(body__icontains=query)
            | Q(priority__icontains=query)
            | Q(is_favourite__icontains=query),
            author=user,
        )

        # Search Pages created by the logged-in user and include the related Notebook for breadcrumbs
        page_results = Page.objects.filter(
            Q(title__icontains=query) | Q(body__icontains=query), notebook__author=user
        ).select_related("notebook")

        # Adjusting results to include breadcrumb style output and subpage searching
        pages_with_breadcrumbs = []
        for page in page_results:
            page_data = {
                "breadcrumb": f"{page.notebook.title} > {page.title}",
                "detail": page,
                "subpages": [],
            }  # Initialize 'subpages' as an empty list
            subpage_results = SubPage.objects.filter(
                Q(title__icontains=query) | Q(body__icontains=query), page=page
            )
            for subpage in subpage_results:
                page_data["subpages"].append(subpage)
            pages_with_breadcrumbs.append(page_data)

        # Search Remainders created by the logged-in user
        remainder_results = Remainder.objects.filter(
            Q(title__icontains=query)
            | Q(body__icontains=query)
            | Q(is_favourite__icontains=query),
            author=user,
        )

        results = {
            "notebooks": notebook_results,
            "pages": pages_with_breadcrumbs,
            "remainders": remainder_results,
        }
    else:
        results = {}

    return render(request, "search.html", {"query": query, "results": results})


def GeneratePdf(request, pk):
    context = {}
    # add the dictionary during initialization
    notebook = Notebook.objects.get(pk=pk)
    page = Page.objects.filter(notebook=notebook)
    subpage = SubPage.objects.filter(page__in=page)
    context["notebook"] = notebook
    context["pages"] = page
    context["subpages"] = subpage
    # getting the template
    pdf = render_to_pdf("pdf_template.html", context)

    # rendering the template
    return HttpResponse(pdf, content_type="application/pdf")


# def verify_password(request, pk):
#     if request.method == 'POST':
#         notebook = Notebook.objects.get(pk = pk)
#         password = request.POST.get('notebook_password')
#         print(str(notebook.password)+" "+str(password))
#         if notebook.password == password:
#             notebook.is_password_entered = True
#             print(notebook.is_password_entered)
#             notebook.save()
#             return redirect('password_protected_notebook', pk=pk)
#         else:
#             return redirect('home')
#     else:
#         context = {}
#     return render(request, 'verify.html', context)
def verify_password(request, pk):
    notebook = get_object_or_404(Notebook, pk=pk)

    if request.method == "POST":
        password = request.POST.get("notebook_password")
        print(f"Entered Password: {password}")
        print(f"Stored Hashed Password: {notebook.password}")

        # Debugging: Check if password matches
        password_match = check_password(password, notebook.password)
        print(f"Password Match: {password_match}")

        if password_match:
            notebook.is_password_entered = True
            notebook.save()
            messages.success(request, "Notebook unlocked successfully!")
            return redirect("password_protected_notebook", pk=pk)
        else:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect("verify_password", pk=pk)

    return render(request, "verify.html", {"notebook": notebook})

def password_protected_notebook(request, pk):
    notebook = Notebook.objects.get(pk=pk)
    pages = Page.objects.filter(notebook=notebook)
    if notebook.is_password_entered == True and notebook.is_password_protected == True:
        notebook.is_accessed_recently = True
        notebook.save()
        context = {}
        context["notebook"] = Notebook.objects.get(pk=pk)
        context["pages"] = Page.objects.filter(notebook=notebook)
        context["subpages"] = SubPage.objects.filter(page__in=pages)
        context["logined_profile"] = Profile.objects.get(user=request.user)
    else:
        context = {}
    return render(request, "password_protected_notebook.html", context)


def notebook_password_reset_page(request, pk):
    notebook = Notebook.objects.get(pk=pk)
    context = {}
    context["notebook"] = notebook
    return render(request, "notebook_password_reset_page.html", context)


def activity_loader(request):
    """Loads the HTMX-powered activity page"""
    request.session["page"] = "activity"
    return render(request, "activities/activity_loader.html")


def activity_page(request):
    """Fetches activity content asynchronously"""
    request.session["page"] = "activity"
    logged_in_profile = Profile.objects.get(user=request.user)
    activities = Activity.objects.filter(author=logged_in_profile).order_by(
        "-updated_at"
    )

    paginator = Paginator(activities, 10)
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Default to first page
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, "activities/activity_history.html", {"activities": page_obj})


def delete_activity_request(request):
    """Handles the activity deletion request"""
    if request.method == "POST":
        logged_in_profile = Profile.objects.get(user=request.user)
        Activity.objects.filter(author=logged_in_profile).delete()
        messages.success(
            request, "✅ All activity logs have been deleted successfully!"
        )

        # Return a message response (HTMX will insert this into #delete-message)
        return HttpResponse(
            '<div class="alert alert-success">✅ All activity logs have been deleted successfully!</div>'
        )

    return HttpResponse(
        '<div class="alert alert-danger">❌ Invalid request.</div>', status=400
    )


@login_required
def request_notebook_password_reset(request, notebook_id):
    logged_in_profile = Profile.objects.get(user=request.user)
    notebook = get_object_or_404(Notebook, id=notebook_id, author=logged_in_profile)

    # Generate a reset link
    reset_link = request.build_absolute_uri(
        reverse("reset_notebook_password", args=[notebook.id])
    )
    print(reset_link)
    if project_settings.DEBUG is False:
        send_email(
            to_email=request.user.email,
            subject="Reset Your Notebook Password",
            title="Reset Your Notebook Password",
            body=f"Click the link below to reset your notebook password.",
            anchor_link=reset_link,
            anchor_text="Reset Password",
        )
    # Send email with reset link
    # subject = "Reset Your Notebook Password"
    # text_content = f"Click the link to reset your notebook password: {reset_link}"
    # html_content = f"""
    # <p>You requested to reset your notebook password.</p>
    # <p>Click the button below to reset it:</p>
    # <p><a href="{reset_link}" style="padding: 10px; background-color: #0076d1; color: white; text-decoration: none;">Reset Password</a></p>
    # """

    # msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [request.user.email])
    # msg.attach_alternative(html_content, "text/html")
    # msg.send()

    messages.success(request, "Password reset link sent to your email.")
    return redirect("home")


@login_required
def reset_notebook_password(request, notebook_id):
    logged_in_profile = Profile.objects.get(user=request.user)
    notebook = get_object_or_404(Notebook, id=notebook_id, author=logged_in_profile)

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_notebook_password", notebook_id=notebook.id)

        # ✅ Hash the new password before saving
        print(new_password)
        print(make_password(new_password))
        notebook.password = make_password(new_password)
        notebook.save()

        messages.success(request, "Notebook password has been reset successfully.")
        return redirect("home")

    return render(request, "notebooks/reset_password.html", {"notebook": notebook})


# TODO GROUP
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string # Import render_to_string
from .models import TodoGroup, Todo, Profile # Assuming Profile model for author
import json

# Main Kanban board view
def todo_group_detail(request, group_uuid):
    group = get_object_or_404(TodoGroup, todogroup_uuid=group_uuid, author__user=request.user)
    todos = group.todos.all()
    
    status_groups = {
        "Not Started": [],
        "In Progress": [],
        "Completed": [],
        "On Hold": [],
        "Cancelled": [],
    }

    for todo in todos:
        status_groups[todo.status].append(todo)
    
    return render(request, "todo_group_detail.html", {
        "group": group,
        "status_groups": status_groups,
    })

# Handles adding a new task via HTMX
@csrf_exempt # Use this decorator if you're not using Django's built-in CSRF protection for HTMX posts
def add_task(request, group_uuid):
    if request.method == "POST":
        title = request.POST.get("title")
        priority = request.POST.get("priority") # Even if not displayed, it might be stored
        profile = get_object_or_404(Profile, user=request.user) # Ensure Profile is correctly fetched
        
        todo = Todo.objects.create(
            title=title,
            status="Not Started", # New tasks typically start here
            author = profile,
            priority=priority,
        )
        group = get_object_or_404(TodoGroup, todogroup_uuid=group_uuid, author__user=request.user)
        group.todos.add(todo)
        
        # Render the new todo card HTML as a string and return it directly
        # IMPORTANT: _todo_card.html MUST NOT extend base.html or any other template.
        # It should be a pure HTML snippet for a single todo card.
        rendered_todo_card = render_to_string('partials/_todo_card.html', {'todo': todo}, request=request)
        return HttpResponse(rendered_todo_card)
    return JsonResponse({"error": "Invalid request"}, status=400)


# Handles updating a todo's status via drag-and-drop (HTMX)
@csrf_exempt
def update_todo_status(request):
    if request.method == "POST":
        data = json.loads(request.body)
        todo_uuid = data.get("todo_uuid")
        new_status = data.get("new_status")
        try:
            todo = get_object_or_404(Todo, todo_uuid=todo_uuid, author__user=request.user) 
            todo.status = new_status
            todo.save()
            return JsonResponse({"success": True})
        except Todo.DoesNotExist:
            return JsonResponse({"error": "Todo not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)


# Handles editing a task's title via HTMX
@csrf_exempt
def edit_task(request, todo_uuid):
    if request.method == "POST":
        todo = get_object_or_404(Todo, todo_uuid=todo_uuid, author__user=request.user)
        todo.title = request.POST["title"]
        # If you decide to re-add priority to the UI, uncomment this:
        # todo.priority = request.POST.get("priority", todo.priority) 
        todo.save()
        # Render the updated todo card HTML as a string and return it directly
        rendered_todo_card = render_to_string('partials/_todo_card.html', {'todo': todo}, request=request)
        return HttpResponse(rendered_todo_card)
    return JsonResponse({"error": "Invalid request"}, status=400)


# Handles deleting a task via HTMX
@csrf_exempt
def delete_task(request, todo_uuid):
    if request.method == "POST":
        todo = get_object_or_404(Todo, todo_uuid=todo_uuid, author__user=request.user)
        todo.delete()
        # Return an empty HttpResponse for HTMX to remove the element
        # return HttpResponse(status=204) # 204 No Content is a good status for successful deletion
        return HttpResponse("<p>Deleted</p>", content_type="text/html")  # Return empty content, not 204
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def create_todo_group(request):
    if request.method == "POST":
        title = request.POST.get("title")
        profile = Profile.objects.get(user=request.user)

        group = TodoGroup.objects.create(
            title=title,
            author=profile
        )
        group.not_viewed_count = 0  # dummy default

        html = render_to_string("partials/todo_group_card.html", {"group": group})
        return HttpResponse(html)
    return JsonResponse({"error": "Invalid request"}, status=400)

def stopSharingTodoGroup(request, pk):
    with transaction.atomic():  # Ensures everything commits or rolls back
        todoGroup = get_object_or_404(TodoGroup, id=pk)

        # Force refresh from DB
        todoGroup.refresh_from_db()

        # Clear shared users
        todoGroup.shared_with.clear()
        todoGroup.save()

        # Log Activity
        Activity.objects.create(
            author=todoGroup.owner,
            title="Stopped Sharing",
            body=f"Stopped sharing todo group with title: {todoGroup.title}",
        )

    messages.success(request, "Todo group sharing has been stopped successfully!")
    return redirect("home")


def startSharingTodoGroup(request, pk):
    todoGroup = get_object_or_404(TodoGroup, id=pk)
    logined_profile = get_object_or_404(Profile, user=request.user)

    if todoGroup.author != logined_profile:
        messages.error(request, "You do not have permission to share this todo group.")
        return redirect("home")

    if request.method == "POST":
        shared_emails = request.POST.get("shared_to_emails", "").strip()

        if shared_emails:
            email_list = [
                email.strip() for email in shared_emails.split(",") if email.strip()
            ]
            valid_users = []
            invalid_emails = []

            for email in email_list:
                shared_to_user = Profile.objects.filter(email=email).first()
                if shared_to_user:
                    valid_users.append(shared_to_user)
                else:
                    invalid_emails.append(email)

            if valid_users:
                todoGroup.shared_with.add(*valid_users)
                todoGroup.save()
                messages.success(
                    request,
                    f"Todo group shared successfully with {', '.join([user.email for user in valid_users])}!",
                )

            if invalid_emails:
                messages.warning(
                    request, f"These emails are invalid: {', '.join(invalid_emails)}"
                )

        else:
            todoGroup.shared_with.clear()
            todoGroup.save()
            messages.success(request, "Todo group has been made public!")

        return redirect("home")

    return redirect("home")