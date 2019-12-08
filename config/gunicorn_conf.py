import os

if False:
    # Sever Socket
    host = '0.0.0.0'  # Flaskは外部公開を許していないので、基本これ
    port = os.getenv('PORT', 5000)

    bind = str(host) + ':' + str(port)

    # Debugging
    reload = True

    # Logging
    accesslog = '-'

    # Proc Name
    proc_name = 'Tsume-Shogi Provider'
else:
    bind = '127.0.0.1:8090'
