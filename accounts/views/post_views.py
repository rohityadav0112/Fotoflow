from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import FileResponse, Http404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.forms import UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm
from accounts.models_folder.post_models import  Post, PostMedia, Hashtag, Comment
from accounts.models_folder.notifications_models import  Notification
import os
from accounts.background_tasks.worker import enqueue_post_task
@login_required(login_url='login_page')
def OldCreatePostView(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

            # Handle multiple media files
            media_files = request.FILES.getlist("media")  # Get multiple files
            for file in media_files:
                PostMedia.objects.create(post=post, file=file)

            return redirect("home_page")

    else:
        form = PostForm()

    return render(request, "posts/create_post.html", {"form": form})


@login_required(login_url='login_page')
def CreatePostView1(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            caption = form.cleaned_data.get("caption")
            media_files = request.FILES.getlist("media")
            for m in media_files:
                print('Media_files', m)
                

            # Send to background queue (handle saving + media separately)
            enqueue_post_task(user=request.user, caption=caption, media_files=media_files)
            print('Called-----------------------------------------------------------------------')
            return redirect("home_page")
    else:
        form = PostForm()

    return render(request, "posts/create_post.html", {"form": form})


@login_required(login_url='login_page')
def CreatePostView(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            caption = form.cleaned_data.get("caption")
            post = form.save(commit=False)
            post.user = request.user
            post.caption = caption  # Ensure caption is set
            post.save()

            # Handle multiple media files
            media_files = request.FILES.getlist("media")
            for file in media_files:
                print('Media_file:', file)  # Debug print
                PostMedia.objects.create(post=post, file=file)

            print('Caption is here----------', caption)
            # Send to background queue for logging, notification, etc.
            enqueue_post_task(user=request.user, post=post, caption=caption)
            print('Background task called ✅')

            return redirect("home_page")
    else:
        form = PostForm()

    return render(request, "posts/create_post.html", {"form": form})


@login_required(login_url='login_page')
def HashtagView(request, hashtag):
    """Show posts related to a hashtag"""
    hashtag_obj = get_object_or_404(Hashtag, name=hashtag)
    posts = hashtag_obj.posts.all()
    return render(request, "posts/hashtag_posts.html", {"hashtag": hashtag, "posts": posts})


@login_required(login_url='login_page')
def PostDetailView(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_liked = request.user in post.likes.all()
    return render(request, 'posts/post_detail.html', {'post':post, 'is_liked': is_liked,})



@login_required(login_url='login_page')
def EditPostView(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)  # Ensure only the owner can edit

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully!")
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'posts/edit_post.html', {'form': form, 'post': post})


@login_required(login_url='login_page')
def DeletePostView(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)  # Ensure only owner can delete

    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted successfully!")
        return redirect('home_page')

    return render(request, 'posts/confirm_delete.html', {'post': post})


def download_post(request, media_id):
    media = get_object_or_404(PostMedia, id=media_id)
    
    # Get the file path
    file_path = media.file.path

    if not os.path.exists(file_path):
        raise Http404("File does not exist")

    # Get file name to display it nicely when downloaded
    file_name = os.path.basename(file_path)

    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)
    return response