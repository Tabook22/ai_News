from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

public = '''

# ---------- Question of the day ----------

def _question_clean(value, limit):
    text = re.sub(r'[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]', '', value or '').strip()
    return text[:limit]


def _question_for(day=None):
    """The published question for a date, or the latest past question."""
    today = day or _gulf_today()
    return (DailyQuestion.query
            .filter(DailyQuestion.is_published.isnot(False))
            .filter(DailyQuestion.question_date <= today)
            .order_by(DailyQuestion.question_date.desc(), DailyQuestion.id.desc())
            .first())


@app.route('/question', methods=['GET', 'POST'])
def question_of_day():
    ar = get_lang_pref() == 'ar'
    requested = None
    raw_date = (request.args.get('date') or '').strip()
    if raw_date:
        try:
            requested = datetime.date.fromisoformat(raw_date)
        except ValueError:
            requested = None

    question = _question_for(requested) if requested else _question_for()
    if question is None:
        return render_template('question_v3.html', question=None, answered=False,
                               answer_count=0, approved_answers=[], ar=ar,
                               archive_url=url_for('question_archive'))

    answered_key = f'qotd_answered_{question.id}'
    if request.method == 'POST':
        if session.get(answered_key):
            return redirect(url_for('question_of_day', date=question.question_date.isoformat()))
        if request.form.get('website'):  # honeypot
            session[answered_key] = True
            return redirect(url_for('question_of_day', date=question.question_date.isoformat()))
        answer_text = _question_clean(request.form.get('answer_text'), 1200)
        display_name = _question_clean(request.form.get('display_name'), 80).replace('\\n', ' ')
        year = _question_clean(request.form.get('year'), 40).replace('\\n', ' ')
        if len(answer_text) < 20:
            flash('Please write at least 20 characters so your answer has substance.' if not ar
                  else 'اكتب 20 حرفًا على الأقل حتى تكون إجابتك ذات معنى.', 'error')
            return redirect(url_for('question_of_day', date=question.question_date.isoformat()))
        if request.form.get('question_id') and str(question.id) != request.form.get('question_id'):
            flash('That question is no longer the current one.' if not ar
                  else 'لم يعد هذا السؤال هو السؤال الحالي.', 'error')
            return redirect(url_for('question_of_day'))
        db.session.add(QuestionAnswer(
            question_id=question.id,
            answer_text=answer_text,
            display_name=display_name,
            year=year,
        ))
        db.session.commit()
        session[answered_key] = True
        flash('Answer received. Read the model answer below.' if not ar
              else 'وصلت إجابتك. اقرأ الإجابة النموذجية أدناه.', 'success')
        return redirect(url_for('question_of_day', date=question.question_date.isoformat()))

    answered = bool(session.get(answered_key))
    approved = (QuestionAnswer.query
                .filter_by(question_id=question.id, is_approved=True)
                .order_by(QuestionAnswer.created_at.desc())
                .limit(5).all())
    answer_count = QuestionAnswer.query.filter_by(question_id=question.id).count()
    return render_template('question_v3.html', question=question, answered=answered,
                           answer_count=answer_count, approved_answers=approved, ar=ar,
                           archive_url=url_for('question_archive'))


@app.route('/question/archive')
def question_archive():
    ar = get_lang_pref() == 'ar'
    rows = (DailyQuestion.query
            .filter(DailyQuestion.is_published.isnot(False))
            .filter(DailyQuestion.question_date <= _gulf_today())
            .order_by(DailyQuestion.question_date.desc(), DailyQuestion.id.desc())
            .limit(60).all())
    return render_template('question_archive.html', questions=rows, ar=ar)

'''
anchor = "@app.route('/library')\ndef reference_library():"
if "def question_of_day(" not in s:
    if anchor in s:
        s = s.replace(anchor, public + anchor, 1)
        print("public question routes added")
    else:
        print("QUESTION PUBLIC ANCHOR MISSING")

