# -*- coding: utf-8 -*-

import hmac
import os
import zlib
from datetime import datetime
from flask import Flask, redirect, request, jsonify, render_template, _app_ctx_stack, _request_ctx_stack
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, DateTime
from werkzeug import secure_filename
from werkzeug.exceptions import BadRequest
from flask.ext.script import Manager, Shell
from fdfs_client.client import Fdfs_client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Strings'

UPLOAD_PREFIX = '/root/python/web_storage/static/file'
DOWNLOAD_PREFIX = 'http://192.168.1.116'
DYNAMIC_DOWNLOAD_PREFIX = 'http://192.168.1.116/get_file'

connection_stack = _app_ctx_stack or _request_ctx_stack

Permissions = {'upload': 0x1, 'delete': 0x2, 'update': 0x3}
db_host = {'1': ('192.168.1.116:3306', '192.168.1.116:3307'), '2': ('192.168.1.116:3306', '192.168.1.116:3309')}
sharding_bit = 1

engine = create_engine('mysql+pymysql://python:python@192.168.1.116:3306/web_storage?charset=utf8')
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine), scopefunc=connection_stack.__ident_func__)
session = sessionmaker(autocommit=False, autoflush=False)

db_session = None
Base = declarative_base()

manager = Manager(app)


def make_shell_context():
    return dict(app=app, User=User, File=File)
manager.add_command("shell", Shell(make_context=make_shell_context))


class User(Base):
    __tablename__ = 'ekoss_user'
    user_id = Column(Integer, primary_key=True)
    user_access_key= Column(String(128), unique=True, nullable=False)
    user_secret_key= Column(String(128), unique=True, nullable=False)
    user_ins_time = Column(DateTime, default=datetime.now)
    user_upd_time = Column(TIMESTAMP, nullable=False)
    user_role = Column(String(20), nullable=False)
    user_pro_line = Column(String(20), nullable=False)
    user_privilege = Column(Integer, nullable=False)
    user_black_list = Column(Text)
    user_white_list = Column(Text)

    def can(self, permission):
        return (self.user_privilege & permission) == permission


class File(Base):
    __tablename__ = 'ekoss_file'
    file_id = Column(Integer, primary_key=True)
    fdfs_id = Column(String(128), unique=True)
    file_url = Column(Text)
    file_name = Column(String(256), nullable=False)
    file_size = Column(String(32))
    file_status = Column(Integer, nullable=False)
    file_access_key = Column(String(256), nullable=False)
    file_crc32 = Column(String(32), nullable=False)
    file_web_ip = Column(String(32), nullable=False)
    file_group_name = Column(String(32))
    file_remote_name = Column(String(256))
    file_ins_time = Column(DateTime, default=datetime.now)
    file_upd_time = Column(TIMESTAMP, nullable=False)

    def save_fs(self):
        import uuid
        new_file_name = '{0}{1}'.format(uuid.uuid4().hex, self.file_name)
        tmp_path = os.path.join(UPLOAD_PREFIX, new_file_name)
        self.file_name = new_file_name
        self.f_obj.save(tmp_path)
        self.tmp_path = tmp_path

    def save_fastfs(self):
        client = Fdfs_client('/etc/fdfs/client.conf')
        rv = client.upload_by_filename(self.tmp_path)
        return rv

    def normal_response(self):
        if self.put_policy in ('0', '3'):
            response = jsonify({"status": 0, "file_id": self.file_id, "file_name": self.file_name, "file_url": self.file_url})
        else:
            response = jsonify({"status": 0, "file_id": self.file_id, "file_url": self.file_url})
        return response


def get_host(file_name=None):
    if file_name:
        import hashlib
        md5 = hashlib.md5(file_name).hexdigest()
        host = []
        for i in range(sharding_bit):
            host.append(str(ord(md5[i]) % 2 + 1))
        return ''.join(host)

def get_file_name():
    print request.url
    if request.method == 'POST' and request.form['file_name']:
        return get_host(request.form['file_name'])
    elif request.method == 'GET' and request.url.endswith(u'/upload_test'):
       return None
    elif request.method == 'GET' and request.args['file_name']:
        return get_host(request.args['file_name'])
    else:
       return None

def get_engine(host):
    final_engine = None
    if host:
        final_engine = None
        engine1 = 'mysql+pymysql://python:python@{0}/web_storage?charset=utf8'.format(db_host[host][0])
        engine2 = 'mysql+pymysql://python:python@{0}/web_storage?charset=utf8'.format(db_host[host][1])
        for i in (engine1, engine2):
            engine = create_engine(i)
            try:
                engine.execute('SELECT 1').scalar()
            except Exception:
                continue
            final_engine = engine
            break
    return final_engine


@app.before_request
def bind_engine():
    global db_session
    host = get_file_name()
    engine = get_engine(host)
    if engine:
        session.configure(bind=engine)
        db_session = scoped_session(session, scopefunc=connection_stack.__ident_func__)
    else:
        pass


@app.teardown_appcontext
def shutdown_session(exception=None):
    if db_session:
        db_session.remove()


def split_token(token):
    if len(token.split(':')) == 3:
        return token.split(':')[0], token.split(':')[1], token.split(':')[2]


def check_token(put_policy, file_name, secret_key, token):
    hmac_obj = hmac.new(secret_key)
    hmac_obj.update('{0} + {1}'.format(put_policy, file_name).encode('base64'))
    return hmac_obj.hexdigest().encode('base64').rstrip() == token


