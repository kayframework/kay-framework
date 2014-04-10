# -*- coding: utf-8 -*-

"""
Kay generics rest.

# Copyright (c) 2008 Boomi, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

This file is originally developped in appengine-rest-server project
hosted at:
http://code.google.com/p/appengine-rest-server

Additional part (Adaption to Kay, parsing json data, etc..) is written
by Takashi Matsuo <tmatsuo@candit.jp>

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.

"""

import logging
import types
import logging
import re
import base64
from datetime import datetime
from xml.dom import minidom

import json
from google.appengine.ext import db
from google.appengine.api import memcache

from werkzeug.routing import (
    Rule, RuleTemplate, EndpointPrefix, Submount,
)
from werkzeug.exceptions import (
    NotFound, Forbidden, BadRequest, InternalServerError
)
from werkzeug import (
    Response, redirect
)
from werkzeug.utils import import_string
from werkzeug.routing import RequestRedirect

from kay.utils import (
    render_to_response, url_for
)
from kay.db import OwnerProperty
from kay.exceptions import NotAuthorized
from kay.i18n import gettext as _
from kay.i18n import lazy_gettext
from kay.routing import ViewGroup

from kay.generics import (
  OP_LIST, OP_SHOW, OP_CREATE, OP_UPDATE, OP_DELETE
)

def get_instance_type_name(value):
    """Returns the name of the type of the given instance."""
    return get_type_name(type(value))

def get_type_name(value_type):
    """Returns the name of the given type."""
    return value_type.__name__
    
METADATA_PATH = "metadata"

MAX_FETCH_PAGE_SIZE = 1000

XML_CLEANSE_PATTERN1 = re.compile(r"^(\d)")
XML_CLEANSE_REPL1 = r"_\1"
XML_CLEANSE_PATTERN2 = re.compile(r"[^a-zA-Z0-9]")
XML_CLEANSE_REPL2 = r"_"

EMPTY_VALUE = object()
MULTI_UPDATE_KEY = object()

KEY_PROPERTY_NAME = "key"
KEY_PROPERTY_TYPE = "KeyProperty"
KEY_QUERY_FIELD = "__key__"

TYPES_EL_NAME = "types"
TYPE_EL_NAME = "type"
LIST_EL_NAME = "list"
TYPE_ATTR_NAME = "type"
NAME_ATTR_NAME = "name"
ITEM_EL_NAME = "item"

DATA_TYPE_SEPARATOR = ":"

DATE_TIME_SEP = "T"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT_NO_MS = "%H:%M:%S"
DATE_TIME_FORMAT_NO_MS = DATE_FORMAT + DATE_TIME_SEP + TIME_FORMAT_NO_MS

TRUE_VALUE = "true"
TRUE_NUMERIC_VALUE = "1"

CONTENT_TYPE_HEADER = "Content-Type"
XML_CONTENT_TYPE = "application/xml"
TEXT_CONTENT_TYPE = "text/plain"
JSON_CONTENT_TYPE = "application/json"
METHOD_OVERRIDE_HEADER = "X-HTTP-Method-Override"

XML_ENCODING = "utf-8"
XSD_PREFIX = "xs"
XSD_ATTR_XMLNS = "xmlns:" + XSD_PREFIX
XSD_NS = "http://www.w3.org/2001/XMLSchema"
XSD_SCHEMA_NAME = XSD_PREFIX + ":schema"
XSD_ELEMENT_NAME = XSD_PREFIX + ":element"
XSD_COMPLEXTYPE_NAME = XSD_PREFIX + ":complexType"
XSD_SEQUENCE_NAME = XSD_PREFIX + ":sequence"
XSD_ANY_NAME = XSD_PREFIX + ":any"
XSD_ANNOTATION_NAME = XSD_PREFIX + ":annotation"
XSD_APPINFO_NAME = XSD_PREFIX + ":appinfo"
XSD_FILTER_PREFIX = "bm"
XSD_ATTR_FILTER_XMLNS = "xmlns:" + XSD_FILTER_PREFIX
XSD_FILTER_NS = "http://www.boomi.com/connector/annotation"
XSD_FILTER_NAME = XSD_FILTER_PREFIX + ":filter"
XSD_ATTR_MINOCCURS = "minOccurs"
XSD_ATTR_MAXOCCURS = "maxOccurs"
XSD_ATTR_NAMESPACE = "namespace"
XSD_ATTR_PROCESSCONTENTS = "processContents"
XSD_ATTR_NOFILTER = "ignore"
XSD_ANY_NAMESPACE = "##any"
XSD_LAX_CONTENTS = "lax"
XSD_NO_MIN = "0"
XSD_SINGLE_MAX = "1"
XSD_NO_MAX = "unbounded"

QUERY_OFFSET_PARAM = "offset"
QUERY_PAGE_SIZE_PARAM = "page_size"
QUERY_ORDERING_PARAM = "ordering"
QUERY_TERM_PATTERN = re.compile(r"^(f.._)(.+)$")
QUERY_PREFIX = "WHERE "
QUERY_JOIN = " AND "
QUERY_ORDERBY = " ORDER BY "
QUERY_ORDER_ASC = " ASC"
QUERY_ORDER_DESC = " DESC"
QUERY_LIST_TYPE = "fin_"

QUERY_EXPRS = {
    "feq_" : "%s = :%d",
    "flt_" : "%s < :%d",
    "fgt_" : "%s > :%d",
    "fle_" : "%s <= :%d",
    "fge_" : "%s >= :%d",
    "fne_" : "%s != :%d",
    QUERY_LIST_TYPE : "%s IN :%d"
    }

