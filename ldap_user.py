<%
# -*- coding: utf-8 -*-
import ldap
import ldap.modlist as modlist
import MySQLdb
import time
from datetime import datetime, timedelta
from dateutil.tz import tzlocal, tzutc

conString = 'cn=username,cn=Users,dc=organization,dc=domain,dc=ru'
l = ldap.initialize('ldap://ldap_server')
l.set_option(ldap.OPT_REFERRALS, 0)
try:
    l.simple_bind_s(conString, "password")
    print "OK"
except ldap.INVALID_CREDENTIALS:
    print "Your username or password is incorrect."
except ldap.LDAPError as err:
    print err

def searchLDAP(l, searchFilter=""):
    baseDN = "dc=organization,dc=domain,dc=ru"
    searchScope = ldap.SCOPE_SUBTREE
    retrieveAttributes = None 
    try:
	ldap_result_id = l.search(baseDN, searchScope, searchFilter, retrieveAttributes)
	result_set = []
	while 1:
	    result_type, result_data = l.result(ldap_result_id, 0)
	    if (result_data == []):
		break
	    else:
		if result_type == ldap.RES_SEARCH_ENTRY:
		    result_set.append(result_data)
	if len(result_set) == 0:
    	    return None
	return result_set
    except ldap.LDAPError, e:
	return None

def convert_ad_timestamp(timestamp):
    epoch_start = datetime(year=1601,month=1,day=1,tzinfo=tzutc())
    seconds_since_epoch = timestamp/10**7
    return epoch_start + timedelta(seconds=seconds_since_epoch)

dbhost = "inet_db_server"
dbuser = "inet_db_user"
dbpassword = "inet_db_password"
dbname = "inet_db_name"
maildbhost = "mail_db_server"
maildbuser = "mail_db_user"
maildbpassword = "mail_db_password"
maildbname = "mail_db_name"
fired = "55c48b7802963" # id группы "Уволенные"
userAccount = {	2:"<b style=\"color: #f00;\">UF_ACCOUNT_DISABLE</b>", 
		64:"UF_PASSWD_CANT_CHANGE", 
		512:"UF_NORMAL_ACCOUNT",
		65536: "UF_DONT_EXPIRE_PASSWD",
		8388608: "<b style=\"color: #f00;\">UF_PASSWORD_EXPIRED</b>"}

try:
    con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpassword, db=dbname)
except:
    #
%>
<h1>Connection error</h1>
<%
    quit()
con.set_character_set("utf8")
cur = con.cursor()
cur.execute("SET NAMES 'utf8'")
#cur.execute("SET CHARACTER SET utf8;")
cur.execute("SET CHARACTER SET latin1;")
cur.execute("SET character_set_connection=utf8;")

tabnumber = form.getfirst("tabnumber")
firstname = form.getfirst("firstname")
find = form.getfirst("find")
user = form.getfirst("user")
inet_block = form.getfirst("inet_block")
inet_unblock = form.getfirst("inet_unblock")
inet_fired = form.getfirst("inet_fired")
user_fired = form.getfirst("user_fired")

%>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="Cache-Control" content="no-cache">
</head>
<body>
<form method="post" action="?" >
    Табельный номер: <input type="text" name="tabnumber">
    Фамилия: <input type="text" name="firstname">
    <input type="submit" name="find" value="OK">
</form>
<%
if find is not None:
    if tabnumber is not None and tabnumber.strip() != "":
	tabnumber = tabnumber.strip()
	searchFilter = "(|(sAMAccountName=usr" + tabnumber + ")(sAMAccountName=user" + tabnumber + ")" \
	+ "(sAMAccountName=tabnum" + tabnumber + "))"
    elif firstname is not None and firstname.strip() != "":
	firstname = firstname.strip()
	searchFilter = "(&(objectCategory=person)(objectClass=user)(displayName=" + firstname + " *))"
    else:
	searchFilter = ""
    if searchFilter != "":
	#
%>
<table border="0" width="100%">
<%
	result_set = searchLDAP(l, searchFilter)
	if result_set is not None:
	    for user in result_set:
		for id in user:
		    #
%>
    <tr>
	<td><a href="?user=<%= id[1]['sAMAccountName'][0] %>"><%= id[1]['displayName'][0] %></a></td>
    </tr>
<%
		    #
		#
	    #
	#
%>
</table>
<%
	#
    #
elif user is not None:
    if inet_block is not None:
	sql = "UPDATE squidusers SET enabled=-1 WHERE nick=\"%s\"" % (MySQLdb.escape_string(user))
	cur.execute(sql)
    elif inet_unblock is not None:
	sql = "UPDATE squidusers SET enabled=1 WHERE nick=\"%s\"" % (MySQLdb.escape_string(user))
	cur.execute(sql)
    elif inet_fired is not None:
        sql = "UPDATE squidusers SET enabled=-1, squidusers.group=\"%s\" WHERE nick=\"%s\"" % (fired, MySQLdb.escape_string(user))
        cur.execute(sql)
    #
%>
<table border="1" width="100%">
    <tr>
	<td valign="top">Пользователь
