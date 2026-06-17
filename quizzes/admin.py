from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Quiz, Question, Choice, QuizAttempt


class ChoiceInline(TabularInline):
    model = Choice
    extra = 4
    fields = ['text', 'is_correct']


class QuestionInline(TabularInline):
    model = Question
    extra = 2
    fields = ['text', 'order']
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['title', 'lesson', 'pass_pct', 'question_count', 'created_at']
    search_fields = ['title', 'lesson__title']
    list_per_page = 20
    inlines = [QuestionInline]

    @admin.display(description='Questions')
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['text', 'quiz', 'order']
    list_filter = ['quiz']
    search_fields = ['text', 'quiz__title']
    inlines = [ChoiceInline]
    ordering = ['quiz', 'order']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'quiz', 'score', 'passed', 'created_at']
    list_filter = ['passed', 'quiz', 'created_at']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['user', 'quiz', 'score', 'passed', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30

    def has_add_permission(self, request):
        return False