DATA_TYPE_TO_PROPERTY_TYPE = {
    "basestring" : db.StringProperty,
    "str" : db.StringProperty,
    "unicode" : db.StringProperty,
    "bool" : db.BooleanProperty,
    "int" : db.IntegerProperty,
    "long" : db.IntegerProperty,
    "float" : db.FloatProperty,
    "Key" : db.ReferenceProperty,
    "datetime" : db.DateTimeProperty,
    "date" : db.DateProperty,
    "time" : db.TimeProperty,
    "Blob" : db.BlobProperty,
    "Text" : db.TextProperty,
    "User" : db.UserProperty,
    "Category" : db.CategoryProperty,
    "Link" : db.LinkProperty,
    "Email" : db.EmailProperty,
    "GeoPt" : db.GeoPtProperty,
    "IM" : db.IMProperty,
    "PhoneNumber" : db.PhoneNumberProperty,
    "PostalAddress" : db.PostalAddressProperty,
    "Rating" : db.RatingProperty,
    "list" : db.ListProperty,
    "tuple" : db.ListProperty
    }

PROPERTY_TYPE_TO_XSD_TYPE = {
    get_type_name(db.StringProperty) : XSD_PREFIX + ":string",
    get_type_name(db.BooleanProperty) : XSD_PREFIX + ":boolean",
    get_type_name(db.IntegerProperty) : XSD_PREFIX + ":long",
    get_type_name(db.FloatProperty) : XSD_PREFIX + ":double",
    get_type_name(db.ReferenceProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.DateTimeProperty) : XSD_PREFIX + ":dateTime",
    get_type_name(db.DateProperty) : XSD_PREFIX + ":date",
    get_type_name(db.TimeProperty) : XSD_PREFIX + ":time",
    get_type_name(db.BlobProperty) : XSD_PREFIX + ":base64Binary",
    get_type_name(db.TextProperty) : XSD_PREFIX + ":string",
    get_type_name(db.UserProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.CategoryProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.LinkProperty) : XSD_PREFIX + ":anyURI",
    get_type_name(db.EmailProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.GeoPtProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.IMProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.PhoneNumberProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.PostalAddressProperty) : XSD_PREFIX + ":normalizedString",
    get_type_name(db.RatingProperty) : XSD_PREFIX + ":integer",
    KEY_PROPERTY_TYPE : XSD_PREFIX + ":normalizedString"
    }


def parse_date_time(dt_str, dt_format, dt_type, allows_microseconds):
    """Returns a datetime/date/time instance parsed from the given string using the given format info."""
    ms = None
    if(allows_microseconds):
        dt_parts = dt_str.rsplit(".", 1)
        dt_str = dt_parts.pop(0)
        if(len(dt_parts) > 0):
            ms = int(dt_parts[0].ljust(6,"0")[:6])
    dt = datetime.strptime(dt_str, dt_format)
    if(ms):
        dt = dt.replace(microsecond=ms)
    if(dt_type is datetime.date):
        dt = dt.date()
    elif(dt_type is datetime.time):
        dt = dt.time()
    return dt
    
def convert_to_valid_xml_name(name):
    """Converts a string to a valid xml element name."""
    name = re.sub(XML_CLEANSE_PATTERN1, XML_CLEANSE_REPL1, name)
    return re.sub(XML_CLEANSE_PATTERN2, XML_CLEANSE_REPL2, name)

def append_child(parent_el, name, content=None):
    """Returns a new xml element with the given name and optional text content appended to the given parent element."""
    doc = parent_el.ownerDocument
    el = doc.createElement(name)
    parent_el.appendChild(el)
    if content:
        el.appendChild(doc.createTextNode(content))
    return el

def xsd_append_sequence(parent_el):
    """Returns an XML Schema sub-sequence (complex type, then sequence) appended to the given parent element."""
    ctype_el = append_child(parent_el, XSD_COMPLEXTYPE_NAME)
    seq_el = append_child(ctype_el, XSD_SEQUENCE_NAME)
    return seq_el

def xsd_append_nofilter(parent_el):
    """Returns Boomi XML Schema no filter annotation appended to the given parent element."""
    child_el = append_child(parent_el, XSD_ANNOTATION_NAME)
    child_el = append_child(child_el, XSD_APPINFO_NAME)
    filter_el = append_child(child_el, XSD_FILTER_NAME)
    filter_el.attributes[XSD_ATTR_FILTER_XMLNS] = XSD_FILTER_NS
    filter_el.attributes[XSD_ATTR_NOFILTER] = TRUE_VALUE
    return filter_el

def xsd_append_element(parent_el, name, prop_type_name, min_occurs, max_occurs):
    """Returns an XML Schema element with the given attributes appended to the given parent element."""
    element_el = append_child(parent_el, XSD_ELEMENT_NAME)
    element_el.attributes[NAME_ATTR_NAME] = name
    type_name = PROPERTY_TYPE_TO_XSD_TYPE.get(prop_type_name, None)
    if type_name:
        element_el.attributes[TYPE_ATTR_NAME] = type_name
    if min_occurs is not None:
        element_el.attributes[XSD_ATTR_MINOCCURS] = min_occurs
    if max_occurs is not None:
        element_el.attributes[XSD_ATTR_MAXOCCURS] = max_occurs
    return element_el
    
def get_node_text(node_list, do_strip=False):
    """Returns the complete text from the given node list (optionally stripped) or None if the list is empty."""
    if(len(node_list) == 0):
        return None
    text = u""
    for node in node_list:
        if node.nodeType == node.TEXT_NODE:
            text += node.data
    if do_strip:
        text = text.strip()
    return text

def xml_to_json(xml_doc):
    doc_el = xml_doc.documentElement
    json_doc = {doc_el.nodeName : xml_node_to_json(doc_el)}

    return json.dumps(json_doc)

