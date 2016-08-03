from datetime import datetime,timedelta
import humanize
import sqlite3
import sys
import time

conn = sqlite3.connect("issues.db")
cu = conn.cursor()
c = conn.cursor()

def header(user):
   print("""<!DOCTYPE html>
   <html lang=en>
   <head>
   <title>CockroachDB Issue dashboard - %s</title>
   <meta charset="utf-8">
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <!-- Latest compiled and minified CSS -->
   <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
   <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap-theme.min.css">
   <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"></script>
   <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script></head>
   <body><div class="container-fluid">
   <style type=text/css>
   td { font-family: monospace !important; }
   .hr { height: 3px; color: solid black; }
   </style>
   <script>
   $(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
   });
   </script>
   <h1>Issue dashboard for %s</h1>
   """ % (user,user))
   print("<p>Generated on {0} UTC</p>".format(time.asctime(time.gmtime())))
   print("<div id='accordion' class='panel-group'>")

def footer():
    print('<script src="/sorttable.js"></script>')
    print("</div></div></body></html>")

def genSection(title, divid, query, colorize):
   rows = list(enumerate(c.execute(query)))
   nrows = len(rows)
   print("""
    <div class="panel panel-default">
     <div class="panel-heading">
      <h2 class="panel-title">
       <a data-toggle="collapse" data-parent="#accordion" href="#{divid}">
       <strong>{title} ({nrows} issues)</strong>
       </a>
      </h2>
     </div>
     <div id="{divid}" class="panel-collapse collapse">
      <div class="panel-body">
    """.format(**locals()))
   print("""
      <table class='sortable table table-condensed table-striped table-hover table-responsive'><thead>
   <tr><th>#</th><th>Issue</th><th>Reporter</th><th>Assignee</th><th>Created</th><th>Updated</th><th>Milestone</th></tr>
   </thead><tbody>""")
   for i,row in rows:
       created = datetime.strptime(row[3],'%Y-%m-%dT%H:%M:%SZ')
       hcreated = humanize.naturaltime(created)
       url = row[0].strip()
       number = row[1]
       title = row[2]
       reporter = row[4]
       assignee = row[5]
       updated = datetime.strptime(row[6],'%Y-%m-%dT%H:%M:%SZ')
       hupdated = humanize.naturaltime(updated)
       milestone = row[7]
       status = colorize(locals())
       print("""<tr class='{status}'>
       <td>{i}</td>
       <td><a href="{url}">{number} - {title}</a></td>
       <td><a href="https://github.com/{reporter}">{reporter}</a></td>
       <td><a href="https://github.com/{assignee}">{assignee}</a></td>
       <td><span class='hidden'>{created}</span>{hcreated}</td>
       <td><span class='hidden'>{updated}</span>{hupdated}</td>
       <td>{milestone}</td>
   </tr>""".format(**locals()))

   print("""</tbody></table>""")
   print("""
      </div>
     </div>
    </div>
    """)
   return nrows

def newIsBad(meta):
    old = meta['created'] <= datetime.now()-timedelta(weeks=1)
    if not old:
        return 'danger'
    return ''
def oldIsBad(meta):
    if meta['updated'] < datetime.now()-timedelta(days=90):
        return 'danger'
    if meta['updated'] < datetime.now()-timedelta(weeks=1):
        return 'warning'
    return ''

ops = {
   "extIssues" : {
      'title':  "Issues from external users without milestone nor assignment",
      'query':  """
     select issues.url, issues.number, issues.title, issues.created, reported.user, issues.assignee, issues.updated, issues.milestone
       from issues 
            join reported on reported.issue=issues.number 
            join users on reported.user=users.name and users.crl=0
      where not exists(select * from assigned where issue=issues.number) 
        and issues.milestone=""
   order by issues.category,issues.updated
      """},
   "yourIssues":{
      'title': "Issues assigned to you",
      'query': """
     select issues.url, issues.number, issues.title, issues.created, reported.user, issues.assignee, issues.updated, issues.milestone
       from issues 
            join reported on reported.issue=issues.number 
            join assigned on assigned.issue=issues.number and assigned.user='{0}'
   order by issues.category,issues.updated
      """},
   "unIssues":{
      'title':"Issues created by you that nobody is working on",
      'query': """
     select issues.url, issues.number, issues.title, issues.created, reported.user, issues.assignee, issues.updated, issues.milestone
       from issues 
            join reported on reported.issue=issues.number and reported.user='{0}'
      where not exists (select * from assigned where issue=issues.number)
   order by issues.category,issues.updated
      """},
   "childIssues":{
      'title': "Issues you created that someone else is working on",
      'query': """
     select issues.url, issues.number, issues.title, issues.created, reported.user, issues.assignee, issues.updated, issues.milestone
       from issues 
            join reported on reported.issue=issues.number and reported.user='{0}'
      where (select count(*) from assigned where issue=issues.number and user<>'{0}') > 0
   order by issues.category,issues.updated
      """},
}

ksorted = sorted(ops.keys())

index = open('dashboard/index.html', 'w')
sys.stdout = index
header('all')
print("<p>Key:</p><table class='table table-condensed' style='width:auto'>")
for i, k in enumerate(ksorted):
   print("<tr><td>%c</td><td>%s</td>" % (chr(ord('A')+i), ops[k]['title']))
print("</table>")

print("<table class='table sortable table-condensed table-striped table-hover table-responsive' style='width:auto'><thead>")
print("<tr><th>User</th>")
for i, k in enumerate(ksorted):
   print("<th><a href='#' data-toggle='tooltip' title='%s'>%c</a></th>" % (ops[k]['title'], chr(ord('A')+i)))
print("</tr></thead><tbody>")

for row in cu.execute("select name, lower(name) as lname from users where crl=1 order by lname"):
    user = row[0]
    luser = row[1]
    sys.stdout = open('dashboard/' + user + '.html', 'w')
    header(user)
    extra = []

    info = {}
    for k,v in ops.items():
       info[k] = genSection(v['title'], k, v['query'].format(user), oldIsBad)

    footer()
    sys.stdout.close()
 
    sys.stdout = index
    print("<tr><td><a href='%s.html'>%s</a> <a href='https://github.com/%s'><span class='glyphicon glyphicon-leaf'></span></a>" % (
       user, luser, user))
    for i, k in enumerate(ksorted):
       print("<td><a href='%s.html' data-toggle='tooltip' title='%s'>%d</a></th>" % (user, ops[k]['title'], info[k]))
    print("</tr>")
    
sys.stdout = index
print("</tbody></table>")
footer()
index.close()
