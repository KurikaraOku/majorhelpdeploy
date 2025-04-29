from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.template import loader
from django.http import Http404
from django.db.models import F
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.views.generic import *
from django.contrib import messages
from .models import *
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
import re
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Value
from django.db.models.functions import Cast
from django.db.models import Min
from django.core.signing import TimestampSigner
from django.core.mail import send_mail
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
from .discussion_models import DiscussionCategory, DiscussionThread, ThreadReply
from django.shortcuts import render, get_object_or_404, redirect
from .forms import NewThreadForm
from .forms import ThreadReplyForm  
from django.shortcuts import get_object_or_404, redirect
import json
import re
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import DiscussionThread
from django.views.decorators.http import require_POST # used for favorite feature
# Used to catch an exception if GET tries to get a value that isn't defined.
from django.utils.datastructures import MultiValueDictKeyError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder


# views.py

def college_map(request):
    universities = University.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    data = [
        {
            'name': u.name,
            'lat': float(u.latitude),
            'lng': float(u.longitude),
            'color': u.primary_color or "#268f95",
            'url': f"/UniversityOverview/{u.slug}/"
        }
        for u in universities
    ]
    return render(request, 'map/college_map.html', {
        'universities_json': json.dumps(data, cls=DjangoJSONEncoder)
    })

@login_required
def major_chat(request):
    return render(request, 'majorchat/chat.html')

class MyThreadsView(LoginRequiredMixin, View):
    def get(self, request):
        threads = DiscussionThread.objects.filter(author=request.user).order_by('-created_at')
        categories = DiscussionCategory.objects.all()
        return render(request, 'discussion/discussion_board.html', {
            'threads': threads,
            'all_categories': categories,
            'my_threads': True
        })

@login_required
def my_discussions(request):
    threads = DiscussionThread.objects.filter(author=request.user).order_by('-created_at')
    categories = DiscussionCategory.objects.all()
    return render(request, 'discussion/discussion_board.html', {
        'threads': threads,
        'categories': categories
    })

@login_required
def delete_thread(request, pk):
    thread = get_object_or_404(DiscussionThread, pk=pk)
    if thread.author == request.user:
        thread.delete()
        messages.success(request, "Thread deleted.")
    else:
        messages.error(request, "You are not allowed to delete this thread.")
    return redirect('MajorHelp:discussion_board')

@login_required
def delete_reply(request, pk):
    reply = get_object_or_404(ThreadReply, pk=pk)
    if reply.author == request.user:
        thread_pk = reply.thread.pk
        reply.delete()
        messages.success(request, "Reply deleted.")
        return redirect('MajorHelp:discussion_detail', pk=thread_pk)
    else:
        messages.error(request, "You are not allowed to delete this reply.")
        return redirect('MajorHelp:discussion_board')

@login_required
def create_thread(request):
    if request.method == 'POST':
        form = NewThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            return redirect('MajorHelp:discussion_board')
    else:
        form = NewThreadForm()
    
    return render(request, 'discussion/create_thread.html', {'form': form})

@login_required
def discussion_detail(request, pk):
    thread = get_object_or_404(DiscussionThread, pk=pk)
    replies = thread.replies.all().order_by('created_at')

    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            ThreadReply.objects.create(
                thread=thread,
                content=content,
                author=request.user,
                created_at=timezone.now()
            )
            return redirect('MajorHelp:discussion_detail', pk=thread.pk)

    return render(request, 'discussion/discussion_detail.html', {
        'thread': thread,
        'replies': replies
    })

@method_decorator(login_required, name='dispatch')
class DiscussionCategoryListView(View):
    def get(self, request):
        categories = DiscussionCategory.objects.all()
        return render(request, 'discussion/category_list.html', {'categories': categories})


@method_decorator(login_required, name='dispatch')
class DiscussionThreadListView(View):
    def get(self, request, category_id):
        category = get_object_or_404(DiscussionCategory, id=category_id)
        threads = DiscussionThread.objects.filter(category=category).order_by('-created_at')
        return render(request, 'discussion/thread_list.html', {
            'category': category,
            'threads': threads
        })


