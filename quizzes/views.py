import random

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Quiz, QuizAttempt


@login_required
def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__choices'), pk=quiz_id)
    lesson = quiz.lesson
    best_attempt = (
        QuizAttempt.objects.filter(user=request.user, quiz=quiz).order_by('-score').first()
    )

    if request.method == 'POST':
        session_key = f'quiz_{quiz_id}_questions'
        stored_ids = request.session.get(session_key, [])

        all_questions = list(quiz.questions.prefetch_related('choices').order_by('order'))

        if stored_ids:
            id_set = set(stored_ids)
            questions = [q for q in all_questions if q.id in id_set]
        else:
            questions = all_questions

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
            is_correct = bool(chosen_choice and chosen_choice.is_correct)
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
            total_questions=total,
            correct_answers=correct_count,
        )

        if passed:
            try:
                from learning.notifications import notify_quiz_passed
                notify_quiz_passed(attempt)
            except Exception:
                pass

        if passed and lesson and lesson.required_quiz_questions and lesson.required_quiz_questions > 0:
            _complete_lesson_after_quiz_pass(request.user, lesson)

        if session_key in request.session:
            del request.session[session_key]

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

    questions = _select_questions(quiz, lesson)
    request.session[f'quiz_{quiz_id}_questions'] = [q.id for q in questions]

    return render(request, 'quizzes/quiz_detail.html', {
        'quiz': quiz,
        'lesson': lesson,
        'questions': questions,
        'best_attempt': best_attempt,
    })


def _select_questions(quiz, lesson):
    all_questions = list(quiz.questions.prefetch_related('choices').order_by('order'))
    if lesson and lesson.required_quiz_questions and lesson.required_quiz_questions > 0:
        n = min(lesson.required_quiz_questions, len(all_questions))
        if n < len(all_questions):
            return random.sample(all_questions, n)
    return all_questions


def _complete_lesson_after_quiz_pass(user, lesson):
    from learning.models import UserLessonProgress
    from learning.views import _check_and_issue_certificate

    progress = UserLessonProgress.objects.filter(user=user, lesson=lesson).first()
    if progress and progress.progress_pct >= 100 and not progress.is_complete:
        progress.is_complete = True
        progress.save(update_fields=['is_complete'])
        _check_and_issue_certificate(user, lesson)
