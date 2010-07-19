import sys
import cgi
import os 
import re
import uuid
import logging

sys.path.append('./pymods')
import simplejson

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
    timestamp_create = db.DateTimeProperty(auto_now_add=True)
    timestamp_mod = db.DateTimeProperty(auto_now=True)

class Comment(db.Model):
    msg = db.StringProperty()
    inst = db.ReferenceProperty(Institution)
    timestamp = db.DateTimeProperty(auto_now=True)
    user = db.UserProperty(auto_current_user=True)
    
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

    ## Error page (TODO -- put this in a super class and inherit. Yuck.
    def error_page(self, error_msg):
        error_msg = "There was an error: <b>%s</b>.  <br><br>Press <b>back button</b> and fix." % error_msg
        template_values = {"error_msg":error_msg}
        path = os.path.join(os.path.dirname(__file__), 'templates/error.tmpl')
        self.response.out.write(template.render(path, template_values))
        pass

    ## Start an institution, parsing tabular text
    def post(self):
        if users.get_current_user():
            logging.debug(users.get_current_user().nickname())
            pass
        try:
            ## store institution
            inst = Institution()
            inst.name = self.request.get('inst_name').strip()
            if inst.name == "":
                self.error_page("Empty institution name")
                return
            inst.unguessable_id = str(uuid.uuid4())
            inst.put()

            ## store first comment
            comm = Comment()
            comm.msg = "Initial upload.  " + self.request.get('comment')
            comm.inst = inst.key()
            comm.put()

            ## store buildings, normalizing all non alphanumerics to '_' so ID's work
            bldg_table_str = str(self.request.get('bldg_table')).strip()
            if bldg_table_str == "":
                self.error_page("Empty building field")
                return 
            for line in re.split("\n+", bldg_table_str):
                line2 = line.strip()
                elems = re.split("[\s,;|]+", line2, 2)
                bldg_name = re.sub('\W', '_', elems[2]) 
                bldg = Building(
                    inst = inst.key(),
                    pt = db.GeoPt(float(elems[0]), float(elems[1])),
                    name = bldg_name)
                bldg.put()
                pass

            ## view the results (redirect)
            self.redirect('/view?unguessable_id=%s' % inst.unguessable_id)
            return
        
        except Exception, exc:
            error_msg = "There was a problem parsing input data.  Python message: \"%s\".<br>  Press <b>back button</b> and fix." % exc
            template_values = {"error_msg":error_msg}
            path = os.path.join(os.path.dirname(__file__), 'templates/error.tmpl')
            self.response.out.write(template.render(path, template_values))
            pass


class ViewInst(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            logging.debug(users.get_current_user().nickname())

        ## get all buildings + comments for institution's id
        unguessable_id = self.request.get('unguessable_id')
        sqlstr = "select *  from Institution where unguessable_id = :1"
        query = db.GqlQuery(sqlstr, unguessable_id)
        if (query.count() != 1) or (not unguessable_id):
            logging.error("ViewInst.get: bad number records returned for inst: %s" % query.count())
            self.redirect('/') 
            return
        inst = query.fetch(query.count())[0]
        
        ## pass to template and write
        template_values = {'unguessable_id':inst.unguessable_id,
                           'inst_name':inst.name,
                           'comments':inst.comment_set.order('-timestamp'),
                           'bldg_table':inst.building_set}
        path = os.path.join(os.path.dirname(__file__), 'templates/view.tmpl')
        self.response.out.write(template.render(path, template_values))


class UpdateInst(webapp.RequestHandler):
    ## Update positions of institution, using JSON from AJAX
    def post(self):
        ## params
        unguessable_id = self.request.get('unguessable_id')
        model = simplejson.loads(self.request.get('model'))
        comment = self.request.get('comment')

        ## update buildings
        instq = db.GqlQuery("SELECT * FROM Institution WHERE unguessable_id = :1", unguessable_id)
        inst = instq.fetch(instq.count())[0]
        logging.debug('UpdateInst.post() unguessable_id: %s', inst.unguessable_id)
        if inst:
            logging.debug("UpdateInst.post: %s %s" % (inst.unguessable_id, inst.name))
            for bldg in inst.building_set: 
                a,b = model[bldg.name]['latlong'].strip('()').split(', ')
                logging.debug("UpdateInst.post():updating building: %s. (%s, %s)." % (bldg.name, a, b))
                bldg.pt = db.GeoPt(float(a), float(b))
                bldg.put()
                pass
            comm = Comment()
            comm.msg = "Points updated.  " + comment  #comm_msg
            comm.inst = inst.key()
            comm.put()
            pass
        else:
            logging.error("UpdateInst.post: Unable to find unguessable_id = %s. Returning." % unguessable_id)
            return
            pass
        

######
def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/', MainPage),
                                      ('/upload', UploadInst),
                                      ('/view', ViewInst),
                                      ('/update', UpdateInst)],
                                     debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
  main()
