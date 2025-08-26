from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models_folder.post_models import  Post, PostMedia, Hashtag, Comment
from accounts.models_folder.notifications_models import  Notification


@login_required(login_url='login_page')
def LikePostView(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    
    if user in post.likes.all():
        post.likes.remove(user)  # Unlike if already liked
    else:
        post.likes.add(user)  # Like the post
        
        # crating Notification for post owner
        if post.user != user:
            Notification.objects.create(
                sender=user,
                receiver=post.user,
                notification_type='like',
                post=post
            )

    return redirect(request.META.get('HTTP_REFERER', 'home_page'))

@login_required(login_url='login_page')
def AddCommentView(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    parent_id = request.POST.get("parent_id")  

    if request.method == "POST":
        text = request.POST.get("text")
        user = request.user
        if text:
            parent_comment = None
            if parent_id:
                parent_comment = Comment.objects.get(id=parent_id)  
            
            comment = Comment.objects.create(
                user=user,
                post=post,
                text=text,
                parent=parent_comment
            )

            #  Notification  comments on the post
            if parent_comment is None and post.user != user: 
                 
                Notification.objects.create(
                    sender=user,
                    receiver=post.user,
                    notification_type="comment",
                    post=post
                )

            # Notification for replies to a comment
            if parent_comment is not None and parent_comment.user != user:  
                Notification.objects.create(
                    sender=user,
                    receiver=parent_comment.user,
                    notification_type="reply",
                    comment=parent_comment
                )

            messages.success(request, "Comment added successfully!")

    return redirect("home_page")

@login_required(login_url='login_page')
def DeleteCommentView(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if the logged-in user is the owner of the comment
    if request.user == comment.user:
        comment.delete()
        messages.success(request, "Comment deleted successfully!")
    else:
        messages.error(request, "You are not allowed to delete this comment.")

    return redirect("home_page")  # Redirect to the homepage after deletion


@login_required(login_url='login_page')
def EditCommentView(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)  # Ensure user owns comment

    if request.method == "POST":
        new_text = request.POST.get("text")
        if new_text:
            comment.text = new_text
            comment.save()
            messages.success(request, "Comment updated successfully!")
            return redirect("home_page")

    return render(request, "posts/edit_comment.html", {"comment": comment})

@login_required(login_url='login_page')
def EditReplyView(request, reply_id):
    reply = get_object_or_404(Comment, id=reply_id, user=request.user)  # Ensure user owns reply

    if request.method == "POST":
        new_text = request.POST.get("reply_text")
        if new_text:
            reply.text = new_text
            reply.save()
            messages.success(request, "Reply updated successfully!")
            return redirect("home_page")

    return render(request, "posts/edit_reply.html", {"reply": reply})


@login_required(login_url='login_page')
def DeleteReplyView(request, reply_id):
    reply = get_object_or_404(Comment, id=reply_id, user=request.user)  # Ensure user owns the reply

    if request.method == "POST":
        reply.delete()
        messages.success(request, "Reply deleted successfully!")
        return redirect("home_page")  # Redirect to the home page after deletion

    return render(request, "posts/delete_reply.html", {"reply": reply})
