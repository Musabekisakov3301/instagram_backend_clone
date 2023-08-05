from rest_framework import serializers

from users.models import User
from post.models import Post,PostLike,PostComment,CommentLike

class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id','username','photo')

class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)  
    author = UserSerializer(read_only=True)
    post_likes_count = serializers.SerializerMethodField('get_post_likes_count')
    post_comments_count = serializers.SerializerMethodField('get_post_comments_count')
    me_liked = serializers.SerializerMethodField('get_me_liked')
    
    class Meta:
        model = Post
        fields = [
                  'id',
                  'author',
                  'image',
                  'caption',
                  'created_time',
                  'post_likes_count',
                  'post_comments_count',
                  'me_liked'
                  ]
        extra_kwargs = {'image': {'required': False}}
    
    @staticmethod
    def get_post_likes_count(obj): # this is the argument that serialized(post) -> obj
        return obj.likes.count() # Postlike(related_name='likes')
       
    # def get_post_likes_count(self, obj):   # this is the argument that serialized(post) -> obj
    #    return obj.likes.count()           # Postlike(related_name='likes')
    
    @staticmethod
    def get_post_comments_count(obj):
        return obj.comments.count() # PostComment(related_name='comments') 
   
    # def get_post_comments_count(self, obj):
    #    return obj.comments.count() # PostComment(related_name='comments') 
    
    def get_me_liked(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            try:
                like = PostLike.objects.get(post=obj, author=request.user)
                return True
            except PostLike.DoesNotExist:
                return False
        
        return False

class CommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField('get_replies')
    me_liked = serializers.SerializerMethodField('get_me_liked')
    likes_count = serializers.SerializerMethodField('get_likes_count')
    
    class Meta:
        model = PostComment
        fields = [
                  'id',
                  'author',
                  'comment',
                  'post',
                  'parent',
                  'created_time',
                  'replies',
                  'me_liked',
                  'likes_count'
                ]
        
    def get_replies(self, obj):
        if obj.child.exists():
            serializers = self.__class__(obj.child.all(), many=True, context=self.context)  # __class__ ->  recursive serializer    
            return serializers.data
        else:
            return None
    
    def get_me_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(author=user).exists()
        else:
            return False
    
    @staticmethod
    def get_likes_count(obj):
        return obj.likes.count()
    
    # def get_likes_count(self, obj):
    #   return obj.likes.count()

class CommentLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True) # read_only=True -> GET
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ('id','author','comment')

class PostLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = PostLike
        fields = ('id','author','post')