@method_decorator(login_required, name='dispatch')
class DiscussionThreadDetailView(View):
    def get(self, request, pk):
        thread = get_object_or_404(DiscussionThread, pk=pk)
        replies = thread.replies.all().order_by('created_at')
        form = ThreadReplyForm()
        return render(request, 'discussion/thread_detail.html', {
            'thread': thread,
            'replies': replies,
            'form': form
        })

    def post(self, request, pk):
        thread = get_object_or_404(DiscussionThread, pk=pk)
        form = ThreadReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()
            return redirect('MajorHelp:discussion_detail', pk=thread.pk)

        replies = thread.replies.all().order_by('created_at')
        return render(request, 'discussion/thread_detail.html', {
            'thread': thread,
            'replies': replies,
            'form': form
        })

@login_required
def discussion_board(request):
    category_id = request.GET.get('category')
    query = request.GET.get('q', '')

    threads = DiscussionThread.objects.select_related('author', 'category').order_by('-created_at')

    if category_id:
        threads = threads.filter(category_id=category_id)

    if query:
        threads = threads.filter(title__icontains=query)

    return render(request, 'discussion/discussion_board.html', {
        'threads': threads,
    })

def settings_view(request):
    return render(request, 'settings.html')  # Make sure you have a 'settings.html' template, or adjust accordingly

# HomeView displays the homepage
class HomeView(TemplateView):
    template_name = "MajorHelp/HomePage.html"

#University overview page 
class UniversityOverviewView(DetailView):
    model = University
    template_name = "MajorHelp/UniOverviewPage.html"
    context_object_name = "university"
    

    # Use slug as the lookup field
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    

    def get_object(self):
        slug = self.kwargs['slug']
        return get_object_or_404(University, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        university = self.get_object()

        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user,
                university=university
            ).exists()

            # Whether this user already submitted a review
            context['user_review'] = UniversityReview.objects.filter(
                username=self.request.user.username,
                university=university
            ).exists()
        else:
            context['is_favorite'] = False

        
        context['latest_post_list'] = UniversityReview.objects.filter(
            university=university
        ).order_by('-pub_date')

        context['primary_color'] = university.primary_color if university.primary_color else '#ffffff'
        context['secondary_color'] = university.secondary_color if university.secondary_color else '#ffffff'
        context['rating_categories'] = ['Campus', 'Athletics', 'Safety', 'Social Life', 'Professors', 'Dorms', 'Dining']
        # Fetch user's existing ratings for this university
        user_ratings = {}

        if self.request.user.is_authenticated:
            ratings = UniversityRating.objects.filter(user=self.request.user, university=self.object)
            for rating in ratings:
                user_ratings[slugify(rating.category)] = int(rating.rating)

        context['user_ratings'] = user_ratings


        
        return context
        
        #JUMP
        if self.request.user.is_authenticated:
            self.request.user.refresh_from_db()
            user_review = UniversityReview.objects.filter(username=self.request.user.username, university=university).exists()
            context['user_review'] = user_review  # If review exists, pass it to the template
            
            #Adds favorite status to context
            context['is_favorite'] = Favorite.objects.filter (
                user=self.request.user, 
                university=university
            ).exists()

        
        return context
        
