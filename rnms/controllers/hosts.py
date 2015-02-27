# -*- coding: utf-8 -*-
#
# This file is part of the RoseNMS
#
# Copyright (C) 2012-2015 Craig Small <csmall@enc.com.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>
#
#
""" Hosts controller """

# turbogears imports
from tg import expose, validate, flash, tmpl_context, url, predicates, request
from tg.decorators import require

# third party imports
#from tg.i18n import ugettext as _
#from repoze.what import predicates
from formencode import validators

# project specific imports
from rnms.lib import structures
from rnms.lib import permissions
from rnms.lib.table import jqGridTableFiller, DiscoveryFiller
from rnms.lib.base import BaseGridController
from rnms.model import DBSession, Host, Event, Attribute
from rnms.widgets import InfoBox, MainMenu, HostMap, HostGrid, EventGrid
from rnms.widgets.attribute import MiniAttributeGrid, DiscoveredAttsGrid


class HostsController(BaseGridController):
    allow_only = permissions.host_ro

    @expose('rnms.templates.host.index')
    @validate(validators={'z': validators.Int(min=1)})
    def index(self, z=None, *args, **kw):
        if tmpl_context.form_errors:
            self.process_form_errors()
            return {}
        if z is not None:
            griddata = {'z': z}
        else:
            griddata = {}

        w = HostGrid()
        return dict(page='host', main_menu=MainMenu,
                    w=w, griddata=griddata)

    @expose('json')
    def griddata(self, **kw):
        class HostFiller(structures.host, jqGridTableFiller):
            pass
        return super(HostsController, self).griddata(HostFiller, {}, **kw)

    @expose('json')
    def gridindex(self, **kw):
        class HostFiller(structures.host_list, jqGridTableFiller):
            pass
        return super(HostsController, self).griddata(HostFiller, {}, **kw)

    @expose('json')
    @validate(validators={'h': validators.Int(min=1)})
    @require(permissions.host_rw)
    def griddiscover(self, **kw):
        if tmpl_context.form_errors:
            self.process_form_errors()
            return {}
        filler = DiscoveryFiller()
        return filler.get_value(**kw)

    @expose('rnms.templates.host.detail')
    @validate(validators={'h': validators.Int(min=1)})
    def _default(self, h):
        if tmpl_context.form_errors:
            self.process_form_errors()
            return dict(page='host', main_menu=MainMenu)
        host = Host.by_id(h)
        if host is None:
            flash('Host ID#{} not found'.format(h), 'error')
            return dict(page='host', main_menu=MainMenu)
        vendor, devmodel = host.snmp_type()
        highest_alarm = Event.host_alarm(host.id)
        if highest_alarm is None:
            host_state = 'Up'
        else:
            host_state = highest_alarm.event_state.display_name.capitalize()

        detailsbox = InfoBox()
        detailsbox.title = 'Host Details'
        attributes_grid = MiniAttributeGrid()
        events_grid = EventGrid()
        return dict(page='host', main_menu=MainMenu,
                    host=host, vendor=vendor, devmodel=devmodel,
                    host_state=host_state,
                    attributes_grid=attributes_grid,
                    grid_data={'h': h},
                    detailsbox=detailsbox,
                    events_grid=events_grid)

    @expose('rnms.templates.map.host')
    @validate(validators={
        'z': validators.Int(min=1), 'events': validators.Bool(),
        'alarmed': validators.Bool()})
    def map(self, z=None, events=False, alarmed=False, **kw):
        """ Display a map of the Hosts, optionally filtered by Zone id
        and optionally showing events for those hosts
        """
        if tmpl_context.form_errors:
            self.process_form_errors()
            return dict(page='host', main_menu=MainMenu)
        hmap_infobox = InfoBox()
        hmap_infobox.title = 'Host Map'
        hmap_infobox.child_widget = HostMap()
        hmap_infobox.child_widget.zone_id = z
        hmap_infobox.child_widget.alarmed_only = alarmed
        if events:
            events_grid = EventGrid()
            events_grid.zone_id = z
        else:
            events_grid = None
        return dict(page='hosts', main_menu=MainMenu,
                    host_map=hmap_infobox, events_grid=events_grid)

    @expose('rnms.templates.host.discover')
    @validate(validators={'h': validators.Int(min=2)})
    def discover(self, h):
        if tmpl_context.form_errors:
            self.process_form_errors()
            return dict(page='host', main_menu=MainMenu)
        w = DiscoveredAttsGrid()
        edit_url = url('/attributes/add_disc', {'h': h})
        return dict(page='host', main_menu=MainMenu,
                    w=w, edit_url=edit_url,
                    griddata={'h': h})

    @expose('rnms.templates.widgets.select')
    def option(self):
        """ Return a list of hosts. If user has required
        permission it shows all, else just their ones """
        if permissions.host_ro:
            hosts = DBSession.query(Host.id, Host.display_name)
        else:
            hosts = DBSession.query(Host.id, Host.display_name).filter(
                Host.id.in_(
                    DBSession.query(Attribute.host_id).filter(
                        Attribute.user_id == request.identity['user'].user_id)
                )
            )
        items = hosts.all()
        items.insert(0, ('', '-- Choose Host --'))
        return dict(items=items)
