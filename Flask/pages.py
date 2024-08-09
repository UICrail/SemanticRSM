from flask import Blueprint

bp = Blueprint('pages', __name__)

@bp.route('/')
def home():
    return "SemanticRSM home page"

@bp.route('/about')
def about():
    return "About SemanticRSM"