# View for submitting a rating to a specific catagory of a cartain university    
class SubmitRatingView(View):
    def post(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        
        # Get the category and rating from the submitted form data
        category = request.POST.get('category')
        rating_value = int(request.POST.get('rating'))
        
        # Ensure the rating is between 1 and 5
        if category in ['campus', 'athletics', 'safety', 'social', 'professor', 'dorm', 'dining'] and 1 <= rating_value <= 5:
            rating, created = UniversityRating.objects.update_or_create(
                university=university,
                category=category,  # Use the selected category
                user=request.user,
                defaults={'rating': rating_value}
            )
            if created:
                messages.success(request, 'Your rating has been submitted.')
            else:
                messages.success(request, 'Your rating has been updated.')
        else:
            messages.error(request, 'Invalid rating. Please select a value between 1 and 5.')

        return redirect('MajorHelp:university-detail', slug=university.slug)

class LeaveUniversityReview(View):
    def post(self, request, username):
        review_text = request.POST.get("review_text", "").strip()
        university_id = request.POST.get("university_id")

        if not review_text:
            messages.error(request, 'Review text cannot be empty.')
            return redirect('MajorHelp:university-detail', slug=university_id)

        university = get_object_or_404(University, pk=university_id)

        # Check if the user has already left a review for this university
        existing_review = UniversityReview.objects.filter(username=request.user.username, university=university).exists()

        if existing_review:
            messages.error(request, 'You have already submitted a review for this university.')
        else:
            # Create and save the review
            UniversityReview.objects.create(
                username=request.user.username,
                review_text=review_text,
                university=university
            )
            messages.success(request, 'Your review has been successfully submitted!')

        return redirect('MajorHelp:university-detail', slug=university.slug)

# Custom form for login
class CustomLoginView(LoginView):
    def form_valid(self, form):
        remember_me = self.request.POST.get("remember_me")
        
        if not remember_me:
            # Expire session when the browser closes
            self.request.session.set_expiry(0)
        else:
            # Keep session active for 2 weeks
            self.request.session.set_expiry(1209600) 
        self.request.session.modified = True   
        
        return super().form_valid(form)
    
# Custom form for SignUp
class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter your Password'}), label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your Password'}), label="Confirm password")
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Enter your Email'}))
    role = forms.ChoiceField(
        choices=[('', 'Select a role')] + [choice for choice in CustomUser.ROLE_CHOICES if choice[0] != 'admin'],
        widget=forms.Select()
    )
    #NEED TO ADD FIRST NAME AND LAST NAME FIELDS
    
    class Meta:
        model = get_user_model()  # Use the custom user model dynamically
        fields = ['username', 'email', 'password', 'confirm_password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your Username'}), #placeholder text in username box
        }
        labels = {
            'username': 'Username', # change the labe of the username entry box
        }
        help_texts = {
            'username': '', # help text by username entry box if we want to add
        }

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.set_password(self.cleaned_data["password"])  # Hash the password
        if commit:
            user.save()
        return user

User = get_user_model()
signer = TimestampSigner()

# SignUpView for user registration
class SignUpView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Mark account as inactive until email verification
            user.save()

            # Generate a token that includes the user's primary key
            token = signer.sign(user.pk)
            activation_link = request.build_absolute_uri(
    reverse('MajorHelp:activate_account', args=[token])
)
            # Send an activation email to the user
            send_mail(
                'Activate Your MajorHelp Account',
                f'Please click the link to activate your account: {activation_link}',
                'noreply@majorhelp.com',  # Replace with your sender email
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'An activation email has been sent. Please check your inbox.')
            return redirect('MajorHelp:check_email')  # Redirect to login page after sign-up
        return render(request, 'registration/signup.html', {'form': form})
    

def check_email_view(request):
    return render(request, 'registration/check_email.html')

def about(request):
    return render(request, 'About/about.html')
    
def contact(request):
    return render(request,'Contact/contact.html')

def activate_account(request, token):
    try:
        # Unsign the token; valid for 1 day (86400 seconds)
        user_pk = signer.unsign(token, max_age=86400)
        user = User.objects.get(pk=user_pk)
        user.is_active = True  # Activate the user
        user.save()
        messages.success(request, 'Your account has been activated. You can now log in.')
        return redirect('MajorHelp:login')
    except SignatureExpired:
        messages.error(request, 'Activation link has expired. Please sign up again.')
        return redirect('MajorHelp:signup')
    except (BadSignature, User.DoesNotExist):
        messages.error(request, 'Invalid activation link.')
        return redirect('MajorHelp:signup')

#the search function
class SearchView(View):
    def get(self, request):
        query = request.GET.get('query', '')
        filter_type = request.GET.get('filter', 'department')
        
        # If the query is empty, reload the search page without redirecting
        if not query:
            return render(request, 'search/search.html', {'query': query, 'filter_type': filter_type})
        
        # Redirect based on the filter type if query is provided
        if filter_type == 'school':
            return redirect('MajorHelp:school_results', query=query)
        elif filter_type == 'department':
            return redirect('MajorHelp:department_results', query=query)
        elif filter_type == 'major':
            return redirect('MajorHelp:major_results', query=query)
        
        # Default behavior (in case of other filter types)
        return render(request, 'search/search.html', {'query': query, 'filter_type': filter_type})

from django.db.models import Prefetch, F

