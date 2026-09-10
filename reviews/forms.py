from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review

        fields = [
            "rating",
            "title",
            "comment",
        ]

        widgets = {
            "rating": forms.Select(
                choices=[
                    (1, "1 - Poor"),
                    (2, "2 - Fair"),
                    (3, "3 - Good"),
                    (4, "4 - Very Good"),
                    (5, "5 - Excellent"),
                ],
            ),
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Review title",
                },
            ),
            "comment": forms.Textarea(
                attrs={
                    "placeholder": "Write your review...",
                    "rows": 5,
                },
            ),
        }

        labels = {
            "rating": "Rating",
            "title": "Review Title",
            "comment": "Your Review",
        }