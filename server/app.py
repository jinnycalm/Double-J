import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import psycopg2
from config import settings

load_dotenv()

# DB class
class RemoteDBConnection:
    def __init__(self, config):
        self.config = config
        self.tunnel = None
        self.connection = None

    def __enter__(self):
        '''SSH Tunnel 생성 및 DB 연결'''
        try:
            self.tunnel = SSHTunnelForwarder(
                (settings.SSH_HOST, settings.SSH_PORT),
                ssh_username=settings.SSH_USER,
                ssh_pkey=settings.SSH_KEY_PATH,
                remote_bind_address=(settings.RDS_HOST, settings.RDS_PORT)
            )
            self.tunnel.start()
            print('SSH 터널 생성 완료')

            self.connection = psycopg2.connect(
                host='127.0.0.1',
                port=self.tunnel.local_bind_port,
                user=settings.RDS_USER,
                database=settings.RDS_DB_NAME,
                password=settings.RDS_PASSWORD,
            )

            return self.connection        # with 구문에서 사용할 connection 객체 반환

        except Exception as e:
            self.__exit__(None, None, None)
            print(f'SSH 터널 생성 실패 : {e}')
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):      # with 구문에서 에러 발생 시 정보를 담아 보내는 객체들
        '''DB 연결 종료 및 SSH Tunnel 종료'''
        if self.connection:
            self.connection.close()
            print('DB 연결 종료')
        if self.tunnel:
            self.tunnel.stop()
            print('SSH 터널 종료')


def call_users(conn):
    '''users 테이블 조회'''
    with conn.cursor() as cur:
        cur.execute('select * from "Users";')
        result = cur.fetchone()
        return print(f'결과: {result}')


if __name__ == '__main__':
    try:
        with RemoteDBConnection(settings) as conn:
            result = call_users(conn)
    except Exception as e:
        print(f'DB 연결 실패 : {e}')