class SchoolResultsView(View):
    def get(self, request, query):
        school_type = request.GET.get('school_type', 'both')

        universities_list = University.objects.filter(name__istartswith=query).only(
            'name', 'location', 'is_public', 'slug'
        )

        if school_type == 'public':
            universities_list = universities_list.filter(is_public=True)
        elif school_type == 'private':
            universities_list = universities_list.filter(is_public=False)

        paginator = Paginator(universities_list, 10)
        page = request.GET.get('page')

        try:
            universities = paginator.page(page)
        except PageNotAnInteger:
            universities = paginator.page(1)
        except EmptyPage:
            universities = paginator.page(paginator.num_pages)

        # 💥 Super lightweight prefetch using only needed fields
        majors_prefetch = Prefetch(
            'majors',
            queryset=Major.objects.only(
                'major_name', 'slug', 'department',
                'in_state_min_tuition', 'in_state_max_tuition',
                'out_of_state_min_tuition', 'out_of_state_max_tuition'
            ).order_by('department', 'major_name')
        )
        universities.object_list = universities.object_list.prefetch_related(majors_prefetch)


        results = {}
        for university in universities:
            majors = university.majors.all()

            departments = {}
            for major in majors:
                departments.setdefault(major.department, []).append({
                    'major_name': major.major_name,
                    'slug': major.slug,
                    'in_state_min_tuition': major.in_state_min_tuition,
                    'in_state_max_tuition': major.in_state_max_tuition,
                    'out_of_state_min_tuition': major.out_of_state_min_tuition,
                    'out_of_state_max_tuition': major.out_of_state_max_tuition,
                })

            if departments:
                results[university.slug] = {
                    'name': university.name,
                    'location': university.location,
                    'type': 'Public' if university.is_public else 'Private',
                    'departments': departments,
                }

        return render(request, 'search/school_results.html', {
            'query': query,
            'results': results,
            'school_type': school_type,
            'filter_type': 'school',
            'page_obj': universities,
            'is_paginated': universities.has_other_pages(),
        })




from django.views import View
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from .models import Major
import string

from django.views import View
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import string

class DepartmentResultsView(View):
    def get(self, request, query):
        school_type = request.GET.get('school_type', 'both')
        letter = request.GET.get('letter', 'A').upper()
        page = request.GET.get('page', 1)

        # Step 1: Filter majors by department
        majors_list = Major.objects.filter(department__icontains=query)

        # Step 2: Filter by school type (public/private)
        if school_type == 'public':
            majors_list = majors_list.filter(university__is_public=True)
        elif school_type == 'private':
            majors_list = majors_list.filter(university__is_public=False)

        # Step 3: Filter by university first letter
        if letter:
            majors_list = majors_list.filter(university__name__istartswith=letter)

        # Step 4: Use .values() for lighter query
        majors_list = majors_list.values(
            'major_name', 'slug', 'department',
            'in_state_min_tuition', 'in_state_max_tuition',
            'out_of_state_min_tuition', 'out_of_state_max_tuition',
            'university__name', 'university__location', 'university__slug', 'university__is_public'
        ).order_by('university__name')

        # Step 5: Group majors by university
        grouped_results = {}
        for major in majors_list:
            uni_slug = major['university__slug']
            if uni_slug not in grouped_results:
                grouped_results[uni_slug] = {
                    'name': major['university__name'],
                    'location': major['university__location'],
                    'type': 'Public' if major['university__is_public'] else 'Private',
                    'departments': {}
                }
            dept = major['department']
            grouped_results[uni_slug]['departments'].setdefault(dept, []).append({
                'major_name': major['major_name'],
                'slug': major['slug'],
                'in_state_min_tuition': major['in_state_min_tuition'],
                'in_state_max_tuition': major['in_state_max_tuition'],
                'out_of_state_min_tuition': major['out_of_state_min_tuition'],
                'out_of_state_max_tuition': major['out_of_state_max_tuition'],
            })

        # Step 6: Paginate universities (only 5 at a time to save memory)
        university_items = list(grouped_results.items())
        paginator = Paginator(university_items, 5)  # <-- Only load 5 universities per page!!

        try:
            paginated_results = paginator.page(page)
        except PageNotAnInteger:
            paginated_results = paginator.page(1)
        except EmptyPage:
            paginated_results = paginator.page(paginator.num_pages)

        # Step 7: Send to template
        return render(request, 'search/department_results.html', {
            'query': query,
            'results': dict(paginated_results.object_list),
            'school_type': school_type,
            'filter_type': 'department',
            'page_obj': paginated_results,
            'is_paginated': paginator.num_pages > 1,
            'alphabet': list(string.ascii_uppercase),
            'current_letter': letter,
        })





from django.views import View
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from .models import Major
import string

