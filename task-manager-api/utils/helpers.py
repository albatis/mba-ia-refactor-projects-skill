from datetime import datetime, timezone
import re


def utcnow():
    # datetime.utcnow() está deprecated desde Python 3.12; mantemos o valor
    # "naive" (sem tzinfo) para permanecer comparável com os DateTime já
    # armazenados no banco, que também são naive.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def validate_email(email):

    if re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
        return True
    return False

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_string, '%d/%m/%Y')
        except (ValueError, TypeError):
            return None

def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False

def process_task_data(data, existing_task=None):
    result = {}

    if 'title' in data:
        title = data['title']
        if title:
            title = title.strip()
            if len(title) >= 3 and len(title) <= 200:
                result['title'] = title
            else:
                return None, 'Título deve ter entre 3 e 200 caracteres'
        else:
            return None, 'Título não pode ser vazio'

    if 'description' in data:
        result['description'] = data['description']

    if 'status' in data:
        valid_statuses = ['pending', 'in_progress', 'done', 'cancelled']
        if data['status'] in valid_statuses:
            result['status'] = data['status']
        else:
            return None, 'Status inválido'

    if 'priority' in data:
        try:
            p = int(data['priority'])
            if p >= 1 and p <= 5:
                result['priority'] = p
            else:
                return None, 'Prioridade deve ser entre 1 e 5'
        except (ValueError, TypeError):
            return None, 'Prioridade inválida'

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if parsed:
                result['due_date'] = parsed
            else:
                return None, 'Data inválida'
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        if type(tags) == list:
            result['tags'] = ','.join(tags)
        else:
            result['tags'] = tags

    return result, None

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
