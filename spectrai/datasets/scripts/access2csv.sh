#!/bin/bash

for table in $(mdb-tables -1 "$1"); do
    echo "Export table $table"
    mdb-export "$1" "$table" > "$2/$table.csv"
done


