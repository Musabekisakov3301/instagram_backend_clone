from django.urls import path
from post.views import PostListApiView, PostCreateView, PostRetrieveUpdateDestroyView, \
                       PostCommentListApiView, PostCommentCreateView, CommentListCreateApiView, \
                       PostLikeListView, CommentRetrieveView,CommentLikeListView, PostLikeApiView, CommentLikeApiView

urlpatterns = [
    path('lists/', PostListApiView.as_view()),
    path('create/', PostCreateView.as_view()),
    path('<uuid:pk>/', PostRetrieveUpdateDestroyView.as_view()),
    path('<uuid:pk>/likes/', PostLikeListView.as_view()),
    path('<uuid:pk>/comments/', PostCommentListApiView.as_view()),
    path('<uuid:pk>/comments/create/', PostCommentCreateView.as_view()),
    
    path('comments/', CommentListCreateApiView.as_view()),
    path('comments/<uuid:pk>/', CommentRetrieveView.as_view()),
    path('comments/<uuid:pk>/likes/', CommentLikeListView.as_view()),
    
    path('<uuid:pk>/create-delete-likes/', PostLikeApiView.as_view()),
    path('comments/<uuid:pk>/create-delete-like/', CommentLikeApiView.as_view()),
    #path('likes/'),
    #path('likes/create/'),
    #path('likes/delete/'),
]
