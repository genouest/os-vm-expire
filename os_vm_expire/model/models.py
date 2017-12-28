# Copyright (c) 2013-2014 Rackspace, Inc.
#               2017 IRISA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Defines database models for osvmexpire
"""
from oslo_serialization import jsonutils as json
from oslo_utils import timeutils
import six
import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.ext import declarative
from sqlalchemy import orm
# from sqlalchemy.orm import collections as col
from sqlalchemy import types as sql_types

from os_vm_expire.common import utils
# from os_vm_expire import i18n as u

BASE = declarative.declarative_base()
ERROR_REASON_LENGTH = 255
SUB_STATUS_LENGTH = 36
SUB_STATUS_MESSAGE_LENGTH = 255


@compiler.compiles(sa.BigInteger, 'sqlite')
def compile_big_int_sqlite(type_, compiler, **kw):
    return 'INTEGER'


class JsonBlob(sql_types.TypeDecorator):
    """JsonBlob is custom type for fields which need to store JSON text."""
    impl = sa.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class ModelBase(object):
    """Base class for Nova and osvmexpire Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    __protected_attributes__ = {
        "created_at", "updated_at", "deleted_at", "deleted"}

    id = sa.Column(sa.String(36), primary_key=True,
                   default=utils.generate_uuid)

    created_at = sa.Column(sa.DateTime, default=timeutils.utcnow,
                           nullable=False)
    updated_at = sa.Column(sa.DateTime, default=timeutils.utcnow,
                           nullable=False, onupdate=timeutils.utcnow)
    deleted_at = sa.Column(sa.DateTime)
    deleted = sa.Column(sa.Boolean, nullable=False, default=False)

    def save(self, session=None):
        """Save this object."""
        # import api here to prevent circular dependency problem
        import os_vm_expire.model.repositories
        session = session or os_vm_expire.model.repositories.get_session()
        # if model is being created ensure that created/updated are the same
        if self.id is None:
            self.created_at = timeutils.utcnow()
            self.updated_at = self.created_at
        session.add(self)
        session.flush()

    def delete(self, session=None):
        """Delete this object."""
        import os_vm_expire.model.repositories
        session = session or os_vm_expire.model.repositories.get_session()
        self._do_delete_children(session)
        session.delete(self)

    def _do_delete_children(self, session):
        """Sub-class hook: delete children relationships."""
        pass

    def update(self, values):
        """dict.update() behaviour."""
        for k, v in values.items():
            self[k] = v

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(orm.object_mapper(self).sa.Columns)
        return self

    def next(self):
        n = next(self._i).name
        return n, getattr(self, n)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        return self.__dict__.copy()

    def to_dict_fields(self):
        """Returns a dictionary of just the db fields of this entity."""

        if self.created_at:
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        if self.updated_at:
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        dict_fields = {
            'created': created_at,
            'updated': updated_at,
        }

        if self.deleted_at:
            dict_fields['deleted_at'] = self.deleted_at.isoformat()
        if self.deleted:
            dict_fields['deleted'] = True
        dict_fields.update(self._do_extra_dict_fields())
        return dict_fields

    def _do_extra_dict_fields(self):
        """Sub-class hook method: return dict of fields."""
        return {}

    def _iso_to_datetime(self, expiration):
        """Convert ISO formatted string to datetime."""
        if isinstance(expiration, six.string_types):
            expiration_iso = timeutils.parse_isotime(expiration.strip())
            expiration = timeutils.normalize_time(expiration_iso)

        return expiration


class SoftDeleteMixIn(object):
    """Mix-in class that adds soft delete functionality."""

    def delete(self, session=None):
        """Delete this object."""
        import os_vm_expire.model.repositories
        session = session or os_vm_expire.model.repositories.get_session()
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)

        self._do_delete_children(session)


class VmExpire(BASE, ModelBase):
    """Represents a VM."""

    __tablename__ = 'vmexpire'

    instance_id = sa.Column(
        sa.String(255), index=True,
        nullable=False)
    project_id = sa.Column(
        sa.String(255), index=True,
        nullable=False)
    user_id = sa.Column(
        sa.String(255), index=False,
        nullable=False)
    expire = sa.Column(
        sa.Integer, index=False,
        nullable=False)
    notified = sa.Column(
        sa.Boolean, index=False,
        nullable=False)
    notified_last = sa.Column(
        sa.Boolean, index=False,
        nullable=False)
    instance_name = sa.Column(
        sa.String(255), index=False,
        nullable=True)

    __table_args__ = (sa.UniqueConstraint('instance_id',
                                          name='_vmexpire_uc'),)

    def __init__(self, parsed_request=None):
        """Creates secret from a dict."""
        super(VmExpire, self).__init__()

    def _do_extra_dict_fields(self):
        """Sub-class hook method: return dict of fields."""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'project_id': self.project_id,
            'expire': self.expire,
            'notified': self.notified,
            'notified_last': self.notified_last,
            'user_id': self.user_id,
            'instance_name': self.instance_name
        }


class VmExclude(BASE, ModelBase):
    """Represents a VM."""

    __tablename__ = 'vmexclude'

    exclude_id = sa.Column(
        sa.String(255), index=False,
        nullable=False)
    exclude_type = sa.Column(
        sa.Integer, index=False,
        nullable=False)

    def __init__(self, parsed_request=None):
        """Creates secret from a dict."""
        super(VmExclude, self).__init__()

    def _do_extra_dict_fields(self):
        """Sub-class hook method: return dict of fields."""
        return {
            'id': self.id,
            'exclude_id': self.exclude_id,
            'exclude_type': self.exclude_type
        }
