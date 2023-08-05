from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxLengthValidator

from shared.models import BaseModel

User = get_user_model()

class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts') # related_name -> User.posts.all() (Queryset)
    image = models.ImageField(upload_to='post_images', validators=[
        FileExtensionValidator(allowed_extensions=['jpeg','jpg','png'])])
    caption = models.TextField(validators=[MaxLengthValidator(2000)])
    
    class Meta:
        db_table = 'posts' # default -> post_post (App-name_Model-name)
        verbose_name = 'post'
        verbose_name_plural = 'posts'
        
    def __str__(self):
        return f'{self.author} post about {self.caption}'
        
class PostComment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments') # related_name -> User.comments.all() -> return all comments in the post
    comment = models.TextField()
    # nested comment
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='child',
        null=True, # not required
        blank=True
    ) 
    
    def __str__(self):
        return f'comment by {self.author}'
    
    # 1. id = uuid1
    #    comment = comment
    #    parent = null
    
    # 2. id = uuid2
    #    commemt = comment
    #    parent = uuid1 
    
class PostLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'post'],
                name='PostLikeUnique'
            )
        ]

class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')
    
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'comment'],
                name='CommentLikeUnique'
            )
        ]