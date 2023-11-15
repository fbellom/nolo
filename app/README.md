# nolo

Backend App to serve Data Information to Nolo Reader App.

CCOM6035 Project 2023

## version: 1.0.0

## Curl Calls

curl -X POST -v \
-H "Content-Type: application/json" \
-d '{"id":123456789,"title":"EmpleadoDelMes","author" : "zovaca"}' \
http://localhost:5000/book | jq .

Like a Book
curl -X POST -v \
-H "Content-Type: application/json" \
http://localhost:5000/like/book/123456789 | jq .
