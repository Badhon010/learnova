from django.db import models
from django.contrib.auth.models import User
from learning.models import Lesson


class Quiz(models.Model):
    lesson = models.OneToOneField(
        Lesson, on_delete=models.CASCADE, related_name='quiz',
        null=True, blank=True,
    )
    title = models.CharField(max_length=200)
    pass_pct = models.PositiveIntegerField(
        default=70,
        help_text='Minimum percentage score required to pass (0–100).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.quiz.title} — Q{self.order}: {self.text[:60]}'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{"✓" if self.is_correct else "✗"} {self.text[:60]}'


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0, help_text='Percentage score 0–100.')
    passed = models.BooleanField(default=False)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'

    def __str__(self):
        return f'{self.user.username} — {self.quiz.title} ({self.score}%)'
