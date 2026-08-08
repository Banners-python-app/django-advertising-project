from agency.models import Category

def global_categories(request):
    # This grabs all categories and makes them available globally as 'categories'
    return {
        'categories': Category.objects.all()
    }