from django.contrib.auth import views as auth_views
from django.urls import path
from .views import home_views as home

from .views import chat_views as chat
from .views import groupchat_views as groupchat
from .views import like_comment_views as like_comment
from .views import notification_views as notification
from .views import post_views as post
from .views import user_views as user
from .views import groupchat_views as group_views

urlpatterns = [
    path("", home.HomeView, name="home_page"),
    path("notification/", home.notification, name="notification_page"),
    
#Authentication Urls
    path("register/",home.RegisterView, name="register_page"),
    path("login/",home.LoginView, name="login_page"),
    path("logout/",home.LogoutView, name="logout_page"),   
    
#Forgot Password
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="authentication/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="authentication/password_reset_done.html"), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="authentication/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="authentication/password_reset_complete.html"), name="password_reset_complete"),
#Password Change
    path("password-change/", auth_views.PasswordChangeView.as_view(template_name="authentication/password_change.html"), name="password_change"),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="authentication/password_change_done.html"), name="password_change_done"),
    

#User Urls
    path('myprofile/', user.ProfileView, name='myprofile_page'),
    path("profileupdate/", user.ProfileUpdateView, name="profile_update_page"),
    path("profile/<str:username>/", user.SearchUserProfile, name="search_profile_page"),
    path('follow/<str:username>/', user.FollowUnfollowView, name='follow_unfollow'),
    path('followrequest/<str:username>/', user.send_follow_request, name='send_follow_request'),
    path('follow/request_accept/<int:req_id>/', user.follow_request_accept, name='follow_request_accept'), 
    path('follow/request_reject/<int:req_id>/', user.follow_request_reject, name='follow_request_reject'),
    path('follow_request_list/', user.follow_request_list, name='follow_request_list'),
    path('profile/<str:username>/followers/', user.FollowerListView, name='followers_list'),
    path('profile/<str:username>/following/', user.FollowingListView, name='following_list'),
    
    
    
# # #Post urls
    path("create_post/",post.CreatePostView, name="create_post_page"),
    path("hashtag/<str:hashtag>/", post.HashtagView, name="hashtag_posts"),
    path('post/<int:post_id>/', post.PostDetailView, name='post_detail'),
    path('post/<int:post_id>/edit/', post.EditPostView, name='edit_post'),
    path('post/<int:post_id>/delete/', post.DeletePostView, name='delete_post'),
    path('download/<int:media_id>/', post.download_post, name='download_post'),


# # #Like_Comment urls
    # path('post/<int:post_id>/like/', like_comment.LikePostView, name='like_post'),
    path('comment/<int:post_id>/', like_comment.AddCommentView, name='add_comment'),
    path("delete-comment/<int:comment_id>/", like_comment.DeleteCommentView, name="delete_comment"),
    path("edit-comment/<int:comment_id>/", like_comment.EditCommentView, name="edit_comment"),
    path("edit-reply/<int:reply_id>/", like_comment.EditReplyView, name="edit_reply"),
    path("delete-reply/<int:reply_id>/", like_comment.DeleteReplyView, name="delete_reply"),
    
    
# Chat Urls
    path("send_message/<str:username>/", chat.chat_view, name="send_message"),
    path("messages_lists/", chat.inbox_view, name="send_message"),
    # path("inbox/", chat.InboxView, name="inbox"),
    # path("conversation/<int:conversation_id>/", chat.ConversationView, name="view_conversation"),
    # path("delete_message/<int:message_id>/", chat.DeleteMessageView, name="delete_message"),
    
#Notification  Urls
    # path('notifications/', notification.NotificationsView, name='notifications_page'),
    # path('notifications/mark-as-read/', notification.NotificationReadView, name='mark_notifications_as_read'),
    path("search/", notification.SearchUserView, name="search_users"),

    # Group Related URLs
    path('groups/', group_views.groups_list, name='groups_list'),
    path('groups/create/', group_views.create_group, name='create_group'),
    path('groups/<int:group_id>/', group_views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/join/', group_views.join_group, name='join_group'),
    path('groups/<int:group_id>/cancel_join/<int:user_id>/', group_views.cancel_join_request, name='cancel_join_request'),
    path('groups/<int:group_id>/leave/', group_views.leave_group, name='leave_group'),
    path('groups/<int:group_id>/add-member/', group_views.add_member, name='add_member'),
    path('groups/<int:group_id>/remove-member/<int:user_id>/', group_views.remove_member, name='remove_member'),
    path('groups/<int:group_id>/promote/<int:user_id>/', group_views.promote_member, name='promote_member'),
    path('groups/<int:group_id>/demote/<int:user_id>/', group_views.demote_member, name='demote_member'),
    path('groups/<int:group_id>/chats/', group_views.group_chat, name='group_chat'),
    path('groups/<int:group_id>/accept_request/<int:request_id>/', group_views.accept_join_request, name='accept_join_request'),
    path('groups/<int:group_id>/reject_request/<int:request_id>/', group_views.reject_join_request, name='reject_join_request'),
]


