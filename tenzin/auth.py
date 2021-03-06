from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, flash, session, current_app
)
from flask_login import login_user, logout_user, login_required
from . import (cbpro, oauth)
from .models import User
from .db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('auth.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@bp.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    resp.raise_for_status()
    profile = resp.json()

    if not profile['verified_email']:
        return "User email not available or not verified by Google.", 400

    print(profile)
    db = get_db()
    existing_user = User.objects(user_id=profile['id']).first()
    session.permanent = True  # session is 15 mins defined in the config file
    # session["access_token"] = token

    if existing_user is None:
        existing_user = User(user_id=profile['id'], email=profile['email']).save()
    login_user(existing_user)
    return redirect(url_for("cbpro.index"))


@bp.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    logout_user()
    return redirect(url_for('cbpro.index'))


@bp.route('/hello')
@login_required
def hello():
    return "<h1>hello</h1>"


def is_valid_token(token):
    expires_at = token['expires_at']