class MajorResultsView(View):
    def get(self, request, query):
        school_type = request.GET.get('school_type', 'both')
        page = request.GET.get('page')
        letter = request.GET.get('letter', 'A').upper()

        # Step 1: Filter majors by major name
        majors_qs = Major.objects.filter(major_name__istartswith=query)

        # Step 2: Filter by school type
        if school_type == 'public':
            majors_qs = majors_qs.filter(university__is_public=True)
        elif school_type == 'private':
            majors_qs = majors_qs.filter(university__is_public=False)

        # Step 3: Filter by university first letter
        if letter:
            majors_qs = majors_qs.filter(university__name__istartswith=letter)

        # Step 4: Use .values() instead of .only()
        majors_qs = majors_qs.values(
            'major_name', 'slug', 'department',
            'in_state_min_tuition', 'in_state_max_tuition',
            'out_of_state_min_tuition', 'out_of_state_max_tuition',
            'university__name', 'university__location', 'university__slug', 'university__is_public'
        ).order_by('university__name')

        # Step 5: Group majors by university and department
        results = {}
        for major in majors_qs:
            uni_slug = major['university__slug']
            if uni_slug not in results:
                results[uni_slug] = {
                    'name': major['university__name'],
                    'location': major['university__location'],
                    'type': 'Public' if major['university__is_public'] else 'Private',
                    'departments': {}
                }

            dept = major['department']
            results[uni_slug]['departments'].setdefault(dept, []).append({
                'major_name': major['major_name'],
                'slug': major['slug'],
                'in_state_min_tuition': major['in_state_min_tuition'],
                'in_state_max_tuition': major['in_state_max_tuition'],
                'out_of_state_min_tuition': major['out_of_state_min_tuition'],
                'out_of_state_max_tuition': major['out_of_state_max_tuition'],
            })

        # Step 6: Paginate universities (5 per page)
        university_items = list(results.items())
        paginator = Paginator(university_items, 5)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        paginated_results = dict(page_obj.object_list)

        # Step 7: Render
        return render(request, 'search/major_results.html', {
            'query': query,
            'results': paginated_results,
            'school_type': school_type,
            'filter_type': 'major',
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'alphabet': list(string.ascii_uppercase),
            'current_letter': letter,
        })



    
class MajorOverviewView(DetailView):
    model = Major
    template_name = "major/MajorOverviewPage.html"
    context_object_name = "major"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        major = self.object

        # Calculate average rating (if you keep the rating field)
        reviews = major.major_reviews.all()
        if reviews.exists():
            average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            context['average_rating'] = round(float(average_rating), 1)
        else:
            context['average_rating'] = 0.0

        # ✅ These are used in the template
        context['reviews'] = reviews
        context['latest_post_list'] = reviews.order_by('-pub_date')
        context['star_range'] = [1, 2, 3, 4, 5]

        # Check if user has already left a review
        if self.request.user.is_authenticated:
            context['user_review'] = reviews.filter(user=self.request.user).first()
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user,
                major=major
            ).exists()
        else:
            context['user_review'] = None
            context['is_favorite'] = False

        return context


class CalcView(View):
    def get(self, request):
        saved_calcs = {}
        if request.user.is_authenticated:
            request.user.refresh_from_db()  # Make sure we get the latest data
            saved_calcs = request.user.savedCalcs

        return render(request, 'calc/calc_page.html', {
            'saved_calcs': saved_calcs
        })


# LeaveMajorReview View - Exclusive for leaving reviews for a major at a specific school
# changed to be like LeaveUnivserityReview 


class LeaveMajorReview (View):
    def post(self, request, username):
        review_text = request.POST.get("review_text", "").strip()
        major_id = request.POST.get("major_id")

        if not review_text:
            messages.error(request, 'Review text cannot be empty.')
            return redirect('MajorHelp:major-detail', slug=major_id)

        major = get_object_or_404(Major, pk=major_id)
        user = request.user

        # Check for existing review by this user for this major
        existing_review = MajorReview.objects.filter(user=user, major=major).exists()

        if existing_review:
            messages.error(request, 'You have already submitted a review for this major.')
        else:
            MajorReview.objects.create(
                user=user,
                review_text=review_text,
                major=major,
                university=major.university
            )
            messages.success(request, 'Your review has been successfully submitted!')

        return redirect('MajorHelp:major-detail', slug=major.slug)



