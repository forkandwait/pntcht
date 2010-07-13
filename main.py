import cgi
import simplejson
import os 
import sys
import re
import uuid

import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class Institution(db.Model):
    name = db.StringProperty()
    unguessable_id = db.StringProperty()


class Building(db.Model):
    name = db.StringProperty() 
    pt = db.GeoPtProperty()
    inst = db.ReferenceProperty(Institution)

	
class MainPage(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            usernick = users.get_current_user().nickname()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            usernick = 'Anonymous'

        template_values = {
            'username':usernick,
            'url': url,
            'url_linktext': url_linktext,
            }
        path = os.path.join(os.path.dirname(__file__), 'templates/index.tmpl')
        self.response.out.write(template.render(path, template_values))


class UploadInst(webapp.RequestHandler):
    ## Start an institution, parsing tabular text
    def post(self):
        if users.get_current_user():
            logging.debug(users.get_current_user().nickname())
            pass
        
        inst_name = self.request.get('inst_name')
        inst_rec = db.GqlQuery("SELECT * FROM Institution WHERE name = :1", inst_name).fetch(1)
        
        ## store institution
        inst = Institution()
        inst.name = inst_name
        inst.unguessable_id = str(uuid.uuid4())
        inst.put()

        ## store buildings
        bldg_table_str = str(self.request.get('bldg_table'))
        for line in re.split("\n+", bldg_table_str):
            line2 = line.strip()
            elems = re.split("\s+", line2, 2)
            bldg = Building(
                inst = inst.key(),
                pt = db.GeoPt(float(elems[0]), float(elems[1])),
                name = elems[2])
            bldg.put()
            pass
        
        ## view the results
        self.redirect('/view?unguessable_id=%s' % inst.unguessable_id)
        pass


class ViewInst(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            logging.debug(users.get_current_user().nickname())

        ## get all buildings for institution's id, pass to a template, write
        unguessable_id = self.request.get('unguessable_id')
        if not unguessable_id:
            self.redirect('/') 
            return
        sqlstr = "select *  from Institution where unguessable_id = :1"
        query = db.GqlQuery(sqlstr, unguessable_id)
        
        if query.count() != 1:
            logging.error("ViewInst.get: bad number records returned for inst: %s" % query.count())
            self.redirect('/') 
            return
        inst = query.fetch(query.count())[0]
        bldg_table = inst.building_set
        template_values = {'unguessable_id':inst.unguessable_id,
                           'inst_name':inst.name,
                           'bldg_table':bldg_table}
        path = os.path.join(os.path.dirname(__file__), 'templates/view.tmpl')
        self.response.out.write(template.render(path, template_values))


class UpdateInst(webapp.RequestHandler):
    ## Update positions of institution, using JSON from AJAX
    def post(self):
        unguessable_id = self.request.get('unguessable_id')
        modeljson = self.request.get('model')
        model = simplejson.loads(modeljson)
        instq = db.GqlQuery("SELECT * FROM Institution WHERE unguessable_id = :1", unguessable_id)
        inst = instq.fetch(instq.count())[0]
        if inst: 
            for bldg in inst.building_set: 
                a,b = model[bldg.name]['pt'].strip('()').split(', ')
                bldg.pt = db.GeoPt(float(a), float(b))
                bldg.put()
                pass
        else:
            logging.error("UpdateInst.post: no institution returned from query")
            pass
        

######
application = webapp.WSGIApplication([('/', MainPage),
                                      ('/upload', UploadInst),
                                      ('/view', ViewInst),
                                      ('/update', UpdateInst)],
                                     debug=True)
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
