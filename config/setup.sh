sudo service mysql restart

echo -e 'Enter Root Password of MySQL: \c '
read ROOT_PASSWORD

echo -e 'Enter desired password for MySQL user : calendar_admin : \c '
read ADMIN_PASSWORD

mysql -u root --password=$ROOT_PASSWORD -e 'create database calendar_db character set utf8;'

mysql -u root --password=$ROOT_PASSWORD -e 'grant all on calendar_db.* to "calendar_admin" identified by "'$ADMIN_PASSWORD'";'
mysql -u root --password=$ROOT_PASSWORD -e "create user 'calendar_admin'@'%' identified by '$ADMIN_PASSWORD';"
mysql -u root --password=$ROOT_PASSWORD -e "grant all on calendar_db.* to 'calendar_admin';"
mysql -u root --password=$ROOT_PASSWORD -e 'flush privileges;'

sudo service mysql restart

#Install timezone
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p




mysql -u root -p
create database calendar_db;
create user 'calendar_admin'@'%' identified by 'MYSQLcalendar!123';
grant all on calendar_db.* to 'calendar_admin';
flush privileges;