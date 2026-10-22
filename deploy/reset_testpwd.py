import sys
sys.path.insert(0, '/tmp/testapp')
import db
db.init_db('/tmp/testapp/data/test.db')
db.set_pass_hash(db.hash_password('admin'))
db.clear_must_change()
db.set_sec('sec_pass_minlen', '8')
db.set_sec('sec_pass_classes', '2')
db.set_sec('sec_login_delay', '1')
db.set_sec('sec_bind_ip', '0')
print('测试密码已重置为 admin,策略复位')
