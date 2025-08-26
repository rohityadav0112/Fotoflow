from django.db import models
from django.contrib.auth.models import User
import re

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.user.username}"

    def total_likes(self):
        return self.likes.count()

    def total_comment(self):
        return self.comments.count()

    def extract_hashtags(self):
        return re.findall(r"#(\w+)", self.caption)

    def extract_mentions(self):
        return re.findall(r"@(\w+)", self.caption)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.process_hashtags()
            self.process_mentions()

    def process_hashtags(self):
        for tag in self.extract_hashtags():
            hashtag, _ = Hashtag.objects.get_or_create(name=tag)
            hashtag.posts.add(self)

    def process_mentions(self):
        for username in self.extract_mentions():
            try:
                mentioned_user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="post_media/")

    def is_image(self):
        return self.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))

    def is_video(self):
        return self.file.name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))

    def __str__(self):
        return f"Media for Post {self.post.id}"

class Hashtag(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    posts = models.ManyToManyField(Post, related_name="hashtags")

    def __str__(self):
        return f"#{self.name}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.id}"