# Render review stars in Major Overview
class UniversityRequestView(View):
    def get(self, request):
        return render(request, 'search/universityRequest.html')

    def post(self, request):
        request_text = request.POST.get('request_text')
        if request_text:
            UniversityRequest.objects.create(
                user=request.user if request.user.is_authenticated else None,
                request_text=request_text
            )
            messages.success(request, 'Your university request has been submitted.')
            return redirect('MajorHelp:home')
        else:
            messages.error(request, 'Please enter your request.')
            return render(request, 'search/universityRequest.html')
    

@csrf_exempt
def university_search(request):
    query = request.GET.get('query', '').strip()

    if not query:
        return JsonResponse({"universities": []}, status=400)

    universities = University.objects.filter(
        name__istartswith=query
    ).only('name', 'location').order_by('name')

    if not universities.exists():
        return JsonResponse({"universities": []}, status=404)

    data = {"universities": []}
    for uni in universities:
        data["universities"].append({
            "name": uni.name,
            "location": uni.location,
            # departments can still be included if you want, but it adds query cost
            # "departments": list(uni.majors.values_list("department", flat=True).distinct())
        })

    return JsonResponse(data)



def calc_list(request):
    if not request.user.is_authenticated:
        # 401 - Unauthorized
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/401
        return HttpResponse("Error - You must be logged in", status=401)
    
    user = request.user
    user.refresh_from_db()


    query = request.GET.get('query')

    # #if not query:
    # #    return HttpResponse("Error - No query provided", status=400)
    #
    # Above is commented out due to Vedal wanting all calcs to show when the
    # user clicks on the search bar.

    # lower the query so that the filtering can be case insensitive
    query = query.lower()

    # dict_you_want = {key: old_dict[key] for key in your_keys}

    # # Returns the values of the calculators matching the filtered_keys
    # filtered_keys = ["Calculator 1", "Calculator 2"]
    # calculators = {key: user.savedCalcs[key] for key in filtered_keys}
    # 
    # # Might be useful later

    # >>> lst = ['a', 'ab', 'abc', 'bac']
    # >>> [k for k in lst if 'ab' in k]
    # ['ab', 'abc']


    # Grab the saved calculators from the user:
    savedCalcs = list(user.savedCalcs.keys())
    # This converts a dict_keys to a list of strings


    # Filter by the given query:
    applicableKeys = [key for key in savedCalcs if query in key]

    data = {"calculators" : []}

    # Create a dictionary of the mix-case names to their corresponding keys
    for key in applicableKeys:
        data['calculators'].append(
            user.savedCalcs[key]
        )

    # Return the data

    # Example return data:
    #
    #   {'calculators'  :   [
    #       {
    #           'calcName'  :   'UofSC',
    #           'uni'       :   'UofSC',
    #           'outstate'  :    False,
    #           'dept'      :   'Engineering and Technology',
    #           'major'     :   'CIS',
    #           'aid'       :   'Palmetto Fellows'
    #       },
    #       {
    #           'calcName'  :   'Custom Name',
    #            ...
    #       },
    #       ...
    #   ]}
    #

    return JsonResponse(data)