def xml_node_to_json(xml_node):
    if((len(xml_node.childNodes) == 1) and
       (xml_node.childNodes[0].nodeType == xml_node.TEXT_NODE)):
        return xml_node.childNodes[0].data
    else:
        json_node = {}
        
        for child_xml_node in xml_node.childNodes:
            new_child_json_node = xml_node_to_json(child_xml_node)
            cur_child_json_node = json_node.get(child_xml_node.nodeName, None)
            if(cur_child_json_node is None):
                cur_child_json_node = new_child_json_node
            else:
                # if we have more than one of the same type, turn the children into a list
                if(not isinstance(cur_child_json_node, types.ListType)):
                    cur_child_json_node = [cur_child_json_node]
                cur_child_json_node.append(new_child_json_node)
            json_node[child_xml_node.nodeName] = cur_child_json_node
            
        xml_node_attrs = xml_node.attributes
        for attr_name in xml_node_attrs.keys():
            json_node["@" + attr_name] = xml_node_attrs[attr_name].nodeValue

        return json_node

class PropertyHandler(object):
    """Base handler for Model properties which manages converting properties to and from xml.

    This implementation works for most properties which have simple to/from string conversions.
    
    """
    
    def __init__(self, property_name, property_type):
        self.property_name = property_name
        self.property_type = property_type

        # most types can be parsed from stripped strings, but don't strip text data
        self.strip_on_read = True
        if(isinstance(property_type, (db.StringProperty, db.TextProperty))):
            self.strip_on_read = False

    def get_query_field(self):
        """Returns the field name which should be used to query this property."""
        return self.property_name
            
    def can_query(self):
        """Returns True if this property can be used as a query filter, False otherwise."""
        return True
            
    def get_data_type(self):
        """Returns the type of data this property accepts."""
        return self.property_type.data_type
            
    def empty(self, value):
        """Tests a property value for empty in a manner specific to the property type."""
        return self.property_type.empty(value)

    def get_type_string(self):
        """Returns the type string describing this property."""
        return get_instance_type_name(self.property_type)

    def get_value(self, model):
        """Returns the value for this property from the given model instance."""
        return getattr(model, self.property_name)

    def get_value_as_string(self, model):
        """Returns the value for this property from the given model instance as a string (or EMPTY_VALUE if the value
        is empty as defined by this property type), used by the default write_xml_value() method."""
        value = self.get_value(model)
        if(self.empty(value)):
            return EMPTY_VALUE
        return self.value_to_string(value)

    def value_to_string(self, value):
        """Returns the given property value as a string, used by the default get_value_as_string() method."""
        return unicode(value)

    def value_from_string(self, value):
        """Returns the value for this property from the given string value (may be None), used by the default
        read_xml_value() method."""
        if((value is None) or (self.strip_on_read and not value)):
            return None
        if(not isinstance(value, self.get_data_type())):
            value = self.get_data_type()(value)
        return value

    def value_for_query(self, value):
        """Returns the value for this property from the given string value (may be None), for use in a query filter."""
        return self.value_from_string(value)
                
    def write_xml_value(self, parent_el, prop_xml_name, model):
        """Returns the property value from the given model instance converted to an xml element and appended to the
        given parent element."""
        value = self.get_value_as_string(model)
        if(value is EMPTY_VALUE):
            return None
        return append_child(parent_el, prop_xml_name, value)

    def read_xml_value(self, props, prop_el):
        """Adds the value for this property to the given property dict converted from an xml element."""
        value = self.value_from_string(get_node_text(prop_el.childNodes, self.strip_on_read))
        props[self.property_name] = value

    def write_xsd_metadata(self, parent_el, prop_xml_name):
        """Returns the XML Schema element for this property type appended to the given parent element."""
        prop_el = xsd_append_element(parent_el, prop_xml_name, self.get_type_string(), XSD_NO_MIN, XSD_SINGLE_MAX)
        if(not self.can_query()):
            xsd_append_nofilter(prop_el)
        return prop_el
    
        
class DateTimeHandler(PropertyHandler):
    """PropertyHandler for datetime/data/time property instances."""
    
    def __init__(self, property_name, property_type):
        super(DateTimeHandler, self).__init__(property_name, property_type)

        self.format_args = []
        if(isinstance(property_type, db.DateProperty)):
            self.dt_format = DATE_FORMAT
            self.dt_type = datetime.date
            self.allows_microseconds = False
        elif(isinstance(property_type, db.TimeProperty)):
            self.dt_format = TIME_FORMAT_NO_MS
            self.dt_type = datetime.time
            self.allows_microseconds = True
        elif(isinstance(property_type, db.DateTimeProperty)):
            self.dt_format = DATE_TIME_FORMAT_NO_MS
            self.dt_type = datetime
            self.allows_microseconds = True
            self.format_args.append(DATE_TIME_SEP)
        else:
            raise ValueError("unexpected property type %s for DateTimeHandler" % property_type)

    def value_to_string(self, value):
        """Returns the datetime/date/time value converted to the relevant iso string value."""
        value_str = value.isoformat(*self.format_args)
        # undo python's idiotic formatting irregularity
        if(self.allows_microseconds and not value.microsecond):
            value_str += ".000000"
        return unicode(value_str)

    def value_from_string(self, value):
        """Returns the datetime/date/time parsed from the relevant iso string value, or None if the string is empty."""
        if(not value):
            return None
        return parse_date_time(value, self.dt_format, self.dt_type, self.allows_microseconds)

    
class BooleanHandler(PropertyHandler):
    """PropertyHandler for boolean property instances."""
    
    def __init__(self, property_name, property_type):
        super(BooleanHandler, self).__init__(property_name, property_type)

    def value_to_string(self, value):
        """Returns the boolean value converted to a string value of 'true' or 'false'."""
        return unicode(value).lower()

    def value_from_string(self, value):
        """Returns the boolean value parsed from the given string value: True for the strings 'true' (any case) and
        '1', False for all other non-empty strings, and None otherwise."""
        if(not value):
            return None
        value = value.lower()
        return ((value == TRUE_VALUE) or (value == TRUE_NUMERIC_VALUE))

    
