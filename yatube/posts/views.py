from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow
from . import consts, utils
from .forms import PostForm, CommentForm
from django.urls import reverse


def index(request):
    """Вызывает шаблон главной страницы сайта."""
    post_list = Post.objects.all()

    page_obj = utils.make_paginator(
        post_list,
        request,
        consts.QUANTITY_OF_POST_TEN
    )

    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    """Обрабатывает шаблон для страницы группы."""
    group = get_object_or_404(Group, slug=slug)

    post_list = group.posts.all()
    page_obj = utils.make_paginator(
        post_list,
        request,
        consts.QUANTITY_OF_POST_TEN
    )

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Профайл пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()

    page_obj = utils.make_paginator(
        post_list,
        request,
        consts.QUANTITY_OF_POST_TEN
    )
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница поста."""
    post = Post.objects.get(id=post_id)
    comments = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None
    )
    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect('posts:profile', temp_form.author)
    context = {
        'form': form,
    }
    return render(request, template, context)


def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(
        request,
        template,
        {'form': form, 'is_edit': True, 'post': post}
    )


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = Post.objects.get(id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = utils.make_paginator(
        post_list,
        request,
        consts.QUANTITY_OF_POST_TEN
    )
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