def save_calc(request):
    if not request.user.is_authenticated:
        return HttpResponse("Error - You must be logged in", status=403) # 403 Forbidden

    user = request.user

    if request.method == 'DELETE':
        # Expected Data
        #
        # { 'calcname' : { True } } // key is the name of the calculator but in lowercase
        # 
        # // The value in the json is not important, just the key is used to delete the calculator
        
        try:
            data = json.loads(request.body.decode())
            key = list(data.keys())[0].lower()

            if key in user.savedCalcs:
                del user.savedCalcs[key]
                user.save()
                return HttpResponse("Deleted", status=204) # No Content, preferred for deletions
            else: 
                return HttpResponse("Key not found", status=404)

        except Exception as e:
            return HttpResponseBadRequest("Invalid delete request: " + str(e))

    if request.method == 'POST':
        # Expected Data
        # { 'calcname'      : {      // key is the name of the calculator but in lowercase
        #        'calcName'      :   'testCalc',
        #        'uni'           :   'exampleUni',
        #        'oustate'       :    False,
        #        'dept'          :   'Humanities and Social Sciences',
        #        'major'         :   'exampleMajor',
        #        'aid'           :   'exampleAid',
        #    }
        # }


        try:
            data = json.loads(request.body.decode())
            key = list(data.keys())[0].lower() # The view "politely" corrects the key to be lowercase
            value = data[key]

            # Validate value
            if not isinstance(value, dict):
                return HttpResponseBadRequest("Invalid value format. Expected a dictionary.")
            
            # Validate required fields in the value dictionary
            required_fields = ['calcName', 'uni', 'outstate', 'dept', 'major', 'aid']
            for field in required_fields:
                if field not in value:
                    return HttpResponseBadRequest(f"Missing required field: {field}")

            # Validate that all fields are strings or booleans as appropriate
            for field in required_fields:
                if field == 'outstate':
                    if not isinstance(value[field], bool):
                        return HttpResponseBadRequest(f"Field '{field}' must be a boolean.")
                elif field == 'aid':
                    if not isinstance(value[field], (str, int)):
                        return HttpResponseBadRequest(f"Field '{field}' must be a string or an integer.")
                else:
                    if not isinstance(value[field], str):
                        return HttpResponseBadRequest(f"Field '{field}' must be a string.")

            # Save or update the calculator
            user.savedCalcs[key] = value
            user.save()
            return HttpResponse("Saved", status=201) # Created, preferred for new resources

        except Exception as e:
            return HttpResponseBadRequest("Error saving calculator: " + str(e))


    # The method was neither delete nor post, respond with 405 and an allow header with the list
    # of the supported methods

    # (mozilla wants us to do this apparently)
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Allow

    allowed_methods = "POST, DELETE"

    # return an http response with a 405 status code and the allowed methods in the header
    response = HttpResponse("Method Not Allowed", status=405)

    # Add the values in the allowed methods to the header
    response['Allow'] = allowed_methods
   
    return response



def aid_list(request):
    uniQuery = request.GET.get('university')
    uniObj = None

    if not uniQuery:
        return HttpResponse("Error - No university provided.", status=400)

    try:
        uniObj = University.objects.get(name__iexact=uniQuery)
    except University.DoesNotExist as error:
        return HttpResponse("Error - No university found.", status=404)
    
    data = {"aids" : []}
    for aid in uniObj.applicableAids.all():
        data["aids"].append({
            'name'      : aid.name,
            'location'  : aid.location,
            'amount'    : aid.amount,
        })
    
    return JsonResponse(data)


def major_list(request):
    university_name = request.GET.get('university', '')
    department = request.GET.get('department', '')

    if not university_name:
        return HttpResponse("Error - No university provided.", status=400)

    if not department:
        return HttpResponse("Error - No department provided.", status=400)

    # Ensure university exists
    university = University.objects.filter(name__icontains=university_name).first()
    if not university:
        return HttpResponse("Error - University not found", status=404)

    # Filter majors by university and department
    majors = Major.objects.filter(university=university, department=department)
    if not majors.exists():
        return JsonResponse({"majors": []})  # Return empty list if no majors found

    data = {"majors": [{"name": major.major_name} for major in majors]}

    return JsonResponse(data)


def calculate(request):
    
    university_name = request.GET.get('university')
    major_name = request.GET.get('major')
    outstate = request.GET.get('outstate')
    aid_name = request.GET.get('aid')

    if not university_name:
        return HttpResponse("Error - No university provided.", status=400)

    if not major_name:
        return HttpResponse("Error - No major provided.", status=400)

    if not outstate:
        return HttpResponse("Error - No outstate provided.", status=400)

    # effectively cast outstate to a boolean now that we know its validated
    outstate = outstate == 'true'


    # Ensure university exists
    university = University.objects.filter(name__icontains=university_name).first()
    if not university:
        return HttpResponse("Error - University not found", status=404)

    # Ensure major exists
    major = Major.objects.filter(university=university, major_name__icontains=major_name).first()
    if not major:
        return HttpResponse("Error - Major not found", status=404)

    # Get aid
    aid = 0
    aidObj = None

    if aid_name and aid_name not in ["", "None", "null"]:
        # Try to convert to int (custom aid), else treat as aid name
        try:
            aid = int(aid_name)
        except ValueError:
            aidObj = FinancialAid.objects.filter(name=aid_name).first()
            if not aidObj:
                return HttpResponse("Error - Financial Aid not found.", status=404)
            aid = aidObj.amount

    


    # Determine correct tuition range
    if outstate:
        min_tuition = university.out_of_state_base_min_tuition + major.out_of_state_min_tuition
        max_tuition = university.out_of_state_base_max_tuition + major.out_of_state_max_tuition
    else:
        min_tuition = university.in_state_base_min_tuition + major.in_state_min_tuition 
        max_tuition = university.in_state_base_max_tuition + major.in_state_max_tuition

    # Add university and major fees
    min_tuition += university.fees + major.fees
    max_tuition += university.fees + major.fees


    # Apply Aid
    min_tuition -= aid
    max_tuition -= aid

    data = {
        "minTui": min_tuition,
        "maxTui": max_tuition,
        "uni": {
            "name": university.name,
            "baseMinTui": university.in_state_base_min_tuition if not outstate else university.out_of_state_base_min_tuition,
            "baseMaxTui": university.in_state_base_max_tuition if not outstate else university.out_of_state_base_max_tuition,
            "fees": university.fees
        },
        "major": {
            "name": major.major_name,
            "baseMinTui": major.in_state_min_tuition if not outstate else major.out_of_state_min_tuition,
            "baseMaxTui": major.in_state_max_tuition if not outstate else major.out_of_state_max_tuition,
            "fees": major.fees
        },
        "aid": (
            {} if aid_name in ["", "None", "null", None]
            else {"name": aidObj.name, "amount": aidObj.amount} if aidObj
            else {"name": f"Custom Aid (${aid})", "amount": aid}
        ),

    }

    return JsonResponse(data)