class TextHandler(PropertyHandler):
    """PropertyHandler for (large) text property instances."""
    
    def __init__(self, property_name, property_type):
        super(TextHandler, self).__init__(property_name, property_type)

    def can_query(self):
        """Text properties may not be used in query filters."""
        return False


class BlobHandler(PropertyHandler):
    """PropertyHandler for blob property instances."""
    
    def __init__(self, property_name, property_type):
        super(BlobHandler, self).__init__(property_name, property_type)

    def can_query(self):
        """Blob properties may not be used in query filters."""
        return False
            
    def value_to_string(self, value):
        """Returns a blob value converted to a Base64 encoded string."""
        return base64.b64encode(str(value))

    def value_from_string(self, value):
        """Returns a blob value parsed from a Base64 encoded string, or None if the string is empty."""
        if(not value):
            return None
        return base64.b64decode(value)


class ReferenceHandler(PropertyHandler):
    """PropertyHandler for reference property instances."""
    
    def __init__(self, property_name, property_type):
        super(ReferenceHandler, self).__init__(property_name, property_type)

    def get_data_type(self):
        """Returns the db.Key type."""
        return db.Key
            
    def get_value(self, model):
        """Returns the key of the referenced model instance."""
        return self.property_type.get_value_for_datastore(model)

    
class KeyHandler(ReferenceHandler):
    """PropertyHandler for primary 'key' of a Model instance."""
    
    def __init__(self):
        super(KeyHandler, self).__init__(KEY_PROPERTY_NAME, None)

    def empty(self, value):
        """Returns True if the value is any value which evaluates to False, False otherwise."""
        return not value

    def get_query_field(self):
        """Returns the special key query field name '__key__'"""
        return KEY_QUERY_FIELD
                
    def get_value(self, model):
        """Returns the key of the given model instance if it has been saved, EMPTY_VALUE otherwise."""
        if(not model.is_saved()):
            return EMPTY_VALUE
        return model.key()

    def get_type_string(self):
        """Returns the custom 'KeyProperty' type name."""
        return KEY_PROPERTY_TYPE

    
class ListHandler(PropertyHandler):
    """PropertyHandler for lists property instances."""
    
    def __init__(self, property_name, property_type):
        super(ListHandler, self).__init__(property_name, property_type)
        self.sub_handler = get_property_handler(ITEM_EL_NAME,
                                                DATA_TYPE_TO_PROPERTY_TYPE[get_type_name(property_type.item_type)]())

    def get_type_string(self):
        """Returns the type string 'ListProperty:' + <sub_type_string>."""
        return super(ListHandler, self).get_type_string() + DATA_TYPE_SEPARATOR + self.sub_handler.get_type_string()

    def can_query(self):
        """Can query is based on the list element type."""
        return self.sub_handler.can_query()
            
    def value_for_query(self, value):
        """Returns the value for a query filter based on the list element type."""
        return self.sub_handler.value_from_string(value)
                
    def write_xml_value(self, parent_el, prop_xml_name, model):
        """Returns a list element containing value elements for the property from the given model instance appended to
        the given parent element."""
        values = self.get_value(model)
        if(not values):
            return None
        list_el = append_child(parent_el, prop_xml_name)
        for value in values:
            append_child(list_el, ITEM_EL_NAME, self.sub_handler.value_to_string(value))
        return list_el

    def read_xml_value(self, props, prop_el):
        """Adds a list containing the property values to the given property dict converted from an xml list element."""
        values = []
        sub_props = {}
        for item_node in prop_el.childNodes:
            if((item_node.nodeType == item_node.ELEMENT_NODE) and (str(item_node.nodeName) == ITEM_EL_NAME)):
                self.sub_handler.read_xml_value(sub_props, item_node)
                values.append(sub_props.pop(ITEM_EL_NAME))
        props[self.property_name] = values

    def write_xsd_metadata(self, parent_el, prop_xml_name):
        """Returns the XML Schema list element for this property type appended to the given parent element."""
        list_el = super(ListHandler, self).write_xsd_metadata(parent_el, prop_xml_name)
        seq_el = xsd_append_sequence(list_el)
        xsd_append_element(seq_el, ITEM_EL_NAME, self.sub_handler.get_type_string(), XSD_NO_MIN, XSD_NO_MIN)
        return list_el
    
class DynamicPropertyHandler(object):
    """PropertyHandler for dynamic properties on Expando models."""
    
    def __init__(self, property_name):
        self.property_name = property_name

    def write_xml_value(self, parent_el, prop_xml_name, model):
        """Returns the property value from the given model instance converted to an xml element (with a type
        attribute) of the appropriate type and appended to the given parent element."""
        value = getattr(model, self.property_name)
        prop_handler = self.get_handler(None, value)
        prop_el = prop_handler.write_xml_value(parent_el, prop_xml_name, model)
        if prop_el:
            prop_el.attributes[TYPE_ATTR_NAME] = prop_handler.get_type_string()
        return prop_el

    def read_xml_value(self, props, prop_el):
        """Adds the value for this property to the given property dict converted from an xml element, either as a
        StringProperty value if no type attribute exists or as the type given in a type attribute."""
        attrs = prop_el.attributes
        
        if(attrs.has_key(TYPE_ATTR_NAME)):
            prop_type = str(attrs[TYPE_ATTR_NAME].value)
            self.get_handler(prop_type, None).read_xml_value(props, prop_el)
            return

        props[self.property_name] = get_node_text(prop_el.childNodes)

    def get_handler(self, property_type, value):
        """Returns the relevant PropertyHandler based on the given property_type string or property value."""
        prop_args = []
        sub_handler = None
        if(value is not None):
            property_type = DATA_TYPE_TO_PROPERTY_TYPE[get_instance_type_name(value)]
            if(property_type is db.ListProperty):
                prop_args.append(type(value[0]))

        if(isinstance(property_type, basestring)):
            if DATA_TYPE_SEPARATOR in property_type:
                property_type, sub_property_type = property_type.split(DATA_TYPE_SEPARATOR, 1)
                sub_handler = get_property_handler(ITEM_EL_NAME, getattr(db, sub_property_type)())
                prop_args.append(sub_handler.get_data_type())
            property_type = getattr(db, property_type)

        property_type = property_type(*prop_args)

        return get_property_handler(self.property_name, property_type)


