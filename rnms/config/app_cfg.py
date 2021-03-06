# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in RoseNMS.

This file complements development/deployment.ini.

Please note that **all the argument values are strings**. If you want to
convert them into boolean, for example, you should use the
:func:`paste.deploy.converters.asbool` function, as in::
    
    from paste.deploy.converters import asbool
    setting = asbool(global_conf.get('the_setting'))
 
"""
#import warnings
#warnings.filterwarnings('ignore', category=DeprecationWarning)

from tg.configuration import AppConfig

import rnms
from rnms import model
from rnms.lib import app_globals, helpers


base_config = AppConfig()
base_config.renderers = []

# True to prevent dispatcher from striping extensions
# For example /socket.io would be served by "socket_io" method instead of "socket"
base_config.disable_request_extensions = False

# Set None to disable escaping punctuation characters to "_" when dispatching methods.
# Set to a function to provide custom escaping.
base_config.dispatch_path_translator = True 

base_config.prefer_toscawidgets2 = True

base_config.package = rnms

#Enable json in expose
base_config.renderers.append('json')

#Enable genshi in expose to have a lingua franca for extensions and pluggable apps
#you can remove this if you don't plan to use it.
#base_config.renderers.append('genshi')

#Set the default renderer
base_config.default_renderer = 'mako'
base_config.renderers.append('mako')

#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = rnms.model
base_config.DBSession = rnms.model.DBSession
# Configure the authentication backend

# YOU MUST CHANGE THIS VALUE IN PRODUCTION TO SECURE YOUR APP
base_config.sa_auth.cookie_secret = "ChangeME"

base_config.auth_backend = 'sqlalchemy'

# what is the class you want to use to search for users in the database
base_config.sa_auth.user_class = model.User

from tg.configuration.auth import TGAuthMetadata


#This tells to TurboGears how to retrieve the data for your user
class ApplicationAuthMetadata(TGAuthMetadata):
    def __init__(self, sa_auth):
        self.sa_auth = sa_auth

    def authenticate(self, environ, identity):
        user = self.sa_auth.dbsession.query(self.sa_auth.user_class).\
            filter_by(user_name=identity['login']).first()
        if user and user.validate_password(identity['password']):
            return identity['login']

    def get_user(self, identity, userid):
        return self.sa_auth.dbsession.query(self.sa_auth.user_class).\
            filter_by(user_name=userid).first()

    def get_groups(self, identity, userid):
        return [g.group_name for g in identity['user'].groups]

    def get_permissions(self, identity, userid):
        return [p.permission_name for p in identity['user'].permissions]

base_config.sa_auth.dbsession = model.DBSession

base_config.sa_auth.authmetadata = ApplicationAuthMetadata(base_config.sa_auth)

# You can use a different repoze.who Authenticator if you want to
# change the way users can login
#base_config.sa_auth.authenticators = [('myauth', SomeAuthenticator()]

# You can add more repoze.who metadata providers to fetch
# user metadata.
# Remember to set base_config.sa_auth.authmetadata to None
# to disable authmetadata and use only your own metadata providers
#base_config.sa_auth.mdproviders = [('myprovider', SomeMDProvider()]

# override this if you would like to provide a different who plugin for
# managing login and logout of your application
base_config.sa_auth.form_plugin = None

# override this if you are using a different charset for the login form
#base_config.sa_auth.charset = 'utf-8'

# You may optionally define a page where you want users to be redirected to
# on login:
base_config.sa_auth.post_login_url = '/post_login'

# You may optionally define a page where you want users to be redirected to
# on logout:
base_config.sa_auth.post_logout_url = '/post_logout'
