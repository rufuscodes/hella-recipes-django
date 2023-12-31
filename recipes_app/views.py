from typing import Any
from django.db.models.query import QuerySet 
from django.shortcuts import render, HttpResponse, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count


from .forms import RecipeForm, RecipeIngredientFormSet, CategoryForm

from django.urls import reverse_lazy

from . import models


# Create your views here.

class RecipeListView(ListView):
    model = models.Recipe
    template_name = 'recipes_app/home.html'
    context_object_name = 'recipes'


class RecipeDetailView(DetailView):
    model = models.Recipe


class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = models.Recipe
    template_name = 'recipes_app/recipe_form.html'
    form_class = RecipeForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = RecipeIngredientFormSet(self.request.POST, prefix='ingredients')
        else:
            context['formset'] = RecipeIngredientFormSet(prefix='ingredients')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        form.instance.author = self.request.user

        if formset.is_valid():
            response = super().form_valid(form)
            
            formset.instance = self.object
            formset.save()
            
            return response
        else:
            return self.form_invalid(form)



class RecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = models.Recipe
    form_class = RecipeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = RecipeIngredientFormSet(self.request.POST, instance=self.object, prefix='ingredients')
        else:
            context['formset'] = RecipeIngredientFormSet(instance=self.object, prefix='ingredients')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            response = super().form_valid(form)
            
            formset.instance = self.object
            formset.save()
            
            return response
        else:
            return self.form_invalid(form)

    def test_func(self):
        recipe = self.get_object()
        return self.request.user == recipe.author

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class RecipeDeleteView( LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = models.Recipe
    success_url = reverse_lazy('recipes-home')
    def test_func(self):
        recipe = self.get_object()
        return self.request.user == recipe.author

def about(request):
    
    return render(request,"recipes_app/about.html", {'title': 'About this app'})

def add_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        formset = RecipeIngredientFormSet(request.POST, prefix='ingredients')
        if form.is_valid() and formset.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            
            for ingredient_form in formset:
                # Set the recipe before saving the ingredient
                ingredient_instance = ingredient_form.save(commit=False)
                ingredient_instance.recipe = recipe
                ingredient_instance.save()
                
            return redirect('recipes-home')
    else:
        form = RecipeForm()
        formset = RecipeIngredientFormSet(prefix='ingredients')
    return render(request, 'recipe_form.html', {'form': form, 'formset': formset})



class IngredientDetailView(DetailView):
    model = models.Ingredient
    template_name = 'recipes_app/ingredient_detail.html'
    context_object_name = 'ingredient'



class RecipeSearchView(ListView):
    model = models.Recipe
    template_name = 'recipes_app/home.html'
    context_object_name = 'recipes'
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return self.model.objects.filter(
                Q(title__icontains=query) | 
                Q(recipeingredient__ingredient__name__icontains=query)
            ).distinct().order_by('-created_at')
        return self.model.objects.all().order_by('-created_at')
        
    def get_queryset(self):
        query = self.request.GET.get('q')
        return self.model.objects.filter(title__icontains=query).order_by('-created_at')
        


def FavoriteRecipe(request, pk):
    recipe = get_object_or_404(models.Recipe, pk=pk)
    if request.user not in recipe.favorited_by.all():
        recipe.favorited_by.add(request.user)
    return redirect(recipe.get_absolute_url())

def UnfavoriteRecipe(request, pk):
    recipe = get_object_or_404(models.Recipe, pk=pk)
    recipe.favorited_by.remove(request.user)
    return redirect(recipe.get_absolute_url())
    
class UserFavoriteRecipes(ListView):
    model = models.Recipe
    template_name = 'recipes_app/user_favorites.html'
    context_object_name = 'recipes'

    def get_queryset(self):
        return self.request.user.favorited_recipes.all()   
    

def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or dashboard after saving
            return redirect('dashboard')
    else:
        form = CategoryForm()

    context = {'form': form}
    return render(request, 'recipes_app/recipe_form.html', context)    

def recipe_list_by_category(request):
    category_name = request.GET.get('category')
    if category_name:
        category = models.Category.objects.get(name=category_name)
        recipes = models.Recipe.objects.filter(category=category)
    else:
        recipes = models.Recipe.objects.all()

    context = {
        'recipes': recipes
    }
    return render(request, 'recipes_app/home.html', context)