def get_property_handler(property_name, property_type):
    """Returns a PropertyHandler instance with the given name appropriate for the given type."""
    if(isinstance(property_type, (db.DateTimeProperty, db.TimeProperty, db.DateProperty))):
        return DateTimeHandler(property_name, property_type)
    elif(isinstance(property_type, db.BooleanProperty)):
        return BooleanHandler(property_name, property_type)
    elif(isinstance(property_type, db.ReferenceProperty)):
        return ReferenceHandler(property_name, property_type)
    elif(isinstance(property_type, db.BlobProperty)):
        return BlobHandler(property_name, property_type)
    elif(isinstance(property_type, db.TextProperty)):
        return TextHandler(property_name, property_type)
    elif(isinstance(property_type, db.ListProperty)):
        return ListHandler(property_name, property_type)
    
    return PropertyHandler(property_name, property_type)


class Lazy(object):
    """Utility class for enabling lazy initialization of decorated properties."""
    
    def __init__(self, calculate_function):
        self._calculate = calculate_function

    def __get__(self, obj, _=None):
        if obj is None:
            return self
        value = self._calculate(obj)
        setattr(obj, self._calculate.func_name, value)
        return value


class ModelHandler(object):
    """Handler for a Model (or Expando) type which manages converting instances to and from xml."""

    def __init__(self, model_name, model_type):
        self.model_name = model_name
        self.model_type = model_type
        self.key_handler = KeyHandler()

    @Lazy
    def property_handlers(self):
        """Lazy initializer for the property_handlers dict."""
        prop_handlers = {}
        for prop_name, prop_type in self.model_type.properties().iteritems():
            prop_handler = get_property_handler(prop_name, prop_type)
            prop_handlers[convert_to_valid_xml_name(prop_handler.property_name)] = prop_handler
        return prop_handlers
            
    def is_dynamic(self):
        """Returns True if this Model type supports dynamic properties (is a subclass of Expando), False otherwise."""
        return issubclass(self.model_type, db.Expando)

    def get(self, key):
        """Returns the model instance with the given key."""
        return self.model_type.get(key)

    def create(self, props):
        """Returns a newly created model instance with the given properties (as a keyword dict)."""
        return self.model_type(**props)

    def get_all(self, limit, offset, ordering, query_expr, query_params):
        """Returns all model instances of this type."""
        if(query_expr is None):
            query = self.model_type.all()
            if(ordering):
                query.order(ordering)
        else:
            if(ordering):
                order_type = QUERY_ORDER_ASC
                if(ordering[0] == "-"):
                    ordering = ordering[1:]
                    order_type = QUERY_ORDER_DESC
                query_expr += QUERY_ORDERBY + ordering + order_type
            query = self.model_type.gql(query_expr, *query_params)
                
        return query.fetch(limit, offset)
    
    def get_property_handler(self, prop_name):
        """Returns the relevant property handler for the given property name."""
        prop_name = str(prop_name)
        if(prop_name == KEY_PROPERTY_NAME):
            return self.key_handler
        elif(self.property_handlers.has_key(prop_name)):
            return self.property_handlers[prop_name]
        elif(self.is_dynamic()):
            return DynamicPropertyHandler(prop_name)
        else:
            raise KeyError("Unknown property %s" % prop_name)

    def read_dict_value(self, model_dict):
        """Returns a property dictionary for this Model from the given
        model element."""
        props = {}
        for propname, propvalue in model_dict.values()[0].iteritems():
            prop_handler = self.get_property_handler(propname)
            props[str(propname)] = prop_handler.value_from_string(propvalue)
        return props

    def read_xml_value(self, model_el):
        """Returns a property dictionary for this Model from the given model element."""
        props = {}
        for prop_node in model_el.childNodes:
            if(prop_node.nodeType != prop_node.ELEMENT_NODE):
                continue
            self.get_property_handler(prop_node.nodeName).read_xml_value(props, prop_node)

        return props

    def read_xml_property(self, prop_el, props, prop_handler):
        """Reads a property from a property element."""
        prop_handler.read_xml_value(props, prop_el)

    def read_query_values(self, prop_query_name, prop_query_values):
        """Returns a tuple of (query_field, query_values) from the given query property name and value list."""
        prop_handler = self.get_property_handler(prop_query_name)

        if(not prop_handler.can_query()):
            raise KeyError("Can not filter on property %s" % prop_query_name)

        return (prop_handler.get_query_field(), [self.read_query_value(prop_handler, v) for v in prop_query_values])

    def read_query_value(self, prop_handler, prop_query_value):
        """Returns a query value from the given query property handler and value (may be a list)."""
        if isinstance(prop_query_value, (types.ListType, types.TupleType)):
            return [prop_handler.value_for_query(v) for v in prop_query_value]
        else:
            return prop_handler.value_for_query(prop_query_value)        
        
    def write_xml_value(self, model_el, model):
        """Appends the properties of the given instance as xml elements to the given model element."""
        # write key property first
        self.write_xml_property(model_el, model, KEY_PROPERTY_NAME, self.key_handler)

        # write static properties next
        for prop_xml_name, prop_handler in self.property_handlers.iteritems():
            self.write_xml_property(model_el, model, prop_xml_name, prop_handler)
                
        # write dynamic properties last
        for prop_name in model.dynamic_properties():
            prop_xml_name = convert_to_valid_xml_name(prop_name)
            self.write_xml_property(model_el, model, prop_xml_name, DynamicPropertyHandler(prop_name))

    def write_xml_property(self, model_el, model, prop_xml_name, prop_handler):
        """Writes a property as a property element."""
        prop_handler.write_xml_value(model_el, prop_xml_name, model)

    def write_xsd_metadata(self, type_el, model_xml_name):
        """Appends the XML Schema elements of the property types of this model type to the given parent element."""
        top_el = append_child(type_el, XSD_ELEMENT_NAME)
        top_el.attributes[NAME_ATTR_NAME] = model_xml_name
        seq_el = xsd_append_sequence(top_el)

        self.key_handler.write_xsd_metadata(seq_el, KEY_PROPERTY_NAME)
        
        for prop_xml_name, prop_handler in self.property_handlers.iteritems():
            prop_handler.write_xsd_metadata(seq_el, prop_xml_name)

        if(self.is_dynamic()):
            any_el = append_child(seq_el, XSD_ANY_NAME)
            any_el.attributes[XSD_ATTR_NAMESPACE] = XSD_ANY_NAMESPACE
            any_el.attributes[XSD_ATTR_PROCESSCONTENTS] = XSD_LAX_CONTENTS
            any_el.attributes[XSD_ATTR_MINOCCURS] = XSD_NO_MIN
            any_el.attributes[XSD_ATTR_MAXOCCURS] = XSD_NO_MAX

