from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    followed_by = models.ManyToManyField('self', blank=True, related_name='following', symmetrical=False)
    image = models.ImageField(upload_to='images/', null=True)

    def is_following(self, another_user):
        """ Returns True if this user is following another_user. """
        return another_user in self.following.all()

    def follow(self, another_user):
        """ Makes this user follow another_user. """
        # if not yet following but instructed to follow
        if not self.is_following(another_user):
            another_user.followed_by.add(self)
            another_user.save()

    def unfollow(self, another_user):
        """ Makes this user unfollow another_user. """
        # if not yet following but instructed to follow
        if self.is_following(another_user):
            another_user.followed_by.remove(self)
            another_user.save()

    def get_posts_of_followed_people(self):
        """ Returns posts posted by people followed by this user, in reversed order. """
        return Post.objects.filter(created_by__in=self.following.all()).order_by('-created_time')

class Post(models.Model):
    """ Class to represent a post. """
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', null=True)
    created_time = models.DateTimeField(auto_now_add=True, null=True)
    content = models.TextField()
    liked_by = models.ManyToManyField(User, blank=True, related_name='liked_posts')

    def __str__(self):
        return f'{self.id}: {self.created_by} - {self.content[:50]}'

    def serialize(self):
        return {
            "id": self.id,
            "created_by": self.created_by.id,
            "created_time": self.created_time.strftime("%b %d %Y, %I:%M %p"), #[user.email for user in self.recipients.all()]
            "content": self.content,
            "liked_by": [user.id for user in self.liked_by.all()]
        }

    @staticmethod
    def get_all_posts():
        """ Returns all posts in reverse order """
        return Post.objects.all().order_by('-created_time')