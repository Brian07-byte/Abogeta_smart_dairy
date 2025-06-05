from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from auths.models import CustomUser
from django.contrib import messages

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = CustomUser.objects.exclude(is_superuser=True)
    return render(request, 'admin_dashboard/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def view_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'admin_dashboard/view_user.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('admin_dashboard:manage_users')
    return render(request, 'admin_dashboard/edit_user.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.warning(request, 'User deleted successfully.')
    return redirect('admin_dashboard:manage_users')

@login_required
@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.save()
    messages.info(request, 'User deactivated.')
    return redirect('admin_dashboard:manage_users')

@login_required
@user_passes_test(is_admin)
def activate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, 'User activated.')
    return redirect('admin_dashboard:manage_users')
