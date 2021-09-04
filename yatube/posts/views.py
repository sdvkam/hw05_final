from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import page_from_paginator


def index(request):
    template = 'posts/index.html'
    page_obj = page_from_paginator(Post.objects.select_related(
        'author', 'group').all(), request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    page_obj = page_from_paginator(
        group.posts.select_related(
            'author', 'group').all(), request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    page_obj = page_from_paginator(
        author.posts.select_related(
            'author', 'group').all(), request.GET.get('page'))
    if request.user.is_authenticated:
        current_user = get_object_or_404(User, username=request.user)
        following = Follow.objects.filter(
            user=current_user, author=author).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form_for_comment = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form_for_comment': form_for_comment,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post_save = form.save(commit=False)
        post_save.author = request.user
        post_save.save()
        return redirect(reverse('post:profile', args=[request.user.username]))
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect(reverse('post:post_detail', args=[post_id]))
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect(reverse('post:post_detail', args=[post_id]))
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    current_user = get_object_or_404(User, username=request.user)
    list_posts_selected_authors = Post.objects.select_related(
        'author', 'group').filter(
            author_id__in=Follow.objects.values('author_id').filter(
                user_id=current_user.id))
    page_obj = page_from_paginator(
        list_posts_selected_authors, request.GET.get('page'))
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # subscribe to author "username"
    current_user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    Follow.objects.get_or_create(user=current_user, author=author)
    return redirect('post:follow_index')


@login_required
def profile_unfollow(request, username):
    # Dislike, unsubscribe from author "username"
    current_user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=current_user, author=author).delete()
    return redirect('post:follow_index')
