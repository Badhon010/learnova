from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json

from .models import Quiz, QuizAttempt


@login_required
def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__choices'), pk=quiz_id)
    lesson = quiz.lesson
    best_attempt = (
        QuizAttempt.objects.filter(user=request.user, quiz=quiz).order_by('-score').first()
    )

    if request.method == 'POST':
        questions = list(quiz.questions.prefetch_related('choices').order_by('order'))
        total = len(questions)
        correct_count = 0
        results = []

        for q in questions:
            chosen_id = request.POST.get(f'question_{q.id}')
            correct_choice = q.choices.filter(is_correct=True).first()
            chosen_choice = None
            if chosen_id:
                try:
                    chosen_choice = q.choices.get(pk=int(chosen_id))
                except (ValueError, q.choices.model.DoesNotExist):
                    pass
            is_correct = chosen_choice and chosen_choice.is_correct
            if is_correct:
                correct_count += 1
            results.append({
                'question': q,
                'chosen': chosen_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
                'all_choices': list(q.choices.all()),
            })

        score = round((correct_count / total) * 100) if total else 0
        passed = score >= quiz.pass_pct

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
        )

        return render(request, 'quizzes/quiz_result.html', {
            'quiz': quiz,
            'lesson': lesson,
            'results': results,
            'score': score,
            'passed': passed,
            'correct_count': correct_count,
            'total': total,
            'attempt': attempt,
        })

    return render(request, 'quizzes/quiz_detail.html', {
        'quiz': quiz,
        'lesson': lesson,
        'questions': quiz.questions.prefetch_related('choices').order_by('order'),
        'best_attempt': best_attempt,
    })
