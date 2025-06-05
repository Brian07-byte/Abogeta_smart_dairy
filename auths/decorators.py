from django.shortcuts import redirect

def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role != role and not request.user.is_superuser:
                return redirect('unauthorized')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