admin = '''

@app.route('/desk/questions')
@login_required
def questions_admin():
    questions = (DailyQuestion.query
                 .order_by(DailyQuestion.question_date.desc(), DailyQuestion.id.desc())
                 .all())
    return render_template('questions_admin.html', questions=questions)


@app.route('/desk/questions/new', methods=['GET', 'POST'])
@login_required
def add_question():
    if request.method == 'POST':
        question = DailyQuestion(question_date=_gulf_today(), question_en='')
        error = _apply_question_form(question)
        if error:
            flash(error, 'error')
            return render_template('question_form.html', question=None,
                                   form=request.form, today=_gulf_today())
        db.session.add(question)
        db.session.commit()
        flash('Question of the day added.', 'success')
        return redirect(url_for('questions_admin'))
    return render_template('question_form.html', question=None, form=None, today=_gulf_today())


@app.route('/desk/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = DailyQuestion.query.get_or_404(question_id)
    if request.method == 'POST':
        error = _apply_question_form(question)
        if error:
            flash(error, 'error')
        else:
            db.session.commit()
            flash('Question updated.', 'success')
            return redirect(url_for('questions_admin'))
    return render_template('question_form.html', question=question, form=None, today=_gulf_today())


@app.route('/desk/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    question = DailyQuestion.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('questions_admin'))


def _apply_question_form(question):
    question_en = _question_clean(request.form.get('question_en'), 1200)
    if not question_en:
        return 'The English question is required.'
    raw_date = (request.form.get('question_date') or '').strip()
    try:
        question_date = datetime.date.fromisoformat(raw_date)
    except ValueError:
        question_date = _gulf_today()
    clash = (DailyQuestion.query.filter(DailyQuestion.question_date == question_date)
             .filter(DailyQuestion.id != (question.id or 0)).first())
    if clash:
        return 'There is already a question for that date.'
    reading_url = (request.form.get('reading_url') or '').strip()
    if reading_url and not reading_url.startswith(('/', 'http://', 'https://')):
        return 'The reading link must be a site path or an http(s) URL.'
    question.question_date = question_date
    question.question_en = question_en
    question.question_ar = _question_clean(request.form.get('question_ar'), 1200)
    question.reading_title = _question_clean(request.form.get('reading_title'), 300)
    question.reading_url = reading_url
    question.reading_source = _question_clean(request.form.get('reading_source'), 160)
    question.hint_en = _question_clean(request.form.get('hint_en'), 500)
    question.hint_ar = _question_clean(request.form.get('hint_ar'), 500)
    question.answer_en = _question_clean(request.form.get('answer_en'), 4000)
    question.answer_ar = _question_clean(request.form.get('answer_ar'), 4000)
    question.is_published = bool(request.form.get('is_published'))
    return None


@app.route('/desk/questions/<int:question_id>/answers')
@login_required
def question_answers_admin(question_id):
    question = DailyQuestion.query.get_or_404(question_id)
    return render_template('question_answers.html', question=question,
                           answers=question.answers)


@app.route('/desk/questions/answers/<int:answer_id>/<action>', methods=['POST'])
@login_required
def question_answer_action(answer_id, action):
    answer = QuestionAnswer.query.get_or_404(answer_id)
    if action == 'approve':
        answer.is_approved = True
    elif action == 'unapprove':
        answer.is_approved = False
    elif action == 'delete':
        db.session.delete(answer)
    db.session.commit()
    flash('Answer updated.', 'success')
    return redirect(url_for('question_answers_admin', question_id=answer.question_id))

'''
anchor2 = "@app.route('/desk/library')\n@login_required\ndef library_admin():"
if "def questions_admin(" not in s:
    if anchor2 in s:
        s = s.replace(anchor2, admin + anchor2, 1)
        print("admin question routes added")
    else:
        print("QUESTION ADMIN ANCHOR MISSING")

p.write_text(s, encoding="utf-8")
