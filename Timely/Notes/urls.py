from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path("", login_required(views.index), name="home"),
    path('create-notebook/', login_required(views.create_notebook), name='create_notebook'),
    path('create-remainder/', login_required(views.create_remainder), name='create_remainder'),
    path('create-page/<int:pk>/', login_required(views.create_page), name='create_page'),
    path('create_subpage/<int:notebook_pk>/<int:page_pk>/', login_required(views.create_subpage), name='create_subpage'),
    path('update_sticky_notes/<int:pk>/', login_required(views.updateStickyNotes), name='update_sticky_notes'),
    path('update_reminder/<int:pk>/', login_required(views.update_reminder), name='update_reminder'),
    path('update-notebook/<int:pk>/', login_required(views.update_notebook_modal), name='update_notebook'),
    path('update-page/<int:pk>/', login_required(views.update_page_modal), name='update_page'),
    path('update_sub_page/<int:pk>/', login_required(views.update_sub_page_modal), name='update_sub_page'),
    path('deleteNotebook/<int:pk>/', login_required(views.deleteNotebook), name='deleteNotebook'),
    path('deletePage/<int:pk>/', login_required(views.deletePage), name='deletePage'),
    path('deleteSubPage/<int:pk>/', login_required(views.deleteSubPage), name='deleteSubPage'),
    path('deleteRemainder/<int:pk>/', login_required(views.deleteRemainder), name='deleteRemainder'),
    path('search/', login_required(views.search), name='search'),
    path('password_protected/<int:pk>', login_required(views.verify_password), name='verify_password'),
    path('password_protected_notebook/<int:pk>', login_required(views.password_protected_notebook), name='password_protected_notebook'),
    path('forgot_password_notebook/<int:pk>/', login_required(views.notebook_password_reset_page), name='forgot_password'),
    path('favourites/add/<int:pk>/', login_required(views.addToFavourites), name='addToFavourites'),
    path('favourites/remove/<int:pk>/', login_required(views.removeToFavourites), name='removeToFavourites'),
    path('sharedNotebooks/<int:pk>/', views.shared_notebooks_view, name='sharedNotebooks'),
    path('startSharingNotebooks/<int:pk>/', login_required(views.startSharingNotebook), name='startingSharedNotebooks'),
    path('stopSharingNotebook/<int:pk>/', login_required(views.stopSharingNotebook), name='stopSharingNotebook'),
    path('deleteAllActivities/', login_required(views.deleteAllActivities), name='deleteAllActivities'),
    path('incrementPriority/<int:pk>/', login_required(views.incrementPriority), name='incrementPriority'),
    path('decrementPriority/<int:pk>/', login_required(views.decrementPriority), name='decrementPriority'),
    path('generate_pdf/<int:pk>/', login_required(views.GeneratePdf), name='generate_pdf'),  
    path('mark_as_complete/<int:pk>/', login_required(views.markReminderComplete), name='markReminderComplete'),
    path('mark_as_uncomplete/<int:pk>/', login_required(views.markReminderUnComplete), name='markReminderUnComplete'),
    path('mark_as_favourite/<int:pk>/', login_required(views.markReminderFavourite), name='markReminderFavourite'),
    path('mark_as_not_favourite/<int:pk>/', login_required(views.markReminderUnFavourite), name='markReminderUnFavourite'), 
    path('exportNotebookToJson/<int:pk>/', login_required(views.exportNotebookToJson), name='exportNotebookToJson'), 
    path('loadJsonToModels/', login_required(views.loadJsonToModels), name='loadJsonToModels'), 

]