<%
    #
    if user_fired is not None:
	searchFilter = "(|(sAMAccountName=" + user + "))"
	result_set = searchLDAP(l, searchFilter)
	if result_set is not None:
	    old_dn = result_set[0][0][0]
	    try:
		old_info = result_set[0][0][1]['info'][0]
    		info = old_info + "\r\n" + old_dn
	    except:
		old_info = ""
		info = old_dn
	    try:
		old_mail = result_set[0][0][1]['mail'][0]
    		info = info + "\r\nE-mail: " + result_set[0][0][1]['mail'][0]
	    except:
		old_mail = ""
	    old = {'info': old_info, 'mail': old_mail, 'userAccountControl': result_set[0][0][1]['userAccountControl'][0]}
	    new = {'info': info, 'mail': '', 'userAccountControl': str(int(result_set[0][0][1]['userAccountControl'][0]) | 2)}
	    ldif = modlist.modifyModlist(old,new)
	    l.modify_s(old_dn,ldif)
    	    l.rename_s(old_dn, 'cn=' + result_set[0][0][1]['cn'][0], 'OU=Уволенные,dc=organization,dc=domain,dc=ru')
    	    sql = "UPDATE squidusers SET enabled=-1, squidusers.group=\"%s\" WHERE nick=\"%s\"" % (fired, MySQLdb.escape_string(user))
    	    cur.execute(sql)
	    if old_mail !="":
		try:
		    mailcon = MySQLdb.connect(host=maildbhost, user=maildbuser, passwd=maildbpassword, db=maildbname)
		except:
		    #
%>
<h1>Mail connection error</h1>
<%
		    quit()
		mailcur = mailcon.cursor()
    		sql = "UPDATE mailbox SET active=0 WHERE username=\"%s\"" % (MySQLdb.escape_string(result_set[0][0][1]['mail'][0]))
    		mailcur.execute(sql)

    searchFilter = "(|(sAMAccountName=" + user + "))"
    result_set = searchLDAP(l, searchFilter)
    if result_set is not None:
	dn = result_set[0][0][0]
	displayName = result_set[0][0][1]['displayName'][0]
	userAccountControl = result_set[0][0][1]['userAccountControl'][0]
	try:
    	    email = result_set[0][0][1]['mail'][0]
	except:
	    email = ""
	#
	if dn.find("OU=Уволенные,dc=organization,dc=domain,dc=ru") and (int(result_set[0][0][1]['userAccountControl'][0]) & 2):
	    disable_user_fired = " disabled"
	else:
	    disable_user_fired = ""
	#
	if result_set[0][0][1]['lastLogon'][0] == 0:
	    lastLogon = convert_ad_timestamp(int())
	    lastLogon_tz = lastLogon.astimezone(tzlocal())
	    lastLogon_print = lastLogon_tz.strftime("%d-%m-%Y %H:%M:%S %Z")
	else:
	    lastLogon_print = "NA"
%>
<form method="post" action="?user=<%= user %>">
    <input type="submit" name="user_fired" value="Увольнение"<%= disable_user_fired%>>
</form>
	    <%= displayName %><br/>
	    Last Logon: <%= lastLogon_print %><br/>
<%
	for flag, val in userAccount.items():
	    if int(userAccountControl) & flag:
%>
	<%= flag %> -> <%= val %><br/>
<%
	#
    else:
	email = ""
    #
%>
	</td>
	<td valign="top">Интернет
<%
    sql = "SELECT u.id,u.nick,u.family,u.name,u.soname,u.quotes,u.size,u.enabled,g.nick,g.name " \
	    "FROM squidusers AS u, groups AS g WHERE u.group=g.name AND u.nick=\"%s\"" % (MySQLdb.escape_string(user))
    cur.execute(sql)
    data =  cur.fetchall()
    try:
	username = data[0]
    except:
	username = ""
    if username != "":
	disable_block = ""
	disable_unblock = ""
	disable_fired = ""
	if username[7] == -1 and username[9] == fired: #Заблокировано и в группе "Уволенные"
	    disable_fired = " disabled"
	    disable_block = " disabled"
	    disable_unblock = " disabled"
	elif username[7] == -1:
	    disable_block = " disabled"
	elif username[7] == 0:
	    disable_block = " disabled"
	    disable_unblock = " disabled"
	elif username[7] == 1:
	    disable_unblock = " disabled"
	#
%>
<form method="post" action="?user=<%= user %>">
    <input type="submit" name="inet_block" value="Заблокировать"<%= disable_block%>>
    <input type="submit" name="inet_unblock" value="Разблокировать"<%= disable_unblock%>>
    <input type="submit" name="inet_fired" value="Увольнение"<%= disable_fired%>>
    <p><%= username[8] %><br/>
    <%= username[2] %> <%= username[3] %> <%= username[4] %><br/>
    <%= round(username[6]/1024/1024) %>/<%= username[5] %></p>
</form>
<%
	#
    #
%>
	</td>
    </tr>
    <tr>
	<td colspan="2">
<%
    if email == "":
        #
%>
Нет почты
<%
	#
    else:
        #
%>
<%= email %>
<%
    #
%>
	</td>
    </tr>
</table>