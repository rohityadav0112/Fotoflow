from django.shortcuts import render, redirect
from .forms import GroupForm
from .models import GroupMember

def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user  # Step 1: make user the owner
            group.save()
            
            # Step 2: Add the user as an admin in GroupMember
            GroupMember.objects.create(
                group=group,
                user=request.user,
                role=GroupMember.ADMIN
            )

            return redirect('group_detail', group_id=group.id)  # or wherever you wanna go
    else:
        form = GroupForm()
    
    return render(request, 'your_template_name.html', {'form': form})
