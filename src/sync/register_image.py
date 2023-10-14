from datetime import datetime
import os
import sys

import psycopg2


if __name__ == '__main__':
    args = sys.argv
    target_dir = args[1]

    user_name, file_name = target_dir.split('/')[-2:]
    result_name = os.listdir(os.path.join(target_dir, 'results'))[0]
    created_at = datetime.strptime(file_name, '%Y%m%d_%H%M%S')
    created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S') + '+09'

    connection = psycopg2.connect("host=db port=5432 user=postgres password=password")
    cur = connection.cursor()
    cur.execute("insert into photos (title, state, user_name, result_name, created_at) " \
        + "values ('{}', {}, '{}', '{}', '{}')".format(file_name, 0, user_name, result_name, created_at_str)
    )
    connection.commit()