def generate_token(put_policy, file_name, secret_key):
    hmac_obj = hmac.new(secret_key)
    hmac_obj.update('{0} + {1}'.format(put_policy, file_name).encode('base64'))
    return hmac_obj.hexdigest().encode('base64')


def file_crc32(file_path):
    crc = 0
    with open(file_path, 'rb') as f:
        for block in _file_iter(f, 1024 * 8):
            crc = zlib.crc32(block, crc) & 0xFFFFFFFF
    return crc


def _file_iter(input_stream, size, offset=0):
    input_stream.seek(offset)
    d = input_stream.read(size)
    while d:
        yield d
        d = input_stream.read(size)


def check_crc(file_path, crc):
    return file_crc32(file_path) == crc


def get_local_ip(ifname='eth0'):
    import socket
    import fcntl
    import struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    ret = socket.inet_ntoa(inet[20:24])
    return ret


def bad_response(file_name, info):
    response = jsonify({"status": 0, "file_name": file_name, "error": info})
    return response


class GeneralError(ValueError):
    pass


class DBError(Exception):
    pass


class ConnetionError(DBError):
    pass


@app.errorhandler(GeneralError)
def validation_error(e):
    return bad_response(e.args[0], e.args[1])


#@app.errorhandler(DBError)
#def DBError_error(e):
#    return bad_response(e)


def basic_auth_process():
    access_key, token_part, put_policy = split_token(request.form['token'])
    user = db_session.query(User).filter_by(user_access_key=access_key).first()
#   if user and request.form['put_policy'] != put_policy.decode('base64'):
#       return 'access key wrong or put_policy not consistant'

    secret_key = user.user_secret_key.encode('utf8')

    if put_policy in ('1', '2'):
        permission = Permissions['upload']
    elif put_policy in ('4', '5'):
        permission = Permissions['update']
    else:
        permission = Permissions['delete']

    if not user.can(permission):
        return 'user has no permission'

    if not check_token(put_policy, request.form['file_name'], secret_key, token_part):
        return 'secret key wrong'
#   if put_policy.decode('base64') in ('0', '1'):
    if request.form['put_policy'] in ('0', '1'):
        file = File()
        file.file_access_key = access_key
#       file.put_policy = put_policy.decode('base64')
    else:
        file = db_session.query(File).filter_by(file_id=request.form['file_id']).first()
    file.put_policy = request.form['put_policy']
    return file


def basic_file_process():
    rv = basic_auth_process()
    if isinstance(rv, str):
        raise GeneralError(request.form['file_name'], rv)
    file = rv
    file.file_web_ip = get_local_ip()
    f = request.files['file_test']
    file.f_obj = f
    file.file_name = secure_filename(file.f_obj.filename)
    file.save_fs()
    if not check_crc(file.tmp_path, int(request.form['crc32'], 16)):
        raise GeneralError(request.form['file_name'], 'crc32 not match')
    file.file_crc32 = int(request.form['crc32'], 16)
    return file


@app.route('/upload', methods=['POST'])
def upload():
    file = basic_file_process()
    if file.put_policy == '0':
        rv = file.save_fastfs()
        file.fdfs_id = file.file_remote_name = rv['Remote file_id']
        file.file_size = rv['Uploaded size']
        file.file_group_name = rv['Group name']
        file.file_url = '{0}/{1}'.format(DOWNLOAD_PREFIX, file.fdfs_id)
        file.file_status = 4
    else:
        file.file_status = 3
        db_session.add(file)
        db_session.commit()
        file.file_url = '{0}/{1}'.format(DYNAMIC_DOWNLOAD_PREFIX, file.file_id)
    db_session.add(file)
    db_session.commit()
    response = file.normal_response()
    return response


@app.route('/update', methods=['POST'])
def update():
    file = basic_file_process()
    if file.put_policy == '3':
        rv = file.save_fastfs()
        file.fdfs_id = file.file_remote_name = rv['Remote file_id']
        file.file_size = rv['Uploaded size']
        file.group_name = rv['Group name']
        file.file_url = '{0}/{1}'.format(DOWNLOAD_PREFIX, file.fdfs_id)
        file.file_status = 6
    else:
        file.file_status = 5
        file.file_url = DYNAMIC_DOWNLOAD_PREFIX
    db_session.add(file)
    db_session.commit()
    response = file.normal_response()
    return response


@app.route('/delete', methods=['POST'])
def delete():
    rv = basic_auth_process()
    if isinstance(rv, str):
        raise GeneralError(request.form['file_name'], rv)
    file = rv
    file.file_status = 1
    db_session.add(file)
    db_session.commit()
    response = file.normal_response()
    return response


@app.route('/upload_test', methods=['GET'])
def upload_test():
    print request.args
    return render_template('upload_simple.html')


@app.route('/update_test', methods=['GET'])
def update_test():
    return render_template('update_simple.html')


@app.route('/delete_test', methods=['GET'])
def delete_test():
    return render_template('delete_simple.html')


@app.route('/get_file', methods=['GET'])
def get_file():
    if request.args['file_name'] and request.args['file_id']:
        file = db_session.query(File).filter_by(file_id=request.args['file_id']).first()
        print file
        if file and file.file_url:
            return file.file_url


if __name__ == '__main__':
    manager.run()
