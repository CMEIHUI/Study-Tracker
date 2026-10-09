from pathlib import Path  
import tempfile  
from datetime import date  
from database import DatabaseManager  
tmp = tempfile.TemporaryDirectory()  
db = DatabaseManager(str(Path(tmp.name) / 'studytracker.db'))  
db.add_task('Math', 'Finish algebra', 'Review', 'High', date.today().isoformat())  
task = db.get_all_tasks()[0]  
print('before', db.get_gamification_state())  
print('complete', db.complete_task(task[0]))  
print('after', db.get_gamification_state())  
conn = db.connect()  
print('profiles', conn.execute('select * from gamification_profiles').fetchall())  
print('events', conn.execute('select * from gamification_events').fetchall())  
conn.close()  
tmp.cleanup()  
