from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisteringForm(UserCreationForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = User
        fields = ('username', 'email',)
