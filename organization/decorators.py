from django.shortcuts import redirect
from functools import wraps

def branch_owner_required(view_func):
    
    @wraps(view_func)
    def _wrapper_view(request, *args,  **kwargs):
        if request.user.role != 'BRANCH_OWNER':
            return redirect('permission_denied')
        return view_func(request, *args, **kwargs)

    return _wrapper_view
    