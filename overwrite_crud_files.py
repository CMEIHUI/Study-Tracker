from pathlib import Path

files = {
    Path('python/database/SubjectCrud.py'): 'from .SubjectCrud_repair import SubjectCrud\n\n__all__ = ["SubjectCrud"]\n',
    Path('python/database/TaskCrud.py'): 'from .TaskCrud_repair import TaskCrud\n\n__all__ = ["TaskCrud"]\n',
    Path('python/database/studyseesioncrud.py'): 'from .studyseesioncrud_repair import StudySessionCrud\n\n__all__ = ["StudySessionCrud"]\n',
}

for path, content in files.items():
    path.write_text(content, encoding='utf-8')
    print('wrote', path)
