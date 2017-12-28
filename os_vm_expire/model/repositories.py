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
Defines interface for DB access that Resource controllers may reference
TODO: The top part of this file was 'borrowed' from Glance, but seems
quite intense for sqlalchemy, and maybe could be simplified.
"""

import datetime
import logging
import re
import threading
import time

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session
from oslo_utils import timeutils
# from oslo_utils import uuidutils
import sqlalchemy
# from sqlalchemy import func as sa_func
# from sqlalchemy import or_
import sqlalchemy.orm as sa_orm

from os_vm_expire.common import config
from os_vm_expire.common import utils
from os_vm_expire import i18n as u
from os_vm_expire.model.migration import commands
from os_vm_expire.model import models

LOG = utils.getLogger(__name__)

_ENGINE = None
_SESSION_FACTORY = None
BASE = models.BASE
sa_logger = None

# Singleton repository references, instantiated via get_xxxx_repository()
#   functions below.  Please keep this list in alphabetical order.
_VMEXPIRE_REPOSITORY = None

CONF = config.CONF

_FACADE = None
_LOCK = threading.Lock()


def _create_facade_lazily():
    global _LOCK, _FACADE

    if _FACADE is None:
        with _LOCK:
            if _FACADE is None:
                _FACADE = session.EngineFacade.from_config(CONF,
                                                           sqlite_fk=True)
    return _FACADE


def hard_reset():
    """Performs a hard reset of database resources, used for unit testing."""
    # TODO(jvrbanac): Remove this as soon as we improve our unit testing
    # to not require this.
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None

    # Make sure we reinitialize the engine and session factory
    setup_database_engine_and_factory()


def setup_database_engine_and_factory():
    global sa_logger, _SESSION_FACTORY, _ENGINE

    LOG.info('Setting up database engine and session factory')
    if CONF.debug:
        sa_logger = logging.getLogger('sqlalchemy.engine')
        sa_logger.setLevel(logging.DEBUG)

    _ENGINE = _get_engine(_ENGINE)

    # Utilize SQLAlchemy's scoped_session to ensure that we only have one
    # session instance per thread.
    session_maker = sa_orm.sessionmaker(bind=_ENGINE)
    _SESSION_FACTORY = sqlalchemy.orm.scoped_session(session_maker)


def start():
    """Start for read-write requests placeholder

    Typically performed at the start of a request cycle, say for POST or PUT
    requests.
    """
    pass


def start_read_only():
    """Start for read-only requests placeholder

    Typically performed at the start of a request cycle, say for GET or HEAD
    requests.
    """
    pass


def commit():
    """Commit session state so far to the database.

    Typically performed at the end of a request cycle.
    """
    get_session().commit()


def rollback():
    """Rollback session state so far.

    Typically performed when the request cycle raises an Exception.
    """
    get_session().rollback()


def clear():
    """Dispose of this session, releases db resources.

    Typically performed at the end of a request cycle, after a
    commit() or rollback().
    """
    if _SESSION_FACTORY:  # not initialized in some unit test
        _SESSION_FACTORY.remove()


def get_session():
    """Helper method to grab session."""
    return _SESSION_FACTORY()


def _get_engine(engine):
    if not engine:
        db_connection = None
        try:
            engine = _create_engine()
            db_connection = engine.connect()
        except Exception as err:
            msg = u._("Error configuring registry database with supplied "
                      "connection. Got error: {error}").format(error=err)
            LOG.exception(msg)
            raise Exception(msg)
        finally:
            if db_connection:
                db_connection.close()

    return engine


def is_db_connection_error(args):
    """Return True if error in connecting to db."""
    # NOTE(adam_g): This is currently MySQL specific and needs to be extended
    #               to support Postgres and others.
    conn_err_codes = ('2002', '2003', '2006')
    for err_code in conn_err_codes:
        if args.find(err_code) != -1:
            return True
    return False


def _create_engine():
    LOG.debug('Sql connection')

    # engine = session.create_engine(connection, **engine_args)
    engine = _create_facade_lazily().get_engine()

    # Wrap the engine's connect method with a retry decorator.
    engine.connect = wrap_db_error(engine.connect)

    return engine


def _auto_generate_tables(engine, tables):
    if tables and 'alembic_version' in tables:
        # Upgrade the database to the latest version.
        LOG.info('Updating schema to latest version')
        commands.upgrade()
    else:
        # Create database tables from our models.
        LOG.info('Auto-creating osvmexpire registry DB')
        models.BASE.metadata.create_all(engine)

        # Sync the alembic version 'head' with current models.
        commands.stamp()


def wrap_db_error(f):
    """Retry DB connection. Copied from nova and modified."""
    def _wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except sqlalchemy.exc.OperationalError as e:
            if not is_db_connection_error(e.args[0]):
                raise

            remaining_attempts = CONF.sql_max_retries
            while True:
                LOG.warning('SQL connection failed. %d attempts left.',
                            remaining_attempts)
                remaining_attempts -= 1
                time.sleep(CONF.sql_retry_interval)
                try:
                    return f(*args, **kwargs)
                except sqlalchemy.exc.OperationalError as e:
                    if (remaining_attempts <= 0 or not
                            is_db_connection_error(e.args[0])):
                        raise
                except sqlalchemy.exc.DBAPIError:
                    raise
        except sqlalchemy.exc.DBAPIError:
            raise
    _wrap.__name__ = f.__name__
    return _wrap


def delete_all_project_resources(project_id):
    """Logic to cleanup all project resources.

    This cleanup uses same alchemy session to perform all db operations as a
    transaction and will commit only when all db operations are performed
    without error.
    """
    session = get_session()

    container_repo = get_vmexpire_repository()
    container_repo.delete_project_entities(
        project_id, suppress_exception=False, session=session)


class BaseRepo(object):
    """Base repository for the osvmexpire entities.

    This class provides template methods that allow sub-classes to hook
    specific functionality as needed. Clients access instances of this class
    via singletons, therefore implementations should be stateless aside from
    configuration.
    """

    def get_session(self, session=None):
        LOG.debug("Getting session...")
        return session or get_session()

    def get_all_by(self, instance_id=None, project_id=None, session=None):
        session = self.get_session(session)
        query = session.query(models.VmExpire)
        if instance_id:
            query = query.filter_by(instance_id=instance_id)
        if project_id:
            query = query.filter_by(project_id=project_id)

        return query.all()

    def get_by_instance(self, instance_id, session=None):
        session = self.get_session(session)

        try:
            query = session.query(
                models.VmExpire
                ).filter_by(instance_id=instance_id)
            entity = query.one()

        except sa_orm.exc.NoResultFound:
            LOG.debug("Not found for %s", instance_id)
            entity = None
            _raise_entity_not_found(self._do_entity_name(), instance_id)

        return entity

    def get(self, entity_id,
            force_show_deleted=False,
            suppress_exception=False, session=None):
        """Get an entity or raise if it does not exist."""
        session = self.get_session(session)

        try:
            query = self._do_build_get_query(entity_id,
                                             session)

            entity = query.one()

        except sa_orm.exc.NoResultFound:
            LOG.debug("Not found for %s", entity_id)
            entity = None
            _raise_entity_not_found(self._do_entity_name(), entity_id)

        return entity

    def extend_vm(self, entity_id, session=None):
        session = self.get_session(session)
        try:
            query = self._do_build_get_query(entity_id,
                                             session)

            entity = query.one()

            entity.expire = int(
                time.mktime(datetime.datetime.now().timetuple()) +
                CONF.max_vm_extend * 3600 * 24
                )

            if entity.created_at + datetime.timedelta(days=CONF.max_vm_total_duration) < datetime.datetime.fromtimestamp(entity.expire):
                _raise_entity_max_extend_reached(entity.id)
                return None
            entity.notified = False
            entity.notified_last = False
            entity.save(session=session)
        except sa_orm.exc.NoResultFound:
            LOG.debug("Not found for %s", entity_id)
            entity = None
            _raise_entity_not_found(self._do_entity_name(), entity_id)
        return entity

    def create_from(self, entity, session=None):
        """Sub-class hook: create from entity."""
        if not entity:
            msg = u._(
                "Must supply non-None {entity_name}."
            ).format(entity_name=self._do_entity_name())
            raise Exception(msg)

        if entity.id:
            msg = u._(
                "Must supply {entity_name} with id=None (i.e. new entity)."
            ).format(entity_name=self._do_entity_name())
            raise Exception(msg)

        LOG.debug("Begin create from...")
        session = self.get_session(session)
        start = time.time()  # DEBUG

        # Validate the attributes before we go any further. From my
        # (unknown Glance developer) investigation, the @validates
        # decorator does not validate
        # on new records, only on existing records, which is, well,
        # idiotic.
        self._do_validate(entity.to_dict())

        try:
            LOG.debug("Saving entity...")
            entity.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            session.rollback()
            LOG.exception('Problem saving entity for create')
            error_msg = re.sub('[()]', '', str(e.args))
            raise Exception(error_msg)

        LOG.debug('Elapsed repo '
                  'create vmexpire:%s', (time.time() - start))  # DEBUG

        return entity

    def save(self, entity, session=None):
        """Saves the state of the entity."""
        entity.updated_at = timeutils.utcnow()

        # Validate the attributes before we go any further. From my
        # (unknown Glance developer) investigation, the @validates
        # decorator does not validate
        # on new records, only on existing records, which is, well,
        # idiotic.
        self._do_validate(entity.to_dict())

        entity.save(session=session)

    def delete_entity_by_id(self, entity_id,
                            session=None):
        """Remove the entity by its ID."""

        session = self.get_session(session)

        entity = self.get(entity_id=entity_id,
                          session=session)

        entity.delete(session=session)

    def _do_entity_name(self):
        """Sub-class hook: return entity name, such as for debugging."""
        return "Entity"

    def _do_build_get_query(self, entity_id, external_project_id, session):
        """Sub-class hook: build a retrieve query."""
        return None

    def _do_convert_values(self, values):
        """Sub-class hook: convert text-based values to target types

        This is specifically for database values.
        """
        pass

    def _do_validate(self, values):
        """Sub-class hook: validate values.

        Validates the incoming data and raises an Invalid exception
        if anything is out of order.
        :param values: Mapping of entity metadata to check
        """
        return values

    def _update_values(self, entity_ref, values):
        for k in values:
            if getattr(entity_ref, k) != values[k]:
                setattr(entity_ref, k, values[k])

    def _build_get_project_entities_query(self, project_id, session):
        """Sub-class hook: build a query to retrieve entities for a project.

        :param project_id: id of osvmexpire project entity
        :param session: existing db session reference.
        :returns: A query object for getting all project related entities
        This will filter deleted entities if there.
        """
        msg = u._(
            "{entity_name} is missing query build method for get "
            "project entities.").format(
                entity_name=self._do_entity_name())
        raise NotImplementedError(msg)

    def get_project_entities(self, project_id, session=None):
        """Gets entities associated with a given project.

        :param project_id: id of osvmexpire project entity
        :param session: existing db session reference. If None, gets session.
        :returns: list of matching entities found otherwise returns empty list
                  if no entity exists for a given project.
        Sub-class should implement `_build_get_project_entities_query` function
        to delete related entities otherwise it would raise NotImplementedError
        on its usage.
        """

        session = self.get_session(session)
        query = self._build_get_project_entities_query(project_id, session)
        if query:
            return query.all()
        else:
            return []

    def get_entities(self, expiration_filter=None, session=None):
        """Get all entities

        :param session: existing db session reference. If None, gets session.
        :param expiration_filter: timestamp to compare expiration date with
        :returns: list of matching entities found otherwise returns empty list
                  if no entity exists for a given project.
        """

        session = self.get_session(session)
        query = session.query(models.VmExpire)
        if expiration_filter:
            query = query.filter(models.VmExpire.expire < expiration_filter)
        LOG.debug(query)
        if query:
            return query.all()
        else:
            return []

    def get_count(self, project_id, session=None):
        """Gets count of entities associated with a given project

        :param project_id: id of osvmexpire project entity
        :param session: existing db session reference. If None, gets session.
        :return: an number 0 or greater
        Sub-class should implement `_build_get_project_entities_query` function
        to delete related entities otherwise it would raise NotImplementedError
        on its usage.
        """
        session = self.get_session(session)
        query = self._build_get_project_entities_query(project_id, session)
        if query:
            return query.count()
        else:
            return 0

    def delete_project_entities(self, project_id,
                                suppress_exception=False,
                                session=None):
        """Deletes entities for a given project.

        :param project_id: id of osvmexpire project entity
        :param suppress_exception: Pass True if want to suppress exception
        :param session: existing db session reference. If None, gets session.
        Sub-class should implement `_build_get_project_entities_query` function
        to delete related entities otherwise it would raise NotImplementedError
        on its usage.
        """
        session = self.get_session(session)
        query = self._build_get_project_entities_query(project_id,
                                                       session=session)
        try:
            # query cannot be None as related repo class is expected to
            # implement it otherwise error is raised in build query call
            for entity in query:
                # Its a soft delete so its more like entity update
                entity.delete(session=session)
        except sqlalchemy.exc.SQLAlchemyError:
            LOG.exception('Problem finding project related entity to delete')
            if not suppress_exception:
                raise Exception(u._('Error deleting project '
                                    'entities for '
                                    'project_id=%s'),
                                project_id)


class VmExpireRepo(BaseRepo):
    """Repository for the expire entity."""

    def _do_entity_name(self):
        """Sub-class hook: return entity name, such as for debugging."""
        return "VMExpire"

    def _do_build_get_query(self, entity_id, session):
        """Sub-class hook: build a retrieve query."""
        query = session.query(models.VmExpire)
        query = query.filter_by(id=entity_id)
        return query

    def _do_validate(self, values):
        """Sub-class hook: validate values."""
        pass

    def _build_get_project_entities_query(self, project_id, session):
        """Builds query for retrieving orders related to given project.

        :param project_id: id of osvmexpire project entity
        :param session: existing db session reference.
        """
        return session.query(models.VmExpire).filter_by(
            project_id=project_id)

    def delete_all_entities(self, suppress_exception=False, session=None):
        """Deletes all entities.

        :param suppress_exception: Pass True if want to suppress exception
        :param session: existing db session reference. If None, gets session.
        """
        session = self.get_session(session)
        try:
            session.query(models.VmExpire).delete()
        except sqlalchemy.exc.SQLAlchemyError:
            LOG.exception('Problem deleting entities')
            if not suppress_exception:
                raise Exception(u._('Error deleting entities '))


class VmExcludeRepo(BaseRepo):
    """Repository for the exclude entity."""

    def _do_entity_name(self):
        """Sub-class hook: return entity name, such as for debugging."""
        return "VMExclude"

    def _do_build_get_query(self, entity_id, session):
        """Sub-class hook: build a retrieve query."""
        query = session.query(models.VmExclude)
        query = query.filter_by(id=entity_id)
        return query

    def _do_validate(self, values):
        """Sub-class hook: validate values."""
        pass

    def get_exclude_by_id(self, exclude_id, session=None):
        """Builds query for retrieving exclude related to given entity id.

        :param entity_id: id of entity (user, project, domain)
        :param session: existing db session reference.
        """
        session = self.get_session(session)
        return session.query(models.VmExclude).filter_by(
            exclude_id=exclude_id).one_or_none()

    def get_type_entities(self, exclude_type=None, session=None):
        """Builds query for retrieving excludes related to given type.

        :param exclude_type: id of osvmexclude type entity
        :param session: existing db session reference.
        """
        session = self.get_session(session)
        if exclude_type is None:
            return session.query(models.VmExclude).all()
        else:
            return session.query(models.VmExclude).filter_by(
                exclude_type=exclude_type).all()

    def get_exclude_type(self, exclude_name):
        """Get numeric value matching the exclude type (domain,project,user).

        :param exclude_name: domain or project or user
        :return: matching numeric value for database
        """
        if exclude_name == 'domain':
            return 0
        elif exclude_name == 'project':
            return 1
        elif exclude_name == 'user':
            return 2
        else:
            return -1

    def create_exclude_entity(self, entity_id, entity_type):
        """Get a VmExclude model

        :param entity_id: domain/project/user id
        :param entity_type: numeric value of type, see get_exclude_type()
        :return: `os_vm_expire.model.models.VmExclude`
        """
        entity = models.VmExclude()
        entity.exclude_id = entity_id
        entity.exclude_type = entity_type
        return entity

    def create_exclude(self, entity, session=None):
        """Record a new Exclude model in database.

        Checks that entity id does not already exists
        :return: `os_vm_expire.model.models.VmExclude`
        """

        ent_in_db = self.get_exclude_by_id(entity.exclude_id, session)
        if ent_in_db:
            raise Exception(u._('Error creating exclude entity '
                                'entity for '
                                'entity_id=%(id)s,'
                                'entity_type=%(type)d'
                                ' already exists') %
                            {'id': entity.exclude_id, 'type': entity.exclude_type})
        else:
            self.create_from(entity, session)
            return entity

    def delete_all_entities(self, suppress_exception=False, session=None):
        """Deletes all entities.

        :param suppress_exception: Pass True if want to suppress exception
        :param session: existing db session reference. If None, gets session.
        """
        session = self.get_session(session)
        try:
            session.query(models.VmExclude).delete()
        except sqlalchemy.exc.SQLAlchemyError:
            LOG.exception('Problem deleting entities')
            if not suppress_exception:
                raise Exception(u._('Error deleting entities '))


def get_vmexpire_repository():
    """Returns a singleton repository instance."""
    global _VMEXPIRE_REPOSITORY
    return _get_repository(_VMEXPIRE_REPOSITORY, VmExpireRepo)


def get_vmexclude_repository():
    """Returns a singleton repository instance."""
    global _VMEXPIRE_REPOSITORY
    return _get_repository(_VMEXPIRE_REPOSITORY, VmExcludeRepo)


def _get_repository(global_ref, repo_class):
    if not global_ref:
        global_ref = repo_class()
    return global_ref


def _raise_entity_max_extend_reached(entity_id):
    raise Exception(u._("VM reached its maximum life, {id}, cannot extend it").format(
        id=entity_id))


def _raise_entity_not_found(entity_name, entity_id):
    raise Exception(u._("No {entity} found with ID {id}").format(
        entity=entity_name,
        id=entity_id))


def _raise_entity_id_not_found(entity_id):
    raise Exception(u._("Entity ID {entity_id} not "
                        "found").format(entity_id=entity_id))


def _raise_no_entities_found(entity_name):
    raise Exception(
        u._("No entities of type {entity_name} found").format(
            entity_name=entity_name))
