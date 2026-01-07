#!/bin/zsh

cd /Users/yeshiwangchk/Desktop/BEAC || exit

source venv/bin/activate

python app.py &

sleep 5

open -a Safari http://127.0.0.1:5001

echo "BEAC is running. Close this window only when done."
read