class RESTViewGroup(ViewGroup):
    models = []
    fetch_page_size = 50
    rest_rule_template = RuleTemplate([
        Rule("/$prefix/metadata", endpoint="$prefix/metadata"),
        Rule("/$prefix/metadata/<model_name>", endpoint="$prefix/metadata"),
        Rule("/$prefix/<model_name>", endpoint="$prefix/model"),
        Rule("/$prefix/<model_name>/<key>", endpoint="$prefix/entity"),
        Rule("/$prefix/<model_name>/<key>/<prop>", endpoint="$prefix/prop"),
    ])

    def __init__(self, models=None, prefix="rest", **kwargs):
      super(RESTViewGroup, self).__init__(**kwargs)
      self.prefix = prefix
      self._models = models or self.models
      self.models_dict = {}
      self.model_handlers = {}
      for model in self._models:
          if isinstance(model, basestring):
              model_name = model.split(".")[-1]
          else:
              model_name = model.__name__
          xml_name = convert_to_valid_xml_name(model_name)
          self.models_dict[xml_name] = model
          self.model_handlers[xml_name] = None

    def _import_model_if_not(self, model_name):
        if isinstance(self.models_dict[model_name], basestring):
            self.models_dict[model_name] = import_string(
                self.models_dict[model_name])
        if self.model_handlers[model_name] is None:
            self.model_handlers[model_name] = ModelHandler(
                model_name, self.models_dict[model_name])

    def _get_rules(self):
        return [self.rest_rule_template(prefix=self.prefix)]

    def _get_views(self, prefix=None):
        ret = {}
        for endpoint in ["metadata", "model", "entity", "prop"]:
            actual_endpoint = self.prefix + "/" + endpoint
            if prefix:
                actual_endpoint = prefix+actual_endpoint
            ret[actual_endpoint] = getattr(self, endpoint)
        return ret

    def authorize(self, request, operation, obj=None, model_name=None,
                  prop_name=None):
        """ Raise AuthorizationError when the operation is not
        permitted.
        """
        return True

    def check_authority(self, request, operation, obj=None, model_name=None,
                        prop_name=None):
        try:
            self.authorize(request, operation, obj, model_name, prop_name)
        except NotAuthorized, e:
            raise Forbidden("Access not allowed.")

    def metadata(self, request, model_name=None):
        impl = minidom.getDOMImplementation()
        doc = None
        try:
            if model_name:
                model_handler = self.get_model_handler(model_name)
                if(not model_handler):
                    return None
                self.check_authority(request, OP_LIST, obj=None,
                                     model_name=model_name, prop_name=None)
                doc = impl.createDocument(XSD_NS, XSD_SCHEMA_NAME, None)
                doc.documentElement.attributes[XSD_ATTR_XMLNS] = XSD_NS
                model_handler.write_xsd_metadata(doc.documentElement,
                                                 model_name)
            else:
                self.check_authority(request, OP_LIST, obj=None,
                                     model_name=None, prop_name=None)
                doc = impl.createDocument(None, TYPES_EL_NAME, None)
                types_el = doc.documentElement
                for model_name in self.model_handlers.iterkeys():
                    append_child(types_el, TYPE_EL_NAME, model_name)
            output = self.doc_to_output(request, doc)
        finally:
            if doc:
                doc.unlink()
        return self.out_to_response(output)

    def prop(self, request, model_name=None, key=None, prop=None):
        model_handler = self.get_model_handler(model_name)
        model = model_handler.get(key)
        self.check_authority(request, OP_SHOW, obj=model,
                             model_name=model_name, prop_name=prop)
        prop_handler = model_handler.get_property_handler(prop)
        prop_value = prop_handler.get_value(model)
        content_type = request.accept_mimetypes.best
        if not content_type:
            content_type = TEXT_CONTENT_TYPE
        return Response(str(prop_value), content_type=content_type)

    def entity(self, request, model_name=None, key=None):
        real_method = request.method
        if request.method == "POST":
            real_method = request.headers.get(METHOD_OVERRIDE_HEADER, None)
            if real_method:
                real_method = real_method.upper()
            else:
                real_method = "POST"

        if real_method == "GET":
            model_handler = self.get_model_handler(model_name)
            model = model_handler.get(key)
            self.check_authority(request, OP_SHOW, obj=model,
                                 model_name=model_name, prop_name=None)
            if model is None:
                raise NotFound
            return self.out_to_response(
                self.models_to_xml(request, model_name, model_handler, model,
                                   {}))
        elif real_method == "POST":
            return self.update_impl(request, model_name, key, False)
        elif real_method == "PUT":
            return self.update_impl(request, model_name, key, True)
        elif real_method == "DELETE":
            model_handler = self.get_model_handler(model_name)
            model = model_handler.get(key)
            self.check_authority(request, OP_DELETE, obj=model,
                                 model_name=model_name, prop_name=None)
            try:
                db.delete(db.Key(key))
                return Response("OK")
            except Exception:
                logging.warning("delete failed", exc_info=1)
                return InternalServerError()
      
    def model(self, request, model_name=None):
        real_method = request.method
        if request.method == "POST":
            real_method = request.headers.get(METHOD_OVERRIDE_HEADER, None)
            if real_method:
                real_method = real_method.upper()
            else:
                real_method = "POST"

        if real_method == "POST":
            return self.update_impl(request, model_name, None, False)
        elif real_method == "GET":
            self.check_authority(request, OP_LIST, obj=None,
                                 model_name=model_name, prop_name=None)
            return self.get_all_impl(request, model_name)

    def get_all_impl(self, request, model_name):
        """Actual implementation of REST query.  Gets Model instances
        based on criteria specified in the query parameters.
        """
        model_handler = self.get_model_handler(model_name)

        cur_fetch_page_size = MAX_FETCH_PAGE_SIZE
        fetch_offset = 0
        ordering = None
        query_expr = None
        query_params = []
        list_props = {}
        
        for arg in request.args:
            if(arg == QUERY_OFFSET_PARAM):
                fetch_offset = int(request.args.get(QUERY_OFFSET_PARAM))
                continue
            
            if(arg == QUERY_PAGE_SIZE_PARAM):
                cur_fetch_page_size = int(request.args.get(
                    QUERY_PAGE_SIZE_PARAM))
                continue
            
            if(arg == QUERY_ORDERING_PARAM):
                ordering = request.args.get(QUERY_ORDERING_PARAM)
                continue
            
            match = QUERY_TERM_PATTERN.match(arg)
            if(match is None):
                logging.warning("ignoring unexpected query param %s", arg)
                continue

            query_type = match.group(1)
            query_field = match.group(2)
            query_sub_expr = QUERY_EXPRS[query_type]

            query_values = request.values.getlist(arg)
            if(query_type == QUERY_LIST_TYPE):
                query_values = [v.split(",") for v in query_values]

            query_field, query_values = model_handler.read_query_values(
              query_field, query_values)

            for value in query_values:
                query_params.append(value)
                query_sub_expr = query_sub_expr % (query_field,
                                                   len(query_params))
                if(not query_expr):
                    query_expr = QUERY_PREFIX + query_sub_expr
                else:
                    query_expr += QUERY_JOIN + query_sub_expr

        cur_fetch_page_size = max(min(self.fetch_page_size,
                                      cur_fetch_page_size,
                                      MAX_FETCH_PAGE_SIZE), 1)

        # if possible, attempt to fetch more than we really want so
        # that we can determine if we have more results
        tmp_fetch_page_size = cur_fetch_page_size
        if(tmp_fetch_page_size < MAX_FETCH_PAGE_SIZE):
            tmp_fetch_page_size += 1

        models = model_handler.get_all(tmp_fetch_page_size, fetch_offset,
                                       ordering, query_expr, query_params)

        next_fetch_offset = str(cur_fetch_page_size + fetch_offset)
        if((tmp_fetch_page_size > cur_fetch_page_size) and \
             (len(models) < tmp_fetch_page_size)):
            next_fetch_offset = ""

        list_props[QUERY_OFFSET_PARAM] = next_fetch_offset
        
        # trim list to the actual size we want
        if(len(models) > cur_fetch_page_size):
            models = models[0:cur_fetch_page_size]

        return self.out_to_response(
          self.models_to_xml(request, model_name, model_handler, models,
                             list_props))


    def update_impl(self, request, model_name, model_key, is_replace):
        """Actual implementation of all Model update methods.
        Creates/updates/replaces Model instances as specified.  Writes
        the key of the modified Model as a plain text result.
        """
        
        model_handler = self.get_model_handler(model_name)
        if(not model_handler):
            return

        is_list = False
        if request.content_type.startswith(JSON_CONTENT_TYPE):
            try:
                model_dict = json.load(request.stream)
                model_els = [(model_key, model_dict)]
                if isinstance(model_dict, list):
                    is_list = True
                    model_els = []
                    for item in model_dict:
                        model_els.append((MULTI_UPDATE_KEY, item))
                models = []
                for model_el_key, model_el in model_els:
                    models.append(self.model_from_dict(
                        model_el, model_name, model_handler, model_el_key,
                        is_replace))
            except Exception:
                logging.exception("failed parsing model")
                raise BadRequest()
        else:
            doc = minidom.parse(request.stream)

            model_els = [(model_key, doc.documentElement)]
            if(str(doc.documentElement.nodeName) == LIST_EL_NAME):
                is_list = True
                model_els = []
                for node in doc.documentElement.childNodes:
                    if(node.nodeType == node.ELEMENT_NODE):
                        model_els.append((MULTI_UPDATE_KEY, node))

            models = []
            try:
                for model_el_key, model_el in model_els:
                    models.append(self.model_from_xml(
                        model_el, model_name, model_handler, model_el_key,
                        is_replace))
            except Exception:
                logging.exception("failed parsing model")
                raise BadRequest()
            finally:
                doc.unlink()

        if not model_key:
            self.check_authority(request, OP_CREATE, obj=None,
                                 model_name=model_name, prop_name=None)
        else:
            for model in models:
                self.check_authority(request, OP_UPDATE, obj=model,
                                     model_name=model_name, prop_name=None)
        for model in models:
          def txn():
            db.put(model)
          db.run_in_transaction(txn)

        # if input was not a list, convert single element models list
        # back to single element
        if(not is_list):
            models = models[0]

        # note, we specifically look in the query string (don't try to
        # parse the POST body)
        output_type = request.args.get("type", None)
        if output_type == "full":
            return self.out_to_response(
              self.models_to_xml(request, model_name, model_handler, models))
        elif output_type == "xml":
            return self.out_to_response(
              self.keys_to_xml(request, model_handler, models))
        else:
            return self.out_to_response(self.keys_to_text(models))

    def get_model_handler(self, model_name):
        try:
            self._import_model_if_not(model_name)
            return self.model_handlers[model_name]
        except Exception:
            raise NotFound()

    def doc_to_output(self, request, doc):
        out_mime_type = request.accept_mimetypes.best_match(
          [JSON_CONTENT_TYPE, XML_CONTENT_TYPE])
        if out_mime_type == JSON_CONTENT_TYPE:
          return xml_to_json(doc)
        else:
          return doc.toxml(XML_ENCODING)

    def out_to_response(self, output):
         first_char = output[0]
         content_type = TEXT_CONTENT_TYPE
         if(first_char == '{'):
             content_type = JSON_CONTENT_TYPE
         elif(first_char == "<"):
             content_type = XML_CONTENT_TYPE
         return Response(output, content_type=content_type)

    def models_to_xml(self, request, model_name, model_handler, models,
                      list_props=None):
        """Returns a string of xml of the given models (may be list or
        single instance)."""
        impl = minidom.getDOMImplementation()
        doc = None
        try:
            if isinstance(models, (types.ListType, types.TupleType)):
                doc = impl.createDocument(None, LIST_EL_NAME, None)
                list_el = doc.documentElement
                if ((list_props is not None) and \
                      (list_props.has_key(QUERY_OFFSET_PARAM))):
                    list_el.attributes[QUERY_OFFSET_PARAM] = \
                        list_props[QUERY_OFFSET_PARAM]
                for model in models:
                    model_el = append_child(list_el, model_name)
                    model_handler.write_xml_value(model_el, model)
            else:
                doc = impl.createDocument(None, model_name, None)
                model_handler.write_xml_value(doc.documentElement, models)

            return self.doc_to_output(request, doc)
        finally:
            if doc:
                doc.unlink()

    def keys_to_xml(self, request, model_handler, models):
        """Returns a string of xml of the keys of the given models
        (may be list or single instance)."""
        impl = minidom.getDOMImplementation()
        doc = None
        try:
            if isinstance(models, (types.ListType, types.TupleType)):
                doc = impl.createDocument(None, LIST_EL_NAME, None)
                list_el = doc.documentElement
                    
                for model in models:
                    append_child(
                        list_el, KEY_PROPERTY_NAME,
                        model_handler.key_handler.get_value_as_string(model))
            else:
                doc = impl.createDocument(None, KEY_PROPERTY_NAME, None)
                doc.documentElement.appendChild(
                    doc.createTextNode(
                        model_handler.key_handler.get_value_as_string(models)))
            return self.doc_to_output(request, doc)
        finally:
            if doc:
                doc.unlink()

    def keys_to_text(self, models):
        """Returns a string of text of the keys of the given models
        (may be list or single instance)."""
        if(not isinstance(models, (types.ListType, types.TupleType))):
            models = [models]
        return unicode(",".join([str(model.key()) for model in models]))

    def model_from_dict(self, json, model_name, model_handler, key,
                        is_replace):
        """Returns a model instance updated from the given model json
        element."""
        if not json.has_key(model_name):
            raise TypeError("wrong model name, found '%s', expected '%s'" %
                            (json.keys()[0], model_name))
        props = model_handler.read_dict_value(json)
        given_key = props.pop(KEY_PROPERTY_NAME, None)

        if(key is MULTI_UPDATE_KEY):
            if(given_key):
                key = str(given_key)
            else:
                key = None

        if(key):
            key = db.Key(key.strip())
            if(given_key and (given_key != key)):
                raise ValueError("key in data %s does not match request key %s"
                                 % (given_key, key))
            model = model_handler.get(key)

            if(is_replace):
                for prop_name, prop_type in model.properties().iteritems():
                    setattr(model, prop_name, prop_type.default_value())
                for prop_name in model.dynamic_properties():
                    delattr(model, prop_name)

            for prop_name, prop_value in props.iteritems():
                setattr(model, prop_name, prop_value)
                
        else:
            model = model_handler.create(props)

        return model
        
    def model_from_xml(self, model_el, model_name, model_handler, key,
                       is_replace):
        """Returns a model instance updated from the given model xml
        element."""
        if(model_name != str(model_el.nodeName)):
            raise TypeError("wrong model name, found '%s', expected '%s'" %
                            (model_el.nodeName, model_name))
        props = model_handler.read_xml_value(model_el)

        given_key = props.pop(KEY_PROPERTY_NAME, None)

        if(key is MULTI_UPDATE_KEY):
            if(given_key):
                key = str(given_key)
            else:
                key = None
        
        if(key):
            key = db.Key(key.strip())
            if(given_key and (given_key != key)):
                raise ValueError("key in data %s does not match request key %s"
                                 % (given_key, key))
            model = model_handler.get(key)

            if(is_replace):
                for prop_name, prop_type in model.properties().iteritems():
                    setattr(model, prop_name, prop_type.default_value())
                for prop_name in model.dynamic_properties():
                    delattr(model, prop_name)

            for prop_name, prop_value in props.iteritems():
                setattr(model, prop_name, prop_value)
                
        else:
            model = model_handler.create(props)

        return model
