#!/bin/bash

md5 () {
    local dir=$1
    if [ `ls $dir | wc -l` -gt 0 ];then
    local j=`echo $dir | sed 's@$@/*@'`
    for i in $j
    do
        if [ -d "$i" ];then
            md5 "$i"
        else
            md5sum "$i"
        fi
    done
    fi
}

while read line
do
    if [ -d "$line" ];then
        if [ `ls $line | wc -l` -gt 0 ];then
            md5 "$line"
        fi
    else
        md5sum "$line"
    fi
done < $1
