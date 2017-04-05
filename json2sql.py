import sys
import json

crl = set([
    "BramGruneir",
    "RaduBerinde",
#    "WillHaack",
    "a-robinson",
    "asubiotto",
    "andreimatei",
    "arjunravinarayan",
    "bdarnell",
    "benesch",
    "cockroach-teamcity",
    "cuongdo",
#    "d4l3k",
    "danhhz",
    "dianasaur323",
    "dt",
    "eisenstatdavid",
    "irfansharif",
    "jordanlewis",
    "jseldess",
    "jess-edwards",
    "kkaneda",
    "knz",
    "kuanluo",
    "maxlang",
    "mberhault",
    "mjibson",
    "mrtracy",
    "nvanbenschoten",
    "paperstreet",
    "petermattis",
    "spencerkimball",
    "sploiselle",
    "tamird",
    "tschottdorf",
    "vivekmenezes",
])

inputfile = sys.stdin
if len(sys.argv) > 1:
    inputfile = open(sys.argv, 'r')

data = json.load(inputfile)

print("""
drop table if exists reported;
drop table if exists assigned;
drop table if exists issues;
drop table if exists users;
create table if not exists issues (
   number int primary key,
   title text,
   category text,
   state text,
   milestone string,
   created timestamp,
   closed timestamp,
   updated timestamp,
   assignee string,
   url string,
   description text );
create table if not exists users (
   name text primary key,
   crl int );
create table if not exists reported (
   user text,
   issue int,
   primary key (user, issue),
   foreign key(user) references users(name),
   foreign key(issue) references issues(id)
);
create table if not exists assigned (
   user text,
   issue int,
   foreign key(user) references users(name),
   foreign key(issue) references issues(id)
);
""")

users = set()
for issue in data:
    for name in issue['Assignees']:
        users.add(name)
    users.add(issue['Reporter'])

for name in users:
    incrl = name in crl and '1' or '0'
    print("insert into users(name, crl) values('{name}', {incrl});".format(**locals()))
    
for issue in data:
    title=issue['Title'].replace("'", "''")
    text=issue['Text'].replace("'", "''")
    
    category=''
    pref=issue['Title'].split(':',1)
    if len(pref) > 1 and ' ' not in pref[0]:
        category=pref[0]
                                 
    print("""
    insert into issues(number,title,category,state,milestone,assignee,created,updated,closed,description,url)
    values({Number}, '{title}', '{category}', '{State}', '{Milestone}', '{Assignee}', '{Created}', '{Updated}', '{Closed}', '{text}', '{URL}');
    insert into reported(issue, user) values({Number}, '{Reporter}');
    """.format(**locals(),**issue))
    for name in issue['Assignees']:
        print("""insert into assigned(issue, user) values({Number}, '{name}');""".format(**locals(),**issue))
        