# favorite feature views for universities and majors 
@require_POST
@login_required
def toggle_favorite(request, object_type, object_id):
    if object_type == 'university':
        obj = get_object_or_404(University, pk=object_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            university=obj
        )
    elif object_type == 'major':
        obj = get_object_or_404(Major, pk=object_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            major=obj
        )
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid object type'}, status=400)
    
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})
    
    return JsonResponse({'status': 'added'})

# for favorites page
@login_required
def favorites_list(request):
    university_favorites = Favorite.objects.filter(
        user=request.user, 
        university__isnull=False
    ).select_related('university').order_by('-created_at') # order_by sorts the list by most recent add to the list for universities in this case.
    
    major_favorites = Favorite.objects.filter(
        user=request.user, 
        major__isnull=False
    ).select_related('major', 'major__university').order_by('-created_at') # order_by sorts the list by most recent add to the list for majors in this case.
    
    return render(request, 'Favorite/favorites.html', {
        'university_favorites': university_favorites,
        'major_favorites': major_favorites
    })


def university_map_data(request):
    universities = University.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    data = []

    for uni in universities:
        data.append({
            'name': uni.name,
            'lat': float(uni.latitude),
            'lng': float(uni.longitude),
            'color': uni.primary_color or "#268f95",
            'url': f"/UniversityOverview/{uni.slug}/"
        })


    return JsonResponse({'universities': data})
from django.contrib.auth.views import redirect_to_login  # If not already imported
from django.urls import reverse

class SubmitOverallRatingView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            university = get_object_or_404(University, pk=pk)
            return redirect_to_login(next=reverse('MajorHelp:university-detail', kwargs={'slug': university.slug}))

        university = get_object_or_404(University, pk=pk)

        
        if request.user.role not in ['alumni', 'current_student']:
            messages.error(request, 'You must be a Current Student or Alumni to submit a university rating.')
            return redirect('MajorHelp:university-detail', slug=university.slug)

        CATEGORY_MAP = {
            'campus': 'campus',
            'athletics': 'athletics',
            'safety': 'safety',
            'social-life': 'social',
            'professors': 'professor',
            'dorms': 'dorm',
            'dining': 'dining',
        }

        for category_key in CATEGORY_MAP.keys():
            rating = request.POST.get(f'{category_key}_rating')

            if rating:
                true_category = CATEGORY_MAP[category_key]
                UniversityRating.objects.update_or_create(
                    university=university,
                    category=true_category,
                    user=request.user,
                    defaults={'rating': int(rating)}
                )

        messages.success(request, 'Your ratings have been saved successfully!')
        return redirect('MajorHelp:university-detail', slug=university.slug)

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class DeleteReviewView(View):
    def post(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        try:
            review = UniversityReview.objects.get(username=request.user.username, university=university)
            review.delete()
            messages.success(request, "Your review has been deleted.")
        except UniversityReview.DoesNotExist:
            messages.error(request, "Review not found.")
        
        return redirect('MajorHelp:university-detail', slug=university.slug)