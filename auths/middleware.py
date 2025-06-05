from django.shortcuts import redirect

class RoleRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path == '/':
            if request.user.role == 'farmer':
                return redirect('farmer_dashboard')
            elif request.user.role == 'collector':
                return redirect('collector_dashboard')
            elif request.user.is_superuser or request.user.role == 'admin':
                return redirect('admin_dashboard')
        return self.get_response(request)
