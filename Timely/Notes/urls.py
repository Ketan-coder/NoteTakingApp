from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", login_required(views.index), name="home"),
    path(
        "fetching-contents/notebook/<int:notebook_id>/",
        login_required(views.fetch_notebook_contents),
        name="fetch_notebook_notebook",
    ),
    path(
        "fetching-contents/page/<int:page_id>/",
        login_required(views.fetch_notebook_contents),
        name="fetch_notebook_pages",
    ),
    path(
        "fetching-contents/subpage/<int:subpage_id>/",
        login_required(views.fetch_notebook_contents),
        name="fetch_notebook_subpages",
    ),
    path('fetching-contents/notebook/<uuid:notebook_uuid>/', login_required(views.fetch_notebook_contents), name='fetch_notebook_by_uuid'),
    path('fetching-contents/page/<uuid:page_uuid>/', login_required(views.fetch_notebook_contents), name='fetch_page_by_uuid'),
    path('fetching-contents/subpage/<uuid:subpage_uuid>/', login_required(views.fetch_notebook_contents), name='fetch_subpage_by_uuid'),
    path(
        "create-notebook/", login_required(views.notebook_form), name="create_notebook"
    ),
    path(
        "notebook/<int:notebook_id>/",
        login_required(views.notebook_form),
        name="update_notebook",
    ),
    path(
        "notebook/<uuid:notebook_uuid>/",
        login_required(views.notebook_form),
        name="update_notebook_by_uuid",
    ),
    path(
        "autosave/<uuid:notebook_uuid>/",
        login_required(views.autosave_notebook),
        name="autosave_notebook",
    ),
    path(
        "create-page/<int:notebook_pk>/",
        login_required(views.page_form),
        name="create_page",
    ),
    path(
        "create-page/<uuid:notebook_uuid>/",
        login_required(views.page_form),
        name="create_page_by_uuid",
    ),
    path("page/<int:page_pk>/", login_required(views.page_form), name="update_page"),
    path("page/<uuid:page_uuid>/", login_required(views.page_form), name="update_page_by_uuid"),
    path(
        "update-page-order/",
        login_required(views.update_page_order),
        name="update_page_order",
    ),
    path(
        "autosave/page/<uuid:page_uuid>/",
        login_required(views.autosave_page),
        name="autosave_page",
    ),
    path(
        "autosave/subpage/<uuid:subpage_uuid>/",
        login_required(views.autosave_subpage),
        name="autosave_subpage",
    ),
    path(
        "create-remainder/",
        login_required(views.remainder_form),
        name="create_remainder",
    ),
    # path('create-page/<int:pk>/', login_required(views.create_page), name='create_page'),
    path(
        "create_subpage/<int:notebook_pk>/<int:page_pk>/",
        login_required(views.subpage_form),
        name="create_subpage",
    ),
    path(
        "create_subpage/<uuid:notebook_uuid>/<uuid:page_uuid>/",
        login_required(views.subpage_form),
        name="create_subpage_by_uuid",
    ),
    path(
        "sticky_notes/<int:pk>/",
        login_required(views.updateStickyNotes),
        name="update_sticky_notes",
    ),
    path(
        "autosave/sticky_notes/<int:stickynote_id>/",
        login_required(views.autosave_sticky_notes),
        name="autosave_sticky_notes",
    ),
    path(
        "reminder/<int:remainder_pk>/",
        login_required(views.remainder_form),
        name="update_reminder",
    ),
    path(
        "autosave/reminder/<int:remainder_pk>/",
        login_required(views.autosave_reminder),
        name="autosave_reminder",
    ),
    # path('update-page/<int:pk>/', login_required(views.update_page_modal), name='update_page'),
    path(
        "update_sub_page/<int:subpage_pk>/",
        login_required(views.subpage_form),
        name="update_sub_page",
    ),
    path(
        "update_sub_page/<uuid:subpage_uuid>/",
        login_required(views.subpage_form),
        name="update_sub_page_by_uuid",
    ),
    path(
        "deleteNotebook/<int:pk>/",
        login_required(views.deleteNotebook),
        name="deleteNotebook",
    ),
    path("deletePage/<int:pk>/", login_required(views.deletePage), name="deletePage"),
    path(
        "deleteSubPage/<int:pk>/",
        login_required(views.deleteSubPage),
        name="deleteSubPage",
    ),
    path(
        "deleteRemainder/<int:pk>/",
        login_required(views.deleteRemainder),
        name="deleteRemainder",
    ),
    path("search/", login_required(views.search), name="search"),
    path(
        "password_protected/<int:pk>",
        login_required(views.verify_password),
        name="verify_password",
    ),
    path(
        "password_protected_notebook/<int:pk>",
        login_required(views.password_protected_notebook),
        name="password_protected_notebook",
    ),
    path(
        "forgot_password_notebook/<int:pk>/",
        login_required(views.notebook_password_reset_page),
        name="forgot_password",
    ),
    path(
        "favourites/add/<int:pk>/",
        login_required(views.addToFavourites),
        name="addToFavourites",
    ),
    path(
        "favourites/remove/<int:pk>/",
        login_required(views.removeToFavourites),
        name="removeToFavourites",
    ),
    path("sharedNotebooks/", views.shared_notebooks_view, name="sharedNotebooks"),
    path("publicNotebooks/", views.public_notebooks_view, name="publicNotebooks"),
    path(
        "startSharingNotebooks/<int:pk>/",
        login_required(views.startSharingNotebook),
        name="startingSharedNotebooks",
    ),
    path(
        "stopSharingNotebook/<int:pk>/",
        login_required(views.stopSharingNotebook),
        name="stopSharingNotebook",
    ),
    path(
        "deleteAllActivities/",
        login_required(views.deleteAllActivities),
        name="deleteAllActivities",
    ),
    path(
        "incrementPriority/<int:pk>/",
        login_required(views.incrementPriority),
        name="incrementPriority",
    ),
    path(
        "decrementPriority/<int:pk>/",
        login_required(views.decrementPriority),
        name="decrementPriority",
    ),
    path(
        "generate_pdf/<int:pk>/", login_required(views.GeneratePdf), name="generate_pdf"
    ),
    path(
        "mark_as_complete/<int:pk>/",
        login_required(views.markReminderComplete),
        name="markReminderComplete",
    ),
    path(
        "mark_as_uncomplete/<int:pk>/",
        login_required(views.markReminderUnComplete),
        name="markReminderUnComplete",
    ),
    path(
        "mark_as_favourite/<int:pk>/",
        login_required(views.markReminderFavourite),
        name="markReminderFavourite",
    ),
    path(
        "mark_as_not_favourite/<int:pk>/",
        login_required(views.markReminderUnFavourite),
        name="markReminderUnFavourite",
    ),
    path(
        "exportNotebookToJson/<int:pk>/",
        login_required(views.exportNotebookToJson),
        name="exportNotebookToJson",
    ),
    path(
        "loadJsonToModels/",
        login_required(views.loadJsonToModels),
        name="loadJsonToModels",
    ),
    path("todo/add/", login_required(views.add_todo), name="add_todo"),
    path(
        "todo/toggle/<int:todo_id>/",
        login_required(views.toggle_todo),
        name="toggle_todo",
    ),
    path(
        "todo/delete/<int:todo_id>/",
        login_required(views.delete_todo),
        name="delete_todo",
    ),
    path(
        "fetch-profile/",
        login_required(views.fetch_profile_details),
        name="fetch_profile_details",
    ),
    path(
        "activity-loader/",
        login_required(views.activity_loader),
        name="activity_loader",
    ),
    path("activity-page/", login_required(views.activity_page), name="activity_page"),
    path(
        "delete-activity-request/",
        login_required(views.delete_activity_request),
        name="delete_activity_request",
    ),
    path(
        "notebook/<int:notebook_id>/reset-password-request/",
        login_required(views.request_notebook_password_reset),
        name="request_notebook_password_reset",
    ),
    path(
        "notebook/<int:notebook_id>/reset-password/",
        login_required(views.reset_notebook_password),
        name="reset_notebook_password",
    ),

    path("todogroup/<uuid:group_uuid>/", views.todo_group_detail, name="todo_group_detail"),
    path("todo/update-status/", views.update_todo_status, name="update_todo_status"),

    path('todo/<uuid:group_uuid>/add/', views.add_task, name='add_task'),
    path('todo/update-status/', views.update_todo_status, name='update_todo_status'),
    path('todo/<uuid:todo_uuid>/json/', views.todo_json, name='todo_json'),
    path('todo/edit/', views.edit_task, name='edit_task'),
    path('todo/<uuid:todo_uuid>/delete/', views.delete_task, name='delete_task'